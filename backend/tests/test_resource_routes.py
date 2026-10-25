"""HTTP and RDF integration checks against the installed OMW lexicons."""

import unittest
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, parse_qs
from unittest.mock import patch

from flask import Flask
from rdflib import Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, RDFS, SKOS
import passivlingo_dictionary as pld
import wn

from resource_routes import init_resources
from wordnet_export import export_graph, relation_predicate, ONTOLEX, WN, ILI, VARTRANS, SYNSEM


def make_app(**config):
    app = Flask(__name__)
    app.config.update(TESTING=True, WORDNET_LANGUAGES=['en', 'de'],
                      WORDNET_URL_PREFIX='', WORDNET_PUBLIC_URL='https://wordnet.example')
    app.config.update(config)
    init_resources(app)
    return app


class NegotiationTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.client = self.app.test_client()

    def test_all_lookup_routes_negotiate_before_loading_javascript(self):
        for kind, value in [('lemma', 'dog'), ('synset', 'ewn-02124272-n'),
                            ('ili', 'i46593'), ('id', '02124272-n')]:
            for language in ['', 'en/']:
                for media, format in [('text/html', 'view'), ('application/json', 'api'),
                                      ('text/turtle', 'ttl'), ('application/rdf+xml', 'rdf'),
                                      ('application/xml', 'xml')]:
                    with self.subTest(kind=kind, language=language, media=media):
                        response = self.client.get(f'/{language}{kind}/{value}', headers={'Accept': media})
                        self.assertEqual(response.status_code, 303)
                        canonical = 'synset' if kind == 'id' else kind
                        self.assertEqual(response.location, f'/{format}/{language}{canonical}/{value}')
                        self.assertIn('Accept', response.vary)

    def test_accept_quality_specificity_and_exclusions(self):
        for accept, target in [
            (None, 'view'), ('*/*', 'view'), ('application/*', 'api'),
            ('application/json;q=0.9,text/html;q=0.2', 'api'),
            ('text/turtle;q=0.8,application/rdf+xml;q=1', 'rdf'),
            ('application/xml;q=1,application/rdf+xml;q=0.5', 'xml'),
            ('application/xml;q=0,application/rdf+xml;q=1', 'rdf'),
            ('text/html;q=0,*/*;q=0.5', 'api'),
            ('text/*;q=0.5,text/html;q=0.1', 'ttl'),
            ('text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'view'),
            ('application/pdf', None), ('*/*;q=0', None), ('', None),
        ]:
            with self.subTest(accept=accept):
                headers = {} if accept is None else {'Accept': accept}
                response = self.client.get('/lemma/dog', headers=headers)
                self.assertEqual(response.status_code, 303 if target else 406)
                if target:
                    self.assertEqual(response.location, f'/{target}/lemma/dog')

    def test_prefix_encoded_values_and_query_survive_redirect(self):
        client = make_app(WORDNET_URL_PREFIX='/wordnet',
                          WORDNET_PUBLIC_URL='https://wordnet.example/wordnet').test_client()
        value = 'café & ice/cream?#%;'
        response = client.get('/lemma/' + quote(value, safe='') + '?langs=de,fr&word=caf%C3%A9',
                              headers={'Accept': 'text/turtle'})
        self.assertEqual(response.status_code, 303)
        target = urlsplit(response.location)
        self.assertEqual(unquote(target.path), '/wordnet/ttl/lemma/' + value)
        self.assertEqual(parse_qs(target.query), {'langs': ['de,fr'], 'word': ['café']})

    def test_fixed_formats_reject_unacceptable_media(self):
        for path, accept in [('/api/en/lemma/dog', 'text/html'),
                             ('/ttl/en/lemma/dog', 'text/turtle;q=0,*/*;q=1'),
                             ('/rdf/en/lemma/dog', 'application/json'),
                             ('/xml/en/lemma/dog', 'application/rdf+xml'),
                             ('/rdf/en/lemma/dog', 'application/xml'),
                             ('/xml/en/lemma/dog', 'application/xml;q=0,*/*;q=1')]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers={'Accept': accept}).status_code, 406)

    def test_view_and_existing_api_routes_are_not_captured(self):
        for path in ['/view/lemma/dog', '/api/dict/words/', '/view/en/lemma/dog', '/assets/en.json']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_invalid_configuration_fails_at_startup(self):
        for config in [dict(WORDNET_LANGUAGES=[]), dict(WORDNET_LANGUAGES='english'),
                       dict(WORDNET_URL_PREFIX='wordnet'), dict(WORDNET_URL_PREFIX='//evil.test'),
                       dict(WORDNET_PUBLIC_URL='https://wordnet.example/wrong-prefix'),
                       dict(WORDNET_PUBLIC_URL='https://user:password@wordnet.example')]:
            with self.subTest(config=config), self.assertRaises(ValueError):
                make_app(**config)


class RepresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not {'en', 'de'} <= {lexicon.language for lexicon in wn.lexicons()}:
            raise unittest.SkipTest('Install English and German OMW lexicons for export integration tests')

    def setUp(self):
        self.app = make_app()
        self.client = self.app.test_client()

    def test_json_preserves_native_identity_lexical_data_and_source_metadata(self):
        response = self.client.get('/api/en/lemma/dog')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')
        document = response.json
        self.assertEqual(document['schemaVersion'], 1)
        self.assertEqual(document['query']['languages'], ['en'])
        self.assertEqual(document['count'], len(wn.synsets('dog', lang='en')))
        for item in document['synsets']:
            raw = wn.synset(item['id'])
            self.assertEqual(item['language'], 'en')
            self.assertEqual(item['lemmas'], raw.lemmas())
            self.assertEqual(item['lexicon']['license'], raw.lexicon().license)
            self.assertEqual(item['lexicon']['version'], raw.lexicon().version)
            self.assertEqual({entry['id'] for entry in item['entries']}, {word.id for word in raw.words()})
            self.assertEqual({sense['id'] for entry in item['entries'] for sense in entry['senses']},
                             {sense.id for sense in raw.senses()})
            self.assertEqual({name: {ref['id'] for ref in targets} for name, targets in item['relations'].items()},
                             {name: {target.id for target in targets} for name, targets in raw.relations().items()})
            self.assertTrue(item['uri'].startswith('https://wordnet.example/en/synset/'))

    def test_all_languages_and_prefix_subset_filters(self):
        for suffix, expected in [('ili/i46593', {'en', 'de'}), ('de/ili/i46593', {'de'}),
                                 ('ili/i46593?langs=de', {'de'}),
                                 ('synset/ewn-02124272-n', {'en'}),
                                 ('en/id/02124272-n', {'en'})]:
            with self.subTest(suffix=suffix):
                response = self.client.get('/api/' + suffix)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual({item['language'] for item in response.json['synsets']}, expected)

    def test_rdf_formats_describe_the_same_graph_with_forms_relations_and_ili(self):
        for path in ['en/lemma/dog', 'de/ili/i46593', 'ili/i46593']:
            with self.subTest(path=path):
                turtle = self.client.get('/ttl/' + path)
                xml = self.client.get('/rdf/' + path)
                self.assertEqual(turtle.status_code, 200, turtle.data)
                self.assertEqual(xml.status_code, 200, xml.data)
                graph = Graph().parse(data=turtle.data, format='turtle')
                self.assertTrue(isomorphic(graph, Graph().parse(data=xml.data, format='xml')))
                document = self.client.get('/api/' + path).json
                for item in document['synsets']:
                    subject = URIRef(item['uri'])
                    self.assertIn((subject, RDF.type, ONTOLEX.LexicalConcept), graph)
                    self.assertIn((subject, WN.ili, ILI[item['ili']]), graph)
                    self.assertIn((subject, SKOS.inScheme, URIRef(item['lexicon']['uri'])), graph)
                    for entry in item['entries']:
                        form = graph.value(URIRef(entry['uri']), ONTOLEX.canonicalForm)
                        self.assertIn((form, ONTOLEX.writtenRep,
                                       Literal(entry['lemma'], lang=item['language'])), graph)
                    for relation, targets in item['relations'].items():
                        for target in targets:
                            self.assertIn((subject, relation_predicate(relation), URIRef(target['uri'])), graph)
                            nodes = set(graph.subjects(VARTRANS.source, subject)) & set(
                                graph.subjects(VARTRANS.target, URIRef(target['uri']))) & set(
                                graph.subjects(VARTRANS.category, relation_predicate(relation)))
                            self.assertEqual(len(nodes), 1)
                            self.assertIsNone(graph.value(next(iter(nodes)), RDF.type))

    def test_english_dog_graph_matches_en_word_net_apart_from_uris_and_known_data_difference(self):
        if not any(lex.id == 'ewn' and lex.version == '2020' for lex in wn.lexicons()):
            self.skipTest('Comparison fixture targets the installed EWN 2020 dataset')
        reference = Graph().parse(Path(__file__).parent / 'fixtures' / 'en-word-net-i46360.ttl')
        document = self.client.get('/api/en/ili/i46360').json
        local = Graph().parse(data=self.client.get('/ttl/en/ili/i46360').data, format='turtle')
        item, = document['synsets']
        site = 'https://en-word.net/'
        remap = {URIRef(item['lexicon']['uri']): URIRef(site)}
        for entry in item['entries']:
            reference_entry = URIRef(site + 'lemma/' + entry['lemma'].replace(' ', '_') + '-n')
            remap[URIRef(entry['uri'])] = reference_entry
            remap[local.value(URIRef(entry['uri']), ONTOLEX.canonicalForm)] = reference.value(
                reference_entry, ONTOLEX.canonicalForm)
            for sense in entry['senses']:
                remap[URIRef(sense['uri'])] = URIRef(str(reference_entry) + '#02086723-n')
        for frame in document['frames']:
            remap[URIRef(frame['uri'])] = reference.value(
                predicate=RDFS.label, object=Literal(frame['label'], lang='en'), any=False)

        def normalize(term):
            if term in remap:
                return remap[term]
            if isinstance(term, URIRef) and str(term).startswith('https://wordnet.example/en/synset/ewn-'):
                return URIRef(str(term).replace('https://wordnet.example/en/synset/ewn-', site + 'synset/'))
            return term

        normalized = Graph()
        for triple in local:
            normalized.add(tuple(normalize(term) for term in triple))
        # EWN 2020 also puts a dog in a pack. Preserve this stored relation in
        # exports; remove its direct + reified triples only for this comparison.
        dog = URIRef(site + 'synset/02086723-n')
        pack = URIRef(site + 'synset/08011383-n')
        self.assertIn((dog, WN.holoMember, pack), normalized)
        normalized.remove((dog, WN.holoMember, pack))
        nodes = list(normalized.subjects(VARTRANS.target, pack))
        self.assertEqual(len(nodes), 1)
        for node in nodes:
            normalized.remove((node, None, None))
        self.assertEqual(len(local), len(reference) + 4)
        self.assertTrue(isomorphic(normalized, reference))

    def test_verb_frame_links_resolve_to_stored_labels_and_survive_both_serializations(self):
        document = self.client.get('/api/en/lemma/run').json
        graph = export_graph(document)
        expected = set()
        for item in document['synsets']:
            for entry in item['entries']:
                for sense in entry['senses']:
                    expected.update((URIRef(entry['uri']), Literal(label, lang='en'))
                                    for label in wn.sense(sense['id']).frames())
        actual = {(entry, label) for entry, _, frame in graph.triples((None, SYNSEM.synBehavior, None))
                  for label in graph.objects(frame, RDFS.label)}
        self.assertTrue(expected)
        self.assertEqual(actual, expected)
        for format in ['turtle', 'xml']:
            self.assertTrue(isomorphic(graph, Graph().parse(data=graph.serialize(format=format), format=format)))

    def test_serializer_escapes_rdf_literals_and_preserves_sense_relations(self):
        document = self.client.get('/api/en/lemma/hot').json
        text = 'café "quoted" & <angle> \\ newline\nnext line'
        document['synsets'][0]['definition'] = text
        expected = export_graph(document)
        self.assertTrue(any(sense['relations'] for item in document['synsets']
                            for entry in item['entries'] for sense in entry['senses']))
        for item in document['synsets']:
            for entry in item['entries']:
                for sense in entry['senses']:
                    for relation, targets in sense['relations'].items():
                        for target in targets:
                            nodes = set(expected.subjects(VARTRANS.source, URIRef(sense['uri']))) & set(
                                expected.subjects(VARTRANS.target, URIRef(target['uri']))) & set(
                                expected.subjects(VARTRANS.category, relation_predicate(relation)))
                            self.assertEqual(len(nodes), 1)
                            self.assertIn((next(iter(nodes)), RDF.type, ONTOLEX.SenseRelation), expected)
        for format in ['turtle', 'xml']:
            with self.subTest(format=format):
                graph = Graph().parse(data=expected.serialize(format=format), format=format)
                self.assertTrue(isomorphic(expected, graph))
                self.assertIn(Literal(text, lang='en'), graph.objects(None, RDF.value))

    def test_http_head_etag_and_conditional_requests(self):
        tags = []
        for format in ['api', 'ttl', 'rdf', 'xml']:
            path = f'/{format}/en/ili/i46593'
            response = self.client.get(path)
            tag = response.headers['ETag']
            tags.append(tag)
            self.assertEqual(response.headers['Content-Location'], path)
            self.assertIn('rel="alternate"', response.headers['Link'])
            self.assertIn('Accept', response.vary)
            self.assertEqual(self.client.get(path).headers['ETag'], tag)
            head = self.client.head(path)
            self.assertEqual(head.status_code, 200)
            self.assertEqual(head.data, b'')
            self.assertEqual(head.content_length, response.content_length)
            cached = self.client.get(path, headers={'If-None-Match': tag})
            self.assertEqual(cached.status_code, 304)
            self.assertEqual(cached.data, b'')
            self.assertEqual(cached.headers['ETag'], tag)
        self.assertEqual(len(set(tags)), 4)
        self.assertNotEqual(self.client.get('/api/de/ili/i46593').headers['ETag'], tags[0])
        head = self.client.head('/en/lemma/dog', headers={'Accept': 'text/html'})
        self.assertEqual(head.status_code, 303)
        self.assertEqual(head.data, b'')

    def test_explicit_public_base_and_prefix_ignore_forwarded_host_headers(self):
        client = make_app(WORDNET_URL_PREFIX='/wordnet',
                          WORDNET_PUBLIC_URL='https://public.example/wordnet').test_client()
        response = client.get('/api/de/ili/i46593', headers={
            'Host': 'internal:5000', 'X-Forwarded-Host': 'spoofed.example',
            'X-Forwarded-Proto': 'http', 'X-Forwarded-Prefix': '/wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(item['uri'].startswith('https://public.example/wordnet/de/synset/')
                            for item in response.json['synsets']))
        self.assertEqual(response.headers['Content-Location'], '/wordnet/api/de/ili/i46593')
        self.assertIn('</wordnet/view/de/ili/i46593>', response.headers['Link'])

    def test_relation_navigation_is_exportable(self):
        response = self.client.get('/api/de/ili/i46593?relation=hypernym')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.json['query']['relation'], 'hypernym')
        self.assertTrue(response.json['synsets'])
        self.assertEqual({item['language'] for item in response.json['synsets']}, {'de'})

    def test_synset_identity_is_exact_in_json_and_both_rdf_formats(self):
        identifier = 'ewn-02086723-n'
        subject = URIRef('https://wordnet.example/en/synset/' + identifier)
        for prefix in ['', 'en/']:
            with self.subTest(prefix=prefix):
                response = self.client.get('/api/' + prefix + 'synset/' + identifier)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json['count'], 1)
                self.assertEqual([(item['id'], item['language']) for item in response.json['synsets']], [(identifier, 'en')])
                for format, syntax in [('ttl', 'turtle'), ('rdf', 'xml')]:
                    response = self.client.get(f'/{format}/{prefix}synset/{identifier}')
                    self.assertEqual(response.status_code, 200)
                    graph = Graph().parse(data=response.data, format=syntax)
                    self.assertEqual(set(graph.subjects(RDF.type, ONTOLEX.LexicalConcept)), {subject})

    def test_conflicting_synset_language_returns_404_in_every_data_format(self):
        for format in ['api', 'ttl', 'rdf', 'xml']:
            for suffix in ['de/synset/ewn-02086723-n', 'de/id/ewn-02086723-n',
                           'synset/ewn-02086723-n?langs=de',
                           'de/synset/ewn-02086723-n?relation=hypernym']:
                with self.subTest(format=format, suffix=suffix):
                    response = self.client.get(f'/{format}/{suffix}')
                    self.assertEqual(response.status_code, 404)
                    self.assertTrue(response.json['error'])

    def test_invalid_queries_and_missing_resources_are_json_errors(self):
        for suffix, status in [
            ('en/ili/not-an-ili', 400), ('xx/lemma/dog', 400),
            ('en/lemma/dog?langs=de', 400), ('lemma/dog?langs=', 400),
            ('lemma/dog?langs=en&langs=de', 400), ('lemma/dog?unknown=1', 400),
            ('lemma/dog?relation=unknown', 400), ('en/lemma/%20', 400),
            ('en/lemma/zzzznonexistentwordzzzz', 404), ('ili/i9999999999', 404),
            ('en/synset/nonexistent-02124272-n', 404),
            ('en/synset/00000000-n', 404),
        ]:
            with self.subTest(suffix=suffix):
                response = self.client.get('/api/' + suffix)
                self.assertEqual(response.status_code, status, response.data)
                self.assertTrue(response.json['error'])
                self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_backend_failure_is_not_reported_as_a_missing_word(self):
        with patch('resource_routes.WordnetService.lookup_synsets', side_effect=pld.BackendError('unavailable')):
            with self.assertLogs(self.app.logger, level='ERROR'):
                response = self.client.get('/api/en/lemma/dog')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json['error'], 'WordNet data is temporarily unavailable')


if __name__ == '__main__':
    unittest.main()
