from lemmatizers.DefaultLemmatizer import DefaultLemmatizer

class FactoryMethods:        

    @classmethod
    def getLemmatizer(cls, lang):        
        return DefaultLemmatizer()    
