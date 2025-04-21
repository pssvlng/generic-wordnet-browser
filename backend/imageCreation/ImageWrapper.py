import os
import wn
from passivlingo_dictionary.encoders.WordEncoder import WordEncoder
from passivlingo_dictionary.wrappers.OwnSynsetWrapper import OwnSynsetWrapper

from helpers.Constants import ABBREVIATIONS

def getArgvTransform(argv):
    if len(argv) < 3:
        raise ValueError('Program expects at least 3 arguments')

    argvTransform = {
        'fileName': None,
        'level': None,
        'filterLangs': None,
        'maxLeafNodes': None,
        'ili': None,
        'synonymCount': None,
        'woi': None,
        'synsetId': None,        
        'hierarchy': False,
        'partWhole': False
    }

    for item in argv:        
        argvTransform[item] = argv[item]

    return argvTransform


def getFontName(filterLangs):
    langs = filterLangs.split(',')

    if len(set(['zh', 'jp']) & set(langs)) > 0:
        return 'SimSun'

    if len(set(['arb', 'fas', 'fa', 'he']) & set(langs)) > 0:
        return '"DejaVu Sans"'

    if 'th' in langs:
        return '"Angsana New"'

    return 'Arial'


def writeOutput(template, root, body, font_name, dotFilePath, pngFilePath, result, body1=None, rankdir=None):
    fileText = template.replace('{font_name0}', font_name)
    fileText = fileText.replace('{root0}', root)
    fileText = fileText.replace('{body}', body)
    if not body1 is None:
        fileText = fileText.replace('{body1}', body1)
    if not rankdir is None:
        fileText = fileText.replace('{rankdir}', rankdir)

    with open(dotFilePath, 'w', encoding='utf-8') as file:
        file.write(fileText)

    os.system(f'dot -Tpng {dotFilePath} -o {pngFilePath}')
    print(WordEncoder().encode(result))


def __formatSynonymDisplay(synset, woi, synonym_count):
    lemmas = synset.lemmas()
    result = ''    

    if synset.id != '*INFERRED*':
        result = woi if woi in lemmas else lemmas[0]        
        lemmas.remove(result)

        for synonym in lemmas[:synonym_count - 1]:
            result += f',{synonym}'
    
    if synset.lang in ABBREVIATIONS:
        return f'{result} [{ABBREVIATIONS[synset.lang][synset.pos]}]'
    
    return f'{result} [{ABBREVIATIONS["en"][synset.pos]}]'

def formatNodeDisplay(synset, woi, filter_langs, ili, synonym_count):
    result = {}
    if filter_langs and ili:
        langs = filter_langs.split(',')
        if 'en' in langs:
            langs.remove('en')
            langs.insert(0, 'en')
        for lang in langs:
            synsets_local = wn.synsets(ili=ili, lang=lang)
            if len(synsets_local) > 0:
                s = OwnSynsetWrapper(lang, synsets_local[0])
                result[lang] = __formatSynonymDisplay(s, woi, synonym_count)
    else:
        result[synset.id] = __formatSynonymDisplay(synset, woi, synonym_count)

    if len(result) == 0:
        s = OwnSynsetWrapper('en', wn.synsets(ili=ili, lang='en')[0])
        result['en'] = __formatSynonymDisplay(s, woi, synonym_count)

    return f"{' | '.join(result.values())}"
