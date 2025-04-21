from ast import List
import nltk
from urllib.parse import unquote
from helpers.FactoryMethods import FactoryMethods
from posTaggers.SpacyPosTagger import SpacyPosTagger
from tokenizers.GenericTokenizer import GenericTokenizer

class TextProcessor:    
                
    def tokenizeParagraph(self, paragraph: str):
        if paragraph is None:
            raise ValueError("Invalid argument list: 'paragraph' required")

        paragraph = unquote(paragraph)
        return nltk.sent_tokenize(paragraph)

    def tokenizeSentence(self, text: str, lang: str, spacyModel):
        if text == None:
            raise ValueError(
                "Invalid argument list: 'sent' required")

        sanatised_text = unquote(text)  
        tokenizer = GenericTokenizer(SpacyPosTagger(spacyModel))    

        return tokenizer.tokenize(lang, sanatised_text)

    def __repr__(self):
        return 'TextProcessor()'

    def __str__(self):
        return 'TextProcessor()'
