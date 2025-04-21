import nltk
from urllib.parse import unquote

import spacy
from helpers.CommonHelper import CommonHelper
from helpers.FactoryMethods import FactoryMethods

class SynsetClassifier:

    def __init__(self, text, spacyModel):        
        self.nlp = spacyModel

        self.text_vec = []
        tokens = self.nlp(text)
        for token in tokens:
            if token.pos_ in ['ADJ', 'ADV', 'NOUN', 'VERB']:
                self.text_vec.append(token)

    def classify(self, lemmas, hypernyms) -> float:
        DEFAULT_CLASSIFICATION_WEIGHT = 0.19        
        vec1 = self.text_vec;        
        vec2 = []
        items = lemmas + hypernyms
        for item in items:
            t = self.nlp(str(item))
            for token in t:
                if token.pos_ in ['ADJ', 'ADV', 'NOUN', 'VERB']:
                    vec2.append(token)

        cntr = 0
        sum = 0
        for tok1 in vec1:
            vn_tok1 = tok1.vector_norm
            for tok2 in vec2:
                if vn_tok1 and tok2.vector_norm:
                    similarity = tok1.similarity(tok2)
                    if similarity > 0:
                        sum += similarity
                        cntr += 1
        if cntr > 0:
            return sum/cntr

        return DEFAULT_CLASSIFICATION_WEIGHT

    def __repr__(self):
        return 'SynsetClassifier()'

    def __str__(self):
        return 'SynsetClassifier()'
