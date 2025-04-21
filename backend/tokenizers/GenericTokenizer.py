from .Tokenizer import Tokenizer
import nltk
from nltk.tokenize import word_tokenize
from helpers.Constants import DOMAIN_NAMES
from nltk.corpus import stopwords
from helpers.CommonHelper import CommonHelper
from models.ContextWord import ContextWord
from posTaggers.PosTagger import PosTagger

class GenericTokenizer(Tokenizer):

    def __init__(self, posTagger):             
        self.posTagger = posTagger        

    def __merge_lists(self, dbpedia_entities, words):
        last_index = 0
        for entry in dbpedia_entities:
            to_search = entry[0].split(' ')
            search_surface = [word[0] for word in words[last_index:]]
            for index, _ in enumerate(search_surface):
                if entry[0] == ' '.join(search_surface[index:index + len(to_search)]):                    
                    try:
                        last_index += index
                        whitespace = words[last_index + len(to_search) - 1][3]
                        words[last_index:last_index + len(to_search) - 1] = []
                        if last_index >= len(words):
                            words.append((entry[0], entry[1], entry[2], whitespace, entry[4]))
                        else:   
                            words[last_index] = (entry[0], entry[1], entry[2], whitespace, entry[4])                    
                        last_index += 1
                        break
                    except Exception as e:
                        print(f"Error while processing Named Entities in Generic Tokenizer: {e}")
                        
        return words            

    def tokenize(self, lang, text):     
        result = []                       
        tagResults = self.posTagger.tagText(text)        
        wordTags = tagResults[0]
        dbpedia_entities = tagResults[1]        
        stopWords = set(stopwords.words(CommonHelper.getWordnetLangDescription(lang)))                
        wordTags = self.__merge_lists(dbpedia_entities, wordTags)        

        for t in wordTags:            
            word = ContextWord()            
            word.name = t[0]
            word.whitespace = t[3]            
            word.dbPediaUrl = t[4]            
            word.lang = lang
            if len([x for x in ["'", "...", "…", "`", '"'] if x in t[0]]) <= 0 and t[1] in ['VERB', 'NOUN', 'ADV', 'ADJ'] and t[0].lower() not in stopWords:                
                word.pos = CommonHelper.getSpacyToWordnetPosMapping(t[1])                     
                word.lemma = t[2]

            result.append(word)        
        return result