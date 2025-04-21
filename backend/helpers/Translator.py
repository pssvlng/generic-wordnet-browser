from nltk.corpus import wordnet as wn
from .Constants import VALID_WORDNET_LANGS

class Translator:

    def __init__(self, lang):
        self.lang = lang

    def translatePos(self, woi, posToken):
        if self.lang not in VALID_WORDNET_LANGS:
            return []
        woi = wn.synsets(woi, lang=self.lang, pos=posToken)
        return woi

    def translate(self, woi):
        if self.lang not in VALID_WORDNET_LANGS:
            return []
        woi = wn.synsets(woi, lang=self.lang)
        return woi

    def translate2(self, woi, lang):
        if lang not in VALID_WORDNET_LANGS:
            return []
        woi = wn.synsets(woi, lang=lang)
        return woi