from .Word import Word

class WeightedWord(Word):           
    def __init__(self):
        super().__init__()        
        self.weight = 0.0