class RdfLiteral():           
    def __init__(self, predicate: str, text: str):
        super().__init__()          
        self.predicate = predicate
        self.contextWords = []      
        self.text = text
        self.lang = 'en'
        