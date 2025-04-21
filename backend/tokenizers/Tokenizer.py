from abc import abstractmethod, ABCMeta
from urllib.parse import unquote
from wordSenseProviders.DefaultWordSenseProvider import DefaultWordSenseProvider
from wordSenseProviders.EnglishWordSenseProvider import EnglishWordSenseProvider

class Tokenizer:

    __metaclass__ = ABCMeta                    

    @abstractmethod
    def tokenize(self, lang, text): pass
    