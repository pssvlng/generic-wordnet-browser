import wn
import sys
import os
import tempfile
from passivlingo_dictionary.encoders.WordEncoder import WordEncoder
from passivlingo_dictionary.wrappers.OwnSynsetWrapper import OwnSynsetWrapper
from pathlib import Path
from .ImageWrapper import getArgvTransform, getFontName
from .ImageWrapper import writeOutput
from .ImageWrapper import formatNodeDisplay


def main(argv):
    try:

        argvTransform = getArgvTransform(argv)

        dotFilePath = os.path.sep.join(
            [tempfile.gettempdir(), f"{argvTransform['fileName']}.dot"])
        pngFilePath = os.path.sep.join(
            [tempfile.gettempdir(), f"{argvTransform['fileName']}.png"])
        data = {"result": True, "filePath": pngFilePath, "msg": "Success"}

        if Path(pngFilePath).is_file():
            print(WordEncoder().encode(data))
            return

        loc_synset = wn.synset(argvTransform['synsetId'])        
        synset = OwnSynsetWrapper(loc_synset.lexicon().language, loc_synset)
        level = int(argvTransform['level'])
        branch_count = int(argvTransform['maxLeafNodes'])
        filter_langs = argvTransform['filterLangs']
        ili = argvTransform['ili']
        synonym_count = int(argvTransform['synonymCount'])
        woi = argvTransform['woi']

        body = f'{buildgraph_body(synset, woi, level, filter_langs, ili, synonym_count, branch_count, True)}{buildgraph_body(synset, woi, level, filter_langs, ili, synonym_count, branch_count, False)}'
        hierarchy_template = '''strict digraph g {
            rankdir=BT            
            "{root0}" [fontname={font_name0} shape=box, style=bold]
            node [fontname={font_name0} shape = plaintext,height=.1];
            edge [style=dotted]
            {body}
        }'''

        root = formatNodeDisplay(synset, woi, filter_langs, ili, synonym_count)
        font_name = getFontName(filter_langs)
        writeOutput(hierarchy_template, root, body,
                    font_name, dotFilePath, pngFilePath, data)

    except Exception as e:
        repr_ = getattr(e, 'message', repr(e))
        str_ = getattr(e, 'message', str(e))
        data = {"result": False, "filePath": pngFilePath,
                "msg": f'repr: {repr_}, str: {str_}'}
        print(WordEncoder().encode(data))


def buildgraph_body(synset, woi, level, filter_langs, ili, synonym_count, branch_count, build_up, edge_label=''):
    if level == 0:
        return ''

    if build_up:
        branches = synset.hypernyms()
    else:
        branches = synset.hyponyms()

    root = formatNodeDisplay(synset, woi, filter_langs, ili, synonym_count)
    entry = ''
    returnstr = ''
    for item in branches[:branch_count]:
        itemDisplay = formatNodeDisplay(
            item, woi, filter_langs, item.ili, synonym_count)
        if build_up:
            entry = f'{entry}"{root}"->"{itemDisplay}" [label="{edge_label}"];'
        else:
            entry = f'{entry}"{itemDisplay}"->"{root}" [label="{edge_label}"];'

        returnstr = f'{returnstr}{buildgraph_body(item, woi, level-1, filter_langs, item.ili, synonym_count, branch_count, build_up, edge_label)}'
    return f'{entry}{returnstr}'


if __name__ == "__main__":
    main(sys.argv[1:])


