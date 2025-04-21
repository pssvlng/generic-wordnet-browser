class RdfNonLiteral():           
    def __init__(self, predicate: str, object: str):
        super().__init__()          
        self.predicate = predicate
        self.object = object    

    def __eq__(self, other):
        if isinstance(other, RdfNonLiteral):
            return self.predicate == other.predicate and self.object == other.object
        return False

    def __hash__(self):
        return hash(f'{self.predicate}{self.object}')        