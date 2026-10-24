"""OMW queries and conversion to the browser's existing response format."""

from dataclasses import asdict
from functools import partial
from types import SimpleNamespace
import re

import passivlingo_dictionary as pld
import wn

from helpers.CommonHelper import CommonHelper
from lemmatizer_cache import LEMMATIZERS


# Flask serves concurrent read-only queries; wn otherwise caches a connection
# that can only be used by whichever request thread opened it first.
wn.config.allow_multithreading = True


POS_NAMES = {
    'n': 'Noun', 'v': 'Verb', 'a': 'Adjective', 's': 'Adjective',
    'r': 'Adverb', 't': 'Phrase', 'c': 'Conjunction', 'p': 'Adposition',
    'x': 'Other', 'u': 'Unknown',
}
RELATIONS = ('hypernym', 'hyponym', 'holonym', 'meronym', 'entailment', 'antonym')
DEFAULT_LANGUAGES = ('en', 'de', 'fr', 'es', 'it', 'nl', 'pt')


class WordnetService:
    def __init__(self, languages=None):
        self.languages = (
            languages.replace(',', ' ').split() if isinstance(languages, str)
            else list(languages or DEFAULT_LANGUAGES)
        ) or list(DEFAULT_LANGUAGES)
        # Check every selected language for a direct match before attempting
        # expensive morphology. The public callback disables automatic fallback
        # for this first pass and for lookups of known synset identifiers.
        self.wordnet = pld.Wordnet(backend='omw', lang=self.languages, lemmatizer=lambda form: [])

    def _lemma_synsets(self, form, languages, pos=None):
        matches = [synset for code in languages
                   for synset in self.wordnet.synsets(form, pos=pos, lang=code)]
        if matches:
            return matches

        # The callback API takes only the word, so bind each language explicitly.
        # Supplying lang on each query also avoids 2.0.1's implicit English pivot
        # leaking into a search restricted to another language.
        for code in languages:
            wordnet = pld.Wordnet(
                backend='omw', lang=self.languages,
                lemmatizer=partial(LEMMATIZERS.lemmatize, language=code),
            )
            matches.extend(wordnet.synsets(form, pos=pos, lang=code))
        return matches

    @staticmethod
    def raw_synset(identifier):
        """Accept the browser's word key or a native wn graph identifier."""
        if not identifier:
            raise ValueError('Invalid word key')
        try:
            return wn.synset(identifier)
        except wn.Error:
            # A lemma can itself contain periods (e.g. U.S.). Split at the
            # POS field instead of assuming the lemma is the first token.
            match = re.fullmatch(r'.+\.([nvarsxtcpu])\.(.+)', identifier)
            if not match:
                raise
            key = '-'.join(reversed(match[2].split('.'))) + '-' + match[1]
            return wn.synset(key)

    def _from_raw(self, raw):
        # In 2.0.1 Wordnet.synset(id) drops the language. Resolve through a
        # language-qualified public query so relations and labels retain it.
        identifier = '.'.join([raw.lemmas()[0], *reversed(raw.id.split('-'))])
        for synset in self.wordnet.synsets(raw.lemmas()[0], lang=raw.lexicon().language):
            if synset.id == identifier:
                return synset
        raise pld.BackendError(f'No such synset: {identifier}')

    def synset(self, identifier):
        return self._from_raw(self.raw_synset(identifier))

    def synsets_from_ili(self, ili, lang):
        # The public API translates existing Synsets but has no ILI entry
        # point. Use wn only to locate the stored concept, then use pld.
        return [self._from_raw(raw) for raw in wn.synsets(ili=ili, lang=lang)]

    def resolve_identifier(self, identifier):
        """Bare offsets use the English pivot; qualified ids stay exact."""
        if not re.fullmatch(r'\d{8}-[nvars]', identifier):
            return self.synset(identifier)
        candidates = []
        for lexicon in wn.lexicons(lang='en'):
            try:
                candidates.append(self.synset(f'{lexicon.id}-{identifier}'))
            except (wn.Error, pld.BackendError):
                continue
        if not candidates:
            raise wn.Error(f'No such synset: {identifier}; use a full lexicon-qualified identifier')
        if len(candidates) > 1:
            raise ValueError('Ambiguous synset identifier; include its lexicon prefix')
        return candidates[0]

    def lookup_synsets(self, kind, value, lang=None, relation=None):
        """Resolve shareable lookup URLs with strict result-language filtering."""
        value = value.strip()
        if not value:
            raise ValueError('A search value is required')
        if lang and lang not in self.languages:
            raise ValueError(f'Language {lang} is not enabled for this search')
        languages = [lang] if lang else self.languages
        if relation and relation not in RELATIONS:
            raise ValueError(f'Unknown relation: {relation}')

        if kind == 'lemma':
            synsets = self._lemma_synsets(value, languages)
        elif kind == 'ili':
            if not re.fullmatch(r'i\d+', value):
                raise ValueError('An ILI must be an i followed by digits, for example i46593')
            synsets = [synset for code in languages
                       for synset in self.synsets_from_ili(value, code)]
        elif kind == 'synset':
            source = self.resolve_identifier(value)
            # A synset ID identifies one synset in a particular lexicon, not its equivalents
            # across the ILI. A language filter can exclude it, never translate
            # it. Validate the source before following any relation as well.
            if source.lang not in languages:
                return []
            synsets = [source]
        else:
            raise ValueError(f'Unknown lookup type: {kind}')

        if relation:
            synsets = [related for synset in synsets
                       for related in (synset.relations(relation)[relation] if kind == 'synset'
                                       else self.relations(synset, relation))]

        # Multilingual lemma/ILI relation queries can project their targets
        # through the ILI. Synset queries stay anchored to the identified synset
        # and its own relation targets, including when all languages are selected.
        if relation and kind != 'synset':
            synsets = [translated for source in synsets for translated in
                       ([source] + source.translate(lang=languages) if source.ili else [source])]
        unique = {}
        for synset in synsets:
            if synset.lang in languages:
                unique.setdefault(synset.id, synset)
        return list(unique.values())

    def lookup(self, kind, value, lang=None, relation=None):
        return self.serialize(self.lookup_synsets(kind, value, lang, relation))

    def relations(self, synset, category):
        related = synset.relations(category)[category]
        # Preserve the browser's English fallback for incomplete lexicons.
        if not related and synset.lang != 'en' and synset.ili:
            for english in synset.translate(lang='en'):
                related.extend(english.relations(category)[category])
        return related

    def search(self, *, woi=None, wordkey=None, ili=None, lang=None,
               category=None, pos=None, lemma=None):
        if category and category not in (*RELATIONS, 'synonym'):
            raise ValueError(f'Unknown category: {category}')
        if pos and pos not in POS_NAMES:
            raise ValueError(f'Unknown part of speech: {pos}')

        if ili:
            if not lang:
                raise ValueError("'lang' is required for an ILI lookup")
            synsets = self.synsets_from_ili(ili, lang)
        elif wordkey:
            synsets = [self.synset(wordkey)]
        elif woi:
            form = CommonHelper.sanatizeWord(lemma or woi)
            languages = [lang] if lang else self.languages
            synsets = self._lemma_synsets(form, languages, pos)
            if not synsets and lemma:
                synsets = self._lemma_synsets(CommonHelper.sanatizeWord(woi), languages, pos)
        else:
            raise ValueError("'woi', 'wordkey' or 'ili' is required")

        if category in RELATIONS:
            synsets = [related for synset in synsets for related in self.relations(synset, category)]
        return self.serialize(synsets)

    def serialize(self, synsets):
        results = []
        for synset in synsets:
            lemmas = synset.lemmas()
            examples = synset.examples()
            identifier = synset.id
            descriptions = {
                lang: ','.join(forms) if lang != synset.lang else ''
                for lang, forms in synset.descriptions().items()
            }
            # The UI indexes every selected language, including lexical gaps.
            for lang in self.languages:
                descriptions.setdefault(lang, '')
            results.append(SimpleNamespace(
                name=lemmas[0], pos=POS_NAMES[synset.pos],
                offset=next((part for part in identifier.split('.')[1:] if part.isdigit()), ''),
                wordKey=identifier, ili=synset.ili or '', lang=synset.lang,
                wordnetId='own',  # Historical HTTP field; the backend is OMW.
                definition=synset.definition() or '',
                example=examples[0] if examples else '', synonyms=lemmas[1:],
                linguisticCounter=asdict(synset.relation_counts()),
                languageDescriptions={
                    name: descriptions.get(lang, '') for lang, name in (
                        ('en', 'english'), ('de', 'german'), ('fr', 'french'),
                        ('es', 'spanish'), ('it', 'italian'), ('nl', 'dutch'),
                        ('pt', 'portuguese'),
                    )
                },
                genericLanguageDescriptions={'descriptionLookup': descriptions},
            ))
        return CommonHelper.getLodViews(results)
