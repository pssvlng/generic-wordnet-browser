
from urllib.parse import unquote
from nltk.corpus import wordnet as wn

from helpers.Constants import WIKTIONARY_LANG_MAP, WIKTIONARY_POS

class CommonHelper:    
            
    @classmethod
    def getCountryCode(cls, lang):
        choices = {'fra': 'fr', 'spa': 'es', 'ita': 'it', 'nld': 'nl', 'por' : 'pt', 'ger': 'de', 'eng': 'en', 'fas': 'fa', 'jpn': 'ja', 'pol': 'pl', 'tha': 'th'}
        return choices.get(lang, 'en')

    @classmethod
    def getWordnetLanguageCode(cls, lang):
        choices = {'fr': 'fra', 'es': 'spa', 'it': 'ita', 'nl': 'nld', 'pt' : 'por', 'de': 'ger', 'en': 'eng'}
        return choices.get(lang, 'eng')    

    @classmethod
    def getWordnetLangDescription(cls, lang):
        choices = {'fra': 'french', 'spa': 'spanish', 'ita': 'italian', 'nld': 'dutch', 'por' : 'portuguese', 'ger': 'german', 'eng': 'english'}
        return choices.get(lang, 'english')
    
    @classmethod
    def getSpacyModelName(cls, lang):
        choices = {'de': 'de_core_news_md'}
        return choices.get(lang, 'en_core_web_sm')

    @classmethod
    def getSpacyToWordnetPosMapping(cls, pos):
        choices = {'VERB': wn.VERB, 'NOUN': wn.NOUN,
                   'ADV': wn.ADV, 'ADJ': wn.ADJ}
        return choices.get(pos, 'x')

    @classmethod
    def getWordnetPosMapping(cls, pos):
        if pos.startswith('NN'):
            return wn.NOUN
        elif pos.startswith('VB'):
            return wn.VERB
        elif pos.startswith('JJ'):
            return wn.ADJ
        elif pos.startswith('RB'):
            return wn.ADV
        else:
            return 'x'

    @classmethod
    def sanatizeWord(cls, woi):
        result = unquote(woi)
        startsWithList = ["...", "'", '"', "n'", "l'", ",", ".", "!", "?", "¿", ";", "_", "-",
                          "`", "~", "<", ">", "%", "$", "#", "*", "(", ")", "+", "|", "@", "&", "^", "«", "»"]
        endsWithList = ["...", "'", '"', "'s", ",", ".", "!", "?", "¿", ";", "_", "-", "`",
                        "~", "<", ">", "%", "$", "#", "*", "(", ")", "+", "|", "@", "&", "^", "«", "»"]
        for s in startsWithList:
            if result.startswith(s):
                result = result[len(s):]
        for e in endsWithList:
            if result.endswith(e):
                result = result[:(len(e)*-1)]

        return result

    @classmethod
    def getLodViews(cls, results):
        for result in results:
            lodViews = {}
            if result.lang in ['en', 'de', 'fr', 'es', 'it', 'nl', 'pt', 'af', 'ro', 'ua']:
                lemmas = [result.name] + result.synonyms
                for lemma in lemmas:
                    uris = []
                    if result.lang == 'en':
                        uris.append(f"https://en.wiktionary.org/wiki/{lemma}#{WIKTIONARY_POS[result.lang][result.pos]}".replace(" ", "_"))
                    else:
                        lang = WIKTIONARY_LANG_MAP[result.lang] if result.lang in WIKTIONARY_LANG_MAP else result.lang
                        uris.append(f"https://{lang}.wiktionary.org/wiki/{lemma}".replace(" ", "_"))

                    if result.lang in ['en', 'fr', 'es', 'it', 'pt', 'nl', 'af', 'ro'] and result.pos[:1].lower() == 'v':
                        uris.append(f"https://cooljugator.com/{result.lang}/{lemma}")
                    if result.lang == 'de':
                        uris.append(f'https://www.verbformen.com/?w={lemma}')                                        
                                                                                
                    lodViews[lemma] = uris
            result.lodViews = lodViews

        return results