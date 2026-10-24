"""Integration checks against installed OMW data (no downloads required)."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import passivlingo_dictionary as pld
import wn

from encoders.WordEncoder import WordEncoder
from imageCreation.CombinedImageWrapper import main as create_image
from wordnet_service import WordnetService


class WordnetServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.languages = {lexicon.language for lexicon in wn.lexicons()}
        if 'en' not in cls.languages:
            raise unittest.SkipTest('Install English OMW data with wn.download("ewn:2020")')

    def setUp(self):
        self.service = WordnetService('en')
        self.cat = self.service.wordnet.synsets('cat', lang='en')[0]

    def test_search_preserves_frontend_contract(self):
        results = self.service.search(woi='cat')
        data = json.loads(WordEncoder().encode(results))
        self.assertTrue(data)
        item = next(item for item in data if item['wordKey'] == self.cat.id)
        self.assertEqual(self.service.wordnet.backend, 'omw')
        self.assertEqual(item['lang'], 'en')
        self.assertEqual(item['pos'], 'Noun')
        self.assertEqual(item['wordnetId'], 'own')
        self.assertEqual([item['name'], *item['synonyms']], self.cat.lemmas())
        self.assertEqual(item['definition'], self.cat.definition())
        self.assertEqual(item['ili'], self.cat.ili)
        self.assertEqual(item['linguisticCounter']['hypernym'], len(self.cat.hypernyms()))
        self.assertEqual(item['genericLanguageDescriptions']['descriptionLookup']['en'], '')
        self.assertTrue(item['offset'].isdigit())
        self.assertIn(item['name'], item['lodViews'])

    def test_word_key_and_graph_id_keep_the_language(self):
        graph_id = self.service.raw_synset(self.cat.id).id
        for identifier in (self.cat.id, graph_id):
            with self.subTest(identifier=identifier):
                resolved = self.service.synset(identifier)
                self.assertIsInstance(resolved, pld.Synset)
                self.assertEqual(resolved.id, self.cat.id)
                self.assertEqual(resolved.lang, 'en')
                self.assertTrue(resolved.hypernyms())

    def test_queries_can_use_different_request_threads(self):
        # setUp already opened the database on the main thread. Flask's
        # request threads must also be able to use wn's cached connection.
        def lookup(_):
            return WordnetService('en').search(woi='cat')[0].wordKey

        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(lookup, range(6)))
        self.assertEqual(results, [self.cat.id] * 6)

    def test_relation_navigation(self):
        for form, pos, category in (
            ('cat', 'n', 'hypernym'), ('cat', 'n', 'hyponym'),
            ('house', 'n', 'meronym'), ('finger', 'n', 'holonym'),
            ('hot', 'a', 'antonym'), ('snore', 'v', 'entailment'),
        ):
            with self.subTest(category=category):
                source = self.service.wordnet.synsets(form, pos=pos, lang='en')[0]
                expected = source.relations(category)[category]
                self.assertTrue(expected)
                actual = self.service.search(wordkey=source.id, lang='en', category=category)
                self.assertEqual({item.wordKey for item in actual}, {item.id for item in expected})
                self.assertTrue(all(item.lang == 'en' for item in actual))

    def test_lemma_and_part_of_speech(self):
        results = self.service.search(woi='houses', lemma='house', pos='n', lang='en')
        self.assertTrue(results)
        self.assertTrue(all(item.pos == 'Noun' for item in results))

    def test_examples(self):
        house = self.service.wordnet.synsets('house', pos='n', lang='en')[0]
        examples = self.service.synset(house.id).examples()
        self.assertTrue(examples)
        self.assertEqual(examples, house.examples())

    def test_lookup_identifier_forms(self):
        raw_id = self.service.raw_synset(self.cat.id).id
        bare_id = '-'.join(raw_id.split('-')[-2:])
        for identifier in (self.cat.id, raw_id, bare_id):
            with self.subTest(identifier=identifier):
                result = self.service.lookup('synset', identifier)
                self.assertEqual([item.wordKey for item in result], [self.cat.id])
        self.assertEqual(self.service.lookup('ili', self.cat.ili)[0].ili, self.cat.ili)
        with self.assertRaises((ValueError, wn.Error, pld.Error)):
            self.service.lookup('synset', f'nonexistent-{bare_id}')

    def test_lookup_language_filters_are_strict(self):
        if 'de' not in self.languages:
            self.skipTest('German OMW data is not installed')
        service = WordnetService('en,de')
        self.assertEqual({item.lang for item in service.lookup('ili', self.cat.ili)}, {'en', 'de'})
        german = service.lookup('ili', self.cat.ili, lang='de')
        self.assertTrue(german)
        self.assertEqual({item.lang for item in german}, {'de'})
        self.assertEqual({item.ili for item in german}, {self.cat.ili})
        german_only = WordnetService('de')
        self.assertEqual({item.lang for item in german_only.lookup('lemma', 'Katze')}, {'de'})
        self.assertEqual({item.lang for item in german_only.lookup('ili', self.cat.ili)}, {'de'})
        self.assertEqual(service.lookup('synset', self.cat.id, lang='de'), [])
        self.assertEqual(service.lookup('synset', self.cat.id, lang='de', relation='hypernym'), [])
        self.assertEqual(german_only.lookup('synset', self.cat.id), [])
        german_id = german_only.raw_synset(german[0].wordKey).id
        self.assertEqual([item.wordKey for item in service.lookup('synset', german_id)], [german[0].wordKey])
        self.assertEqual(service.lookup('synset', german_id, lang='en'), [])

    def test_synset_lookup_preserves_exact_identity_with_all_languages_selected(self):
        languages = [code for code in ('en', 'de', 'fr', 'es', 'it', 'nl', 'pt') if code in self.languages]
        service = WordnetService(languages)
        raw_id = service.raw_synset(self.cat.id).id
        bare_id = '-'.join(raw_id.split('-')[-2:])
        # No ILI expansion even if equivalents exist in the same language.
        with patch.object(pld.Synset, 'translate', side_effect=AssertionError('Unexpected ILI expansion')):
            for identifier in (raw_id, bare_id, self.cat.id):
                with self.subTest(identifier=identifier):
                    self.assertEqual([item.id for item in service.lookup_synsets('synset', identifier)], [self.cat.id])
                    self.assertEqual([item.id for item in service.lookup_synsets('synset', identifier, lang='en')], [self.cat.id])
            expected = {item.id for item in self.cat.hypernyms()}
            self.assertTrue(expected)
            self.assertEqual({item.id for item in service.lookup_synsets('synset', raw_id, relation='hypernym')}, expected)

    def test_multilingual_direct_matches_never_invoke_lemmatization(self):
        # English is last: misses in preceding languages must not load models
        # before we discover the English match. Assert the expensive operation
        # is absent instead of relying on a machine-dependent time threshold.
        languages = [code for code in ('de', 'nl', 'fr', 'es', 'pt', 'it', 'en')
                     if code in self.languages]
        with patch('wordnet_service.LEMMATIZERS.lemmatize', side_effect=AssertionError('Unexpected NLP fallback')):
            service = WordnetService(languages)
            result = service.lookup('lemma', 'spouse')
            self.assertTrue(result)
            self.assertEqual({item.lang for item in result}, {'en'})
            self.assertEqual({item.wordKey for item in result},
                             {item.wordKey for item in service.search(woi='spouse')})

    def test_direct_search_collects_all_selected_languages(self):
        if 'fr' not in self.languages:
            self.skipTest('French OMW data is not installed')
        with patch('wordnet_service.LEMMATIZERS.lemmatize', side_effect=AssertionError('Unexpected NLP fallback')):
            service = WordnetService('en,fr')
            result = service.lookup_synsets('lemma', 'chat')
        self.assertEqual({item.lang for item in result}, {'en', 'fr'})
        expected = {raw.id for language in ('en', 'fr') for raw in wn.synsets('chat', lang=language)}
        self.assertEqual({service.raw_synset(item.id).id for item in result}, expected)

    def test_english_pivot_does_not_suppress_filtered_language_fallback(self):
        if 'de' not in self.languages:
            self.skipTest('German OMW data is not installed')
        # spouse exists in English only. Neither a hidden English pivot nor
        # another configured language may short-circuit the German fallback.
        for languages, lang in [('de', None), ('en,de', 'de')]:
            with self.subTest(languages=languages):
                with patch('wordnet_service.LEMMATIZERS.lemmatize', return_value=['Katze']) as fallback:
                    result = WordnetService(languages).lookup('lemma', 'spouse', lang=lang)
                fallback.assert_called_once_with('spouse', language='de')
                self.assertTrue(result)
                self.assertEqual({item.lang for item in result}, {'de'})

    def test_inflected_words_still_use_language_specific_lemmatization(self):
        for language, form, lemma in [('en', 'spouses', 'spouse'), ('de', 'Häuser', 'Haus')]:
            if language not in self.languages:
                continue
            with self.subTest(language=language):
                service = WordnetService(language)
                result = service.lookup('lemma', form)
                self.assertTrue(result)
                self.assertEqual({item.lang for item in result}, {language})
                self.assertTrue(any(lemma in [item.name, *item.synonyms] for item in result))

    def test_lookup_validation_and_missing_results(self):
        for kind, value, lang in [('ili', 'cat', None), ('lemma', '', None),
                                 ('other', 'cat', None), ('lemma', 'cat', 'xx')]:
            with self.subTest(kind=kind, value=value), self.assertRaises(ValueError):
                self.service.lookup(kind, value, lang)
        self.assertEqual(self.service.lookup('ili', 'i9999999999'), [])
        self.assertEqual(self.service.lookup('lemma', 'zzzznonexistentwordzzzz'), [])

    def test_missing_word_and_invalid_queries(self):
        self.assertEqual(self.service.search(woi='zzzznonexistentwordzzzz'), [])
        for query in ({}, {'ili': self.cat.ili}, {'woi': 'cat', 'category': 'invalid'},
                      {'woi': 'cat', 'pos': 'invalid'}):
            with self.subTest(query=query), self.assertRaises(ValueError):
                self.service.search(**query)
        for identifier in ('', 'not-a-synset', 'missing.n.00000000.ewn'):
            with self.subTest(identifier=identifier), self.assertRaises((ValueError, wn.Error, pld.Error)):
                self.service.synset(identifier)

    def test_german_translation_and_relations(self):
        if 'de' not in self.languages:
            self.skipTest('German OMW data is not installed')
        service = WordnetService('en,de')
        translated = service.search(ili=self.cat.ili, lang='de')
        self.assertTrue(translated)
        german = translated[0]
        self.assertEqual(german.lang, 'de')
        self.assertEqual(german.ili, self.cat.ili)
        self.assertTrue(german.genericLanguageDescriptions['descriptionLookup']['en'])
        resolved = service.synset(german.wordKey)
        self.assertEqual(resolved.lang, 'de')
        self.assertEqual(resolved.id, german.wordKey)
        self.assertTrue(service.search(wordkey=german.wordKey, lang='de', category='hypernym'))

    @unittest.skipUnless(shutil.which('dot'), 'Graphviz is not installed')
    def test_graph_uses_public_synsets_and_renders_png(self):
        langs = 'en,de' if 'de' in self.languages else 'en'
        with tempfile.TemporaryDirectory() as directory:
            result = create_image({
                'fileName': f'{Path(directory).name}/migration',
                'synsetId': self.service.raw_synset(self.cat.id).id,
                'level': '1', 'maxLeafNodes': '2', 'filterLangs': langs,
                'synonymCount': '2', 'woi': 'cat', 'hierarchy': 'True', 'partWhole': 'True',
            })
            self.assertTrue(result['result'], result['msg'])
            png = Path(result['filePath'])
            self.assertTrue(png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            graph = png.with_suffix('.dot').read_text()
            self.assertIn('cat', graph)
            self.assertIn('is a', graph)
            if 'de' in self.languages:
                self.assertIn('Katze', graph)


if __name__ == '__main__':
    unittest.main()
