"""Regression checks for model reuse and concurrent fallback requests."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
import time
import unittest

from lemmatizer_cache import LemmatizerCache
from wordnet_service import WordnetService


class LemmatizerCacheTests(unittest.TestCase):
    def test_concurrent_requests_load_once_and_do_not_share_pipeline_execution(self):
        cache = LemmatizerCache()
        start = Barrier(4)
        active = False

        def infer(form):
            nonlocal active
            self.assertFalse(active, 'Concurrent use of one pipeline')
            active = True
            time.sleep(0.01)
            active = False
            return ['spouse']

        def load(language):
            # Release the GIL so competing requests can reach initialization.
            time.sleep(0.02)
            return SimpleNamespace(lemmatize=infer)

        def request(_):
            start.wait(timeout=5)
            return cache.lemmatize('spouses', language='en')

        with patch('lemmatizer_cache.FactoryMethods.getLemmatizer', side_effect=load) as factory:
            with ThreadPoolExecutor(max_workers=4) as executor:
                result = list(executor.map(request, range(4)))
        factory.assert_called_once_with('en')
        self.assertEqual(result, [['spouse']] * 4)

    def test_new_service_instances_reuse_warmed_models(self):
        cache = LemmatizerCache()
        with patch('lemmatizer_cache.FactoryMethods.getLemmatizer',
                   return_value=SimpleNamespace(lemmatize=lambda form: ['spouse'])) as factory:
            cache.warm(['en'])
            factory.assert_called_once_with('en')
            with patch('wordnet_service.LEMMATIZERS', cache):
                for _ in range(3):
                    results = WordnetService('en').lookup('lemma', 'spouses')
                    self.assertTrue(results)
                    self.assertTrue(all(item.lang == 'en' for item in results))
            factory.assert_called_once_with('en')

    def test_missing_optional_model_is_logged_once_and_does_not_break_exact_search(self):
        cache = LemmatizerCache()
        with patch('lemmatizer_cache.FactoryMethods.getLemmatizer', side_effect=OSError('model absent')) as factory:
            with self.assertLogs('lemmatizer_cache', level='WARNING') as logs:
                cache.warm(['en'])
                self.assertEqual(cache.lemmatize('spouses', language='en'), [])
                self.assertEqual(cache.lemmatize('spouses', language='en'), [])
            self.assertEqual(len(logs.output), 1)
            factory.assert_called_once_with('en')
        with patch('wordnet_service.LEMMATIZERS', cache):
            self.assertTrue(WordnetService('en').lookup('lemma', 'spouse'))
            self.assertEqual(WordnetService('en').lookup('lemma', 'spouses'), [])


if __name__ == '__main__':
    unittest.main()
