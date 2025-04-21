class ContextWordWrapper():           
    def __init__(self):
        super().__init__()          
        self.contextWords = []      
        self.text = ''
        self.is_rdf = False
        self.rdfNonLiterals = []
        self.rdfLiterals = []
