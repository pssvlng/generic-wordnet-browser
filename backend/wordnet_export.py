"""A lookup document and its equivalent OntoLex/WordNet RDF graph."""

import hashlib
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

from wordnet_service import WordnetService


ONTOLEX = Namespace('http://www.w3.org/ns/lemon/ontolex#')
VARTRANS = Namespace('http://www.w3.org/ns/lemon/vartrans#')
SYNSEM = Namespace('http://www.w3.org/ns/lemon/synsem#')
WN = Namespace('https://globalwordnet.github.io/schemas/wn#')
ILI = Namespace('http://ili.globalwordnet.org/ili/')
RDF_PROFILE_VERSION = '2'
POS = dict(n='noun', v='verb', a='adjective', s='adjective_satellite',
           r='adverb', t='named_entity', c='conjunction', p='adposition',
           x='other_pos', u='unknown_pos')


def resource_uri(base, language, kind, value):
    return f'{base}/{quote(language, safe="")}/{kind}/{quote(value, safe="")}'


def relation_predicate(name):
    """WN-LMF uses snake_case; the WordNet RDF vocabulary uses camelCase."""
    first, *rest = name.split('_')
    return WN[first + ''.join(part.capitalize() for part in rest)]


def _lexicon_frames(lexicon, base):
    """Read the small frame table once per lexicon per export.

    wn's public Sense.frames() only returns frames used by that sense. Subset
    RDF exports on en-word.net also declare the complete lexicon frame table.
    This adapter uses the wn 0.9.4 schema (pinned in requirements), avoiding a
    full lexicon/sense export. Older WN-LMF data has no frame IDs; use stable
    label hashes, scoped to the lexicon, instead of borrowing English IDs.
    """
    from wn._db import connect

    rows = connect().execute('''
        SELECT DISTINCT sb.id, sb.frame
          FROM syntactic_behaviours AS sb
          JOIN lexicons AS lex ON lex.rowid = sb.lexicon_rowid
         WHERE lex.id = ? AND lex.version = ?
         ORDER BY sb.id, sb.frame
    ''', (lexicon.id, lexicon.version))
    frames = []
    for identifier, label in rows:
        identifier = ('id-' + identifier if identifier else
                      'label-' + hashlib.sha256(label.encode('utf-8')).hexdigest())
        frames.append({
            'uri': resource_uri(base, lexicon.language, 'frame',
                                f'{lexicon.id}:{lexicon.version}:{identifier}'),
            'label': label, 'language': lexicon.language,
        })
    return frames


def export_document(synsets, *, base, kind, value, languages, relation=None):
    """Use native lexical ids and source metadata, without inventing licences.

    pld resolves queries; wn supplies the lexical-entry/sense identifiers and
    stored relations which pld's public API does not expose in full.
    """
    records = []
    frames_by_lexicon = {}
    for synset in synsets:
        raw = WordnetService.raw_synset(synset.id)
        lexicon = raw.lexicon()
        language = lexicon.language
        uri = resource_uri(base, language, 'synset', raw.id)
        lexicon_key = (lexicon.id, lexicon.version)
        if lexicon_key not in frames_by_lexicon:
            frames_by_lexicon[lexicon_key] = _lexicon_frames(lexicon, base)
        frames = frames_by_lexicon[lexicon_key]

        def synset_ref(target):
            lang = target.lexicon().language
            return {'id': target.id, 'language': lang,
                    'uri': resource_uri(base, lang, 'synset', target.id)}

        def sense_ref(sense):
            parent = synset_ref(sense.synset())
            return {'id': sense.id, 'uri': parent['uri'] + '#sense-' + quote(sense.id, safe='')}

        entries = []
        for word in sorted(raw.words(), key=lambda word: word.id):
            entry_uri = resource_uri(base, language, 'lemma', word.lemma()) + '#entry-' + quote(word.id, safe='')
            senses = []
            frame_labels = set()
            for sense in sorted(word.senses(), key=lambda sense: sense.id):
                if sense.synset().id != raw.id:
                    continue
                frame_labels.update(sense.frames())
                senses.append({
                    **sense_ref(sense), 'examples': sense.examples(),
                    'relations': {name: sorted((sense_ref(target) for target in targets), key=lambda ref: ref['uri'])
                                  for name, targets in sorted(sense.relations().items())},
                })
            entries.append({
                'id': word.id, 'uri': entry_uri, 'lemma': word.lemma(), 'senses': senses,
                'frames': sorted(frame['uri'] for frame in frames if frame['label'] in frame_labels),
            })

        records.append({
            'id': raw.id, 'wordKey': synset.id, 'uri': uri, 'language': language,
            'ili': synset.ili, 'partOfSpeech': synset.pos, 'lemmas': synset.lemmas(),
            'definition': synset.definition(), 'examples': synset.examples(),
            'lexfile': raw.metadata().get('subject'),
            'lexicon': {
                'id': lexicon.id, 'version': lexicon.version, 'language': language,
                'label': lexicon.label, 'license': lexicon.license, 'url': lexicon.url,
                'uri': f'{base}/#lexicon-{quote(lexicon.id + ":" + lexicon.version, safe="")}',
            },
            'entries': entries,
            'relations': {name: sorted((synset_ref(target) for target in targets), key=lambda ref: ref['uri'])
                          for name, targets in sorted(raw.relations().items())},
        })
    return {
        'schemaVersion': 1,
        'query': {'type': kind, 'value': value, 'languages': languages, 'relation': relation},
        'count': len(records), 'synsets': sorted(records, key=lambda item: item['uri']),
        'frames': sorted((frame for frames in frames_by_lexicon.values() for frame in frames),
                         key=lambda frame: frame['uri']),
    }


def export_graph(document):
    graph = Graph()
    for prefix, namespace in [('ontolex', ONTOLEX), ('vartrans', VARTRANS),
                              ('synsem', SYNSEM), ('wn', WN), ('ili', ILI), ('skos', SKOS)]:
        graph.bind(prefix, namespace)

    def blank_node(*parts):
        # RDF/XML nodeIDs must start with a letter, even when Turtle accepts
        # a leading digit. Keep names deterministic for stable serialization.
        return BNode('b' + hashlib.sha256('\0'.join(map(str, parts)).encode('utf-8')).hexdigest())

    def text_node(subject, predicate, text, language, index=0):
        node = blank_node(subject, predicate, index)
        graph.add((subject, predicate, node))
        graph.add((node, RDF.value, Literal(text, lang=language)))

    def relation_node(subject, relation, target, *, sense=False):
        predicate = relation_predicate(relation)
        node = blank_node(subject, predicate, target)
        graph.add((subject, predicate, target))
        graph.add((node, VARTRANS.source, subject))
        graph.add((node, VARTRANS.category, predicate))
        graph.add((node, VARTRANS.target, target))
        if sense:
            graph.add((node, RDF.type, ONTOLEX.SenseRelation))

    def language_tag(language):
        # These application aliases are not BCP-47 language tags.
        return {'ua': 'uk', 'jp': 'ja'}.get(language, language)

    for frame in document.get('frames', []):
        graph.add((URIRef(frame['uri']), RDFS.label,
                   Literal(frame['label'], lang=language_tag(frame['language']))))

    for item in document['synsets']:
        subject = URIRef(item['uri'])
        language = language_tag(item['language'])
        lexicon = item['lexicon']
        lexicon_uri = URIRef(lexicon['uri'])
        pos = WN[POS[item['partOfSpeech']]]
        graph.add((subject, RDF.type, ONTOLEX.LexicalConcept))
        graph.add((subject, SKOS.inScheme, lexicon_uri))
        graph.add((subject, WN.partOfSpeech, pos))
        if item['ili']:
            graph.add((subject, WN.ili, ILI[item['ili']]))
        if item.get('lexfile'):
            graph.add((subject, WN.lexfile, Literal(item['lexfile'])))
        if item['definition']:
            text_node(subject, WN.definition, item['definition'], language)
        for index, example in enumerate(item['examples']):
            text_node(subject, WN.example, example, language, index)
        for relation, targets in item['relations'].items():
            for target in targets:
                relation_node(subject, relation, URIRef(target['uri']))
        for entry in item['entries']:
            entry_uri = URIRef(entry['uri'])
            form = URIRef(entry['uri'] + '-form')
            graph.add((entry_uri, RDF.type, ONTOLEX.LexicalEntry))
            graph.add((entry_uri, ONTOLEX.canonicalForm, form))
            graph.add((form, RDF.type, ONTOLEX.Form))
            graph.add((form, ONTOLEX.writtenRep, Literal(entry['lemma'], lang=language)))
            graph.add((entry_uri, WN.partOfSpeech, pos))
            for frame in entry.get('frames', []):
                graph.add((entry_uri, SYNSEM.synBehavior, URIRef(frame)))
            for sense in entry['senses']:
                sense_uri = URIRef(sense['uri'])
                graph.add((entry_uri, ONTOLEX.sense, sense_uri))
                graph.add((sense_uri, RDF.type, ONTOLEX.LexicalSense))
                graph.add((sense_uri, ONTOLEX.isLexicalizedSenseOf, subject))
                for relation, targets in sense['relations'].items():
                    for target in targets:
                        relation_node(sense_uri, relation, URIRef(target['uri']), sense=True)
                for index, example in enumerate(sense['examples']):
                    text_node(sense_uri, WN.example, example, language, index)
    return graph
