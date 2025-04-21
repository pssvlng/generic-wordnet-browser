class LanguageDescriptions:
    def __init__(self):
        self.english = ''
        self.spanish = ''
        self.french = ''
        self.german = ''
        self.portuguese = ''
        self.italian = ''        
        self.dutch = ''
        self.farsi = ''
        self.japanese = ''
        self.polish = ''
        self.thai = ''

    def getWordDescription(self, lang):
        if lang == 'fra':
            return self.french
        if lang == 'spa':
            return self.spanish
        if lang == 'por':
            return self.portuguese             
        if lang == 'ita':
            return self.italian            
        if lang == 'eng':
            return self.english            
        if lang == 'ger':
            return self.german            
        if lang == 'nld':
            return self.dutch            
        if lang == 'fas':
            return self.farsi            
        if lang == 'jpn':
            return self.japanese            
        if lang == 'tha':
            return self.thai            
        if lang == 'pol':
            return self.polish            

        return ''    

    def setWordDescription(self, lang, woi):        
        if lang == 'fra':
            self.french = woi
            return
        if lang == 'spa':
            self.spanish = woi
            return
        if lang == 'por':
            self.portuguese = woi
            return    
        if lang == 'ita':
            self.italian = woi
            return
        if lang == 'eng':
            self.english = woi
            return            
        if lang == 'ger':
            self.german = woi
            return
        if lang == 'nld':
            self.dutch = woi
            return    
        if lang == 'fas':
            self.farsi = woi
            return    
        if lang == 'jpn':
            self.japanese = woi
            return    
        if lang == 'tha':
            self.thai = woi
            return    
        if lang == 'pol':
            self.polish = woi
            return                    

    def getWordDescriptions(self, separator):
        return separator.join([self.french, self.spanish, self.portuguese, self.italian, self.english, self.german, self.dutch, self.farsi, self.japanese, self.thai, self.polish])        


        