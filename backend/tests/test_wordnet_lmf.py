"""WN-LMF lookup integration tests against source data and the official DTD."""

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import PropertyMock, patch

from lxml import etree
import wn

from test_resource_routes import make_app
from wordnet_lmf import export_lmf


FIXTURES = Path(__file__).parent / 'fixtures'
DC = '{https://globalwordnet.github.io/schemas/dc/}'


class LmfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not {'en', 'de'} <= {lex.language for lex in wn.lexicons()}:
            raise unittest.SkipTest('Install English and German OMW lexicons for XML tests')

    def setUp(self):
        self.client = make_app().test_client()

    def read_xml(self, path, client=None):
        response = (client or self.client).get(path)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.mimetype, 'application/xml')
        self.assertIn(b'WN-LMF-1.4.dtd', response.data)
        parser = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
        root = etree.fromstring(response.data, parser)
        self.assertEqual(root.tag, 'LexicalResource')
        with (FIXTURES / 'WN-LMF-1.4.dtd').open('rb') as source:
            dtd = etree.DTD(source)
        dtd.validate(root)
        # The live site's lookup exports also have external relation targets.
        # Permit ONLY those missing IDs; all other DTD errors are failures.
        errors = [err.message for err in dtd.error_log if not (
            err.type_name == 'DTD_UNKNOWN_ID' and err.message.startswith('IDREF attribute target '))]
        self.assertEqual(errors, [])
        identifiers = [element.get('id') for element in root.iter() if element.get('id')]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for sense in root.findall('.//Sense'):
            self.assertIn(sense.get('synset'), identifiers)
            for identifier in sense.get('subcat', '').split():
                self.assertIn(identifier, identifiers)
        for synset in root.findall('.//Synset'):
            for identifier in synset.get('members', '').split():
                self.assertIn(identifier, identifiers)
        return root

    def test_english_lookup_preserves_native_identity_metadata_and_reference_structure(self):
        root = self.read_xml('/xml/en/ili/i46360')
        lexicon, = root.findall('Lexicon')
        synset, = lexicon.findall('Synset')
        raw = wn.synset(synset.get('id'))
        for attribute in ('id', 'label', 'language', 'email', 'license', 'version', 'url'):
            self.assertEqual(lexicon.get(attribute), getattr(raw.lexicon(), attribute))
        self.assertEqual({entry.get('id') for entry in lexicon.findall('LexicalEntry')},
                         {word.id for word in raw.words()})
        self.assertEqual({sense.get('id') for sense in lexicon.findall('.//Sense')},
                         {sense.id for sense in raw.senses()})
        self.assertEqual({(rel.get('relType'), rel.get('target')) for rel in synset.findall('SynsetRelation')},
                         {(name, target.id) for name, targets in raw.relations().items() for target in targets})
        self.assertEqual([example.text for example in synset.findall('Example')], raw.examples())
        reference = etree.parse(str(FIXTURES / 'en-word-net-i46360.xml'),
                                etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False))
        ref_synset = reference.find('.//Synset')
        for attribute in ('ili', 'partOfSpeech', 'lexfile'):
            self.assertEqual(synset.get(attribute), ref_synset.get(attribute))
        self.assertEqual(synset.findtext('Definition'), ref_synset.findtext('Definition'))
        self.assertEqual({(lemma.get('writtenForm'), lemma.get('partOfSpeech')) for lemma in root.findall('.//Lemma')},
                         {(lemma.get('writtenForm'), lemma.get('partOfSpeech')) for lemma in reference.findall('.//Lemma')})

    def test_lookup_kinds_language_filters_and_relations_keep_the_selected_synsets(self):
        for suffix, expected in [
            ('ili/i46360', {'en', 'de'}), ('de/ili/i46360', {'de'}),
            ('ili/i46360?langs=de', {'de'}), ('synset/ewn-02086723-n', {'en'}),
            ('en/id/02086723-n', {'en'}), ('en/lemma/dog', {'en'}),
            ('de/ili/i46360?relation=hypernym', {'de'}),
        ]:
            with self.subTest(suffix=suffix):
                root = self.read_xml('/xml/' + suffix)
                self.assertEqual({lex.get('language') for lex in root}, expected)
                document = self.client.get('/api/' + suffix).json
                self.assertEqual({ss.get('id') for ss in root.findall('.//Synset')},
                                 {item['id'] for item in document['synsets']})

    def test_verb_senses_are_deduplicated_ordered_and_linked_to_their_frames(self):
        root = self.read_xml('/xml/en/lemma/run')
        frames = {frame.get('id'): frame.get('subcategorizationFrame')
                  for frame in root.findall('.//SyntacticBehaviour')}
        self.assertTrue(frames)
        has_multiple_senses = False
        has_frame_links = False
        for entry in root.findall('.//LexicalEntry'):
            raw = wn.word(entry.get('id'))
            selected_ids = {sense.get('id') for sense in entry.findall('Sense')}
            self.assertEqual([sense.get('id') for sense in entry.findall('Sense')],
                             [sense.id for sense in raw.senses() if sense.id in selected_ids])
            has_multiple_senses |= len(selected_ids) > 1
            ranks = {sense.id: index for index, sense in enumerate(raw.senses(), start=1)}
            for sense in entry.findall('Sense'):
                self.assertEqual(int(sense.get('n')), ranks[sense.get('id')])
                labels = {frames[identifier] for identifier in sense.get('subcat', '').split()}
                self.assertEqual(labels, set(wn.sense(sense.get('id')).frames()))
                has_frame_links |= bool(labels)
        self.assertTrue(has_multiple_senses)
        self.assertTrue(has_frame_links)

    def test_forms_and_lexical_relations_preserve_the_source(self):
        has_relations = False
        for lemma in ('hot', 'mouse'):
            root = self.read_xml('/xml/en/lemma/' + lemma)
            for entry in root.findall('.//LexicalEntry'):
                raw = wn.word(entry.get('id'))
                self.assertEqual([entry.find('Lemma').get('writtenForm')] +
                                 [form.get('writtenForm') for form in entry.findall('Form')],
                                 list(map(str, raw.forms())))
                for sense in entry.findall('Sense'):
                    expected = {(name, target.id) for name, targets in wn.sense(sense.get('id')).relations().items()
                                for target in targets}
                    actual = {(rel.get('relType'), rel.get('target')) for rel in sense.findall('SenseRelation')}
                    self.assertTrue(expected <= actual)
                    has_relations |= bool(actual)
        self.assertTrue(has_relations)

    def test_xml_escapes_text_and_metadata_and_etag_tracks_xml_only_fields(self):
        path = '/xml/en/ili/i46360'
        original = self.client.get(path)
        text = 'café "quoted" & <angle> \\ newline\nnext line'
        definitions = [{'text': text, 'language': 'en', 'meta': {'source': 'https://example.org/?a=1&b="2"'}}]
        with patch('wordnet_lmf._export._export_definitions', return_value=definitions):
            root = self.read_xml(path)
            definition = root.find('.//Definition')
            self.assertEqual(definition.text, text)
            self.assertEqual(definition.get(DC + 'source'), definitions[0]['meta']['source'])
            changed = self.client.get(path, headers={'If-None-Match': original.headers['ETag']})
            self.assertEqual(changed.status_code, 200)
            self.assertNotEqual(changed.headers['ETag'], original.headers['ETag'])

    def test_multilingual_casa_is_grouped_by_lexicon(self):
        if not {'es', 'it', 'pt'} <= {lex.language for lex in wn.lexicons()}:
            self.skipTest('Install Spanish, Italian and Portuguese lexicons for casa test')
        client = make_app(WORDNET_LANGUAGES=['en', 'de', 'es', 'it', 'pt']).test_client()
        root = self.read_xml('/xml/lemma/casa', client)
        self.assertEqual({lex.get('language') for lex in root}, {'es', 'it', 'pt'})
        for lex in root:
            for synset in lex.findall('Synset'):
                self.assertEqual(wn.synset(synset.get('id')).lexicon().language, lex.get('language'))

    def test_dependencies_use_lmf_reference_attributes_without_fetching_them(self):
        dependencies = [{'id': 'source-wordnet', 'version': '1.0', 'url': 'https://example.org/wordnet.xml'}]
        with patch('wordnet_lmf._export._export_requires', return_value=dependencies):
            root = self.read_xml('/xml/en/ili/i46360')
        dependency, = root.findall('.//Requires')
        self.assertEqual(dict(dependency.attrib), {
            'ref': 'source-wordnet', 'version': '1.0', 'url': 'https://example.org/wordnet.xml'})

    def test_unmapped_and_proposed_ilis_use_the_lmf_conventions(self):
        proposed = {'text': 'A proposed definition for a new interlingual concept.', 'meta': {}}
        for ili, definition, expected in [(None, None, ''),
                                           (SimpleNamespace(id=None), proposed, 'in'),
                                           (SimpleNamespace(id='i46360'), proposed, 'i46360')]:
            with self.subTest(expected=expected), \
                    patch.object(wn.Synset, 'ili', new_callable=PropertyMock, return_value=ili), \
                    patch('wordnet_lmf._export._export_ili_definition', return_value=definition):
                data = export_lmf([SimpleNamespace(id='ewn-02086723-n')])
            root = etree.fromstring(data, etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False))
            synset = root.find('.//Synset')
            self.assertEqual(synset.get('ili'), expected)
            self.assertEqual(synset.findtext('ILIDefinition'), proposed['text'] if expected == 'in' else None)


if __name__ == '__main__':
    unittest.main()
