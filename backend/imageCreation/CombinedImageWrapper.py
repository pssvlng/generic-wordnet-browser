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
from .HierarchyImageWrapper import buildgraph_body as hierarchy_build
from .PartWholeImageWrapper import buildgraph_body as partWhole_build


def main(argv):
    try:

        argvTransform = getArgvTransform(argv)

        dotFilePath = os.path.sep.join(
            [tempfile.gettempdir(), f"{argvTransform['fileName']}.dot"])
        pngFilePath = os.path.sep.join(
            [tempfile.gettempdir(), f"{argvTransform['fileName']}.png"])
        data = {"result": True, "filePath": pngFilePath, "msg": "Success"}

        if Path(pngFilePath).is_file():
            return data            

        level = int(argvTransform['level'])
        branch_count = int(argvTransform['maxLeafNodes'])
        filter_langs = argvTransform['filterLangs']        
        synonym_count = int(argvTransform['synonymCount'])
        is_hierarchy = bool(argvTransform['hierarchy'])
        is_partWhole = bool(argvTransform['partWhole'])
        woi = argvTransform['woi']
        rankdir = 'BT'
        body = ''
        body1 = ''

        synsets = []        
        for synset_id in argvTransform['synsetId'].split(','):
            loc_synset = wn.synset(synset_id)
            synsets.append(OwnSynsetWrapper(loc_synset.lexicon().language, loc_synset))

        if is_hierarchy:
            body = build_body(synsets, woi, level, filter_langs,
                              synonym_count, branch_count, 'is a', hierarchy_build)
        else:
            rankdir = 'RL'

        if is_partWhole:
            body1 = build_body(synsets, woi, level, filter_langs,
                                synonym_count, branch_count, 'has a', partWhole_build)

        combined_template = '''strict digraph g {
            compound=true;
            rankdir={rankdir};                    
            {root0}
            node [fontname={font_name0} shape = plaintext,height=.1];
            edge [style=dotted]
            {body}             
            node [fontname={font_name0} shape = box,height=.1];
            edge [style=solid]
            {body1}                           
        }'''

        font_name = getFontName(filter_langs)
        root = ''
        for synset in synsets:
            root = f'{root}"{formatNodeDisplay(synset, woi, filter_langs, synset.ili, synonym_count)}" [fontname={font_name} shape=box, style=bold];'
        writeOutput(combined_template, root, body, font_name,
                    dotFilePath, pngFilePath, data, body1=body1, rankdir=rankdir)

        return data
    
    except Exception as e:
        repr_ = getattr(e, 'message', repr(e))
        str_ = getattr(e, 'message', str(e))
        data = {"result": False, "filePath": pngFilePath,
                "msg": f'repr: {repr_}, str: {str_}'}
        return data


def build_body(synsets, woi, level, filter_langs, synonym_count, branch_count, edge_label, func):
    result = ''
    for synset in synsets:
        result = f'{result} {func(synset, woi, level, filter_langs, synset.ili, synonym_count, branch_count, True, edge_label)}{func(synset, woi, level, filter_langs, synset.ili, synonym_count, branch_count, False, edge_label)}'

    return result


if __name__ == "__main__":
    main(sys.argv[1:])
