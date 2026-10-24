"""Reuse the dictionary's language models across requests in each worker."""

import logging
from threading import Lock

from passivlingo_dictionary.helpers.FactoryMethods import FactoryMethods


logger = logging.getLogger(__name__)


class LemmatizerCache:
    def __init__(self):
        self._entries = {}
        self._initialization_lock = Lock()

    def _get(self, language):
        # functools.lru_cache alone can initialize the same expensive model
        # more than once when concurrent requests first encounter a language.
        with self._initialization_lock:
            if language not in self._entries:
                try:
                    # Preserve 2.0.1's default lemmatization and model-path
                    # selection. Inject the cached callable through Wordnet's
                    # public lemmatizer argument; never patch library globals.
                    lemmatizer = FactoryMethods.getLemmatizer(language)
                except (OSError, ImportError) as error:
                    # Lemmatization is optional; exact WordNet lookups should
                    # still work if a deployment lacks a language model.
                    logger.warning('Lemmatization unavailable for %s: %s', language, error)
                    lemmatizer = None
                self._entries[language] = (lemmatizer, Lock())
            return self._entries[language]

    def lemmatize(self, form, *, language):
        lemmatizer, lock = self._get(language)
        if lemmatizer is None:
            return []
        # Keep concurrent inference from mutating the same spaCy pipeline.
        # Different languages use independent locks.
        with lock:
            return lemmatizer.lemmatize(form)

    def warm(self, languages):
        for language in languages:
            self._get(language)


LEMMATIZERS = LemmatizerCache()
