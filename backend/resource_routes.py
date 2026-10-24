"""HTTP resource identifiers, content negotiation and fixed representations."""

import hashlib
import json
import os
import re
from urllib.parse import quote, urlencode, urlsplit

from flask import Blueprint, Response, current_app, redirect, request
import passivlingo_dictionary as pld
import wn
from werkzeug.routing import BaseConverter

from wordnet_export import export_document, export_graph
from wordnet_service import DEFAULT_LANGUAGES, RELATIONS, WordnetService


resources = Blueprint('resources', __name__)
FORMATS = {'view': 'text/html', 'api': 'application/json',
           'ttl': 'text/turtle', 'rdf': 'application/rdf+xml'}
KINDS = ('lemma', 'synset', 'ili', 'id')


class LanguageConverter(BaseConverter):
    regex = r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*'


def init_resources(app):
    app.url_map.converters['language'] = LanguageConverter
    app.config.setdefault('WORDNET_LANGUAGES', os.environ.get('WORDNET_LANGUAGES', ','.join(DEFAULT_LANGUAGES)))
    languages = app.config['WORDNET_LANGUAGES']
    if isinstance(languages, str):
        languages = languages.replace(',', ' ').split()
    if not languages or any(not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*', lang) for lang in languages):
        raise ValueError('WORDNET_LANGUAGES must list the configured language codes')
    app.config['WORDNET_LANGUAGES'] = list(dict.fromkeys(languages))
    app.config.setdefault('WORDNET_URL_PREFIX', os.environ.get('WORDNET_URL_PREFIX', ''))
    prefix = app.config['WORDNET_URL_PREFIX'].rstrip('/')
    if prefix and not re.fullmatch(r'(?:/[A-Za-z0-9_-]+)+', prefix):
        raise ValueError('WORDNET_URL_PREFIX must be an absolute URL path, such as /wordnet')
    app.config['WORDNET_URL_PREFIX'] = prefix
    app.config.setdefault('WORDNET_PUBLIC_URL', os.environ.get('WORDNET_PUBLIC_URL', '').rstrip('/'))
    if app.config['WORDNET_PUBLIC_URL']:
        base = urlsplit(app.config['WORDNET_PUBLIC_URL'])
        if (base.scheme not in ('http', 'https') or not base.netloc or base.username
                or base.query or base.fragment or base.path.rstrip('/') != prefix):
            raise ValueError('WORDNET_PUBLIC_URL must be an HTTP(S) base URL matching WORDNET_URL_PREFIX')
        app.config['WORDNET_PUBLIC_URL'] = app.config['WORDNET_PUBLIC_URL'].rstrip('/')
    app.register_blueprint(resources)


def _path(format, kind, value, lang=None):
    parts = [format, *([lang] if lang else []), 'synset' if kind == 'id' else kind, value]
    return current_app.config['WORDNET_URL_PREFIX'] + '/' + '/'.join(quote(part, safe='') for part in parts)


def _target(format, kind, value, lang):
    query = urlencode(list(request.args.items(multi=True)))
    return _path(format, kind, value, lang) + ('?' + query if query else '')


def _error(message, status):
    response = Response(json.dumps({'error': message}), status=status, mimetype='application/json')
    response.headers['Cache-Control'] = 'no-store'
    response.vary.add('Accept')
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def _languages(lang):
    allowed = current_app.config['WORDNET_LANGUAGES']
    if lang and 'langs' in request.args:
        raise ValueError('Use either a language prefix or the langs query parameter')
    for key in request.args:
        if key not in ('langs', 'relation', 'word') or len(request.args.getlist(key)) != 1:
            raise ValueError(f'Unsupported or repeated query parameter: {key}')
    selected = [lang] if lang else request.args.get('langs', ','.join(allowed)).split(',')
    if not selected or any(code not in allowed for code in selected):
        raise ValueError(f'Unsupported language; configured languages: {", ".join(allowed)}')
    if request.args.get('relation') and request.args['relation'] not in RELATIONS:
        raise ValueError('Unknown semantic relation')
    return [code for code in allowed if code in selected]


def negotiated(kind, value, lang=None):
    accept = request.accept_mimetypes
    media = accept.best_match(list(FORMATS.values())) if 'Accept' in request.headers else 'text/html'
    if media is None:
        return _error('Supported representations: ' + ', '.join(FORMATS.values()), 406)
    format = next(name for name, mime in FORMATS.items() if mime == media)
    # HTML goes to the view even for unknown terms/languages, so the existing
    # UI can explain invalid searches. Data endpoints validate before lookup.
    response = redirect(_target(format, kind, value, lang), code=303)
    response.vary.add('Accept')
    response.headers['Cache-Control'] = 'public, max-age=300'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def representation(format, kind, value, lang=None):
    media = FORMATS[format]
    if 'Accept' in request.headers and request.accept_mimetypes[media] <= 0:
        return _error(f'This representation is {media}', 406)
    try:
        languages = _languages(lang)
        kind = 'synset' if kind == 'id' else kind
        value = value.strip()
        service = WordnetService(languages)
        synsets = service.lookup_synsets(kind, value, lang, request.args.get('relation'))
        if not synsets:
            return _error('No matching concepts in the selected languages', 404)
        base = current_app.config['WORDNET_PUBLIC_URL'] or (
            request.host_url.rstrip('/') + current_app.config['WORDNET_URL_PREFIX'])
        document = export_document(synsets, base=base, kind=kind, value=value,
                                   languages=languages, relation=request.args.get('relation'))
        canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        # RDF serializations can reorder triples without changing meaning.
        # A weak validator over the common document remains stable for both.
        etag = hashlib.sha256(format.encode() + b'\0' + canonical).hexdigest()
        body = canonical if format == 'api' else export_graph(document).serialize(
            format='turtle' if format == 'ttl' else 'xml', encoding='utf-8')
        response = Response(body, content_type=media + '; charset=utf-8')
        response.set_etag(etag, weak=True)
        response.headers['Cache-Control'] = 'public, max-age=0, must-revalidate'
        response.headers['Content-Location'] = _target(format, kind, value, lang)
        response.headers['Link'] = ', '.join(
            f'<{_target(name, kind, value, lang)}>; rel="alternate"; type="{mime}"'
            for name, mime in FORMATS.items() if name != format)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.vary.add('Accept')
        return response.make_conditional(request)
    except (ValueError, pld.LanguageError) as error:
        return _error(str(error), 400)
    except (wn.Error, pld.BackendError) as error:
        if 'no such synset' in str(error).lower():
            return _error('Synset not found in the installed lexicons', 404)
        current_app.logger.exception('WordNet export failed')
        return _error('WordNet data is temporarily unavailable', 503)


# Explicit rules avoid a catch-all that could capture Angular's /view routes
# or the existing /api/dict endpoints. Flask also provides HEAD and OPTIONS.
for kind in KINDS:
    for with_language in (False, True):
        language = '<language:lang>/' if with_language else ''
        suffix = f'{kind}_{with_language}'
        resources.add_url_rule(f'/{language}{kind}/<path:value>', f'resource_{suffix}',
                               negotiated, defaults={'kind': kind})
        for format in ('api', 'ttl', 'rdf'):
            resources.add_url_rule(f'/{format}/{language}{kind}/<path:value>', f'{format}_{suffix}',
                                   representation, defaults={'format': format, 'kind': kind})
