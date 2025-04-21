from .BaseWord import BaseWord

class Word(BaseWord):           
    def __init__(self):
        super().__init__()                
        self.definition = ''
        self.example = ''        
        self.LinguisticCounter = None
        self.LanguageDescriptions = None
        self.synonyms = ''
        self.LodViews = {}        
            