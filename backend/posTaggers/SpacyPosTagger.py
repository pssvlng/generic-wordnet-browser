import spacy
from .PosTagger import PosTagger
from helpers.CommonHelper import CommonHelper
import spacy_dbpedia_spotlight

class SpacyPosTagger(PosTagger):    
    def __init__(self, spacyModel):        
        self.nlp = spacyModel        

    def tagText(self, textToTag):                  
        result = []
        dbpedia_entities = []
        if not textToTag:
            return (result, dbpedia_entities)    
        try: 
            words = self.nlp(textToTag)                                            
            if "dbpedia_spotlight" in self.nlp.pipe_names:
                for word in [ent for ent in words.ents if ent.label_ == 'DBPEDIA_ENT']:                        
                    dbpedia_entities.append((word.text, "NOUN", word.lemma_, "", word._.dbpedia_raw_result['@URI']))
            
            for word in words:                        
                result.append((word.text, word.pos_, word.lemma_, word.whitespace_, ""))
            
        except:
            print(f'Spacy Tagger failed on following text: {textToTag}')        
        
        return (result, dbpedia_entities)


