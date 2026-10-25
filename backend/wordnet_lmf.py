"""WN-LMF 1.4 lookup subsets, with native identities and source metadata.

Like en-word.net's /xml lookups, relation targets can be outside the returned
subset. This is not a self-contained whole-lexicon installation file.
The selective wn._export helpers and frame queries below target the pinned
wn 0.9.4 schema; they never load/export an entire lexicon to answer a lookup.
"""

import hashlib
from collections import defaultdict
from xml.etree import ElementTree as ET

from wn import _export
from wn._db import connect

from wordnet_service import WordnetService


DC = 'https://globalwordnet.github.io/schemas/dc/'
DOCTYPE = '<!DOCTYPE LexicalResource SYSTEM "https://globalwordnet.github.io/schemas/WN-LMF-1.4.dtd">'
DC_FIELDS = frozenset('contributor coverage creator date description format identifier '
                      'publisher relation rights source subject title type'.split())


def _metadata(metadata):
    attributes = {}
    for key, value in (metadata or {}).items():
        if value is not None and value != '':
            if key in DC_FIELDS:
                attributes['dc:' + key] = str(value)
            elif key in ('status', 'note', 'confidenceScore'):
                attributes[key] = str(value)
    return attributes


def _text(parent, tag, records):
    for record in records:
        attributes = _metadata(record.get('meta'))
        for name in ('language', 'sourceSense'):
            if record.get(name):
                attributes[name] = record[name]
        ET.SubElement(parent, tag, attributes).text = record['text']


def _relations(parent, tag, records):
    for record in sorted(records, key=lambda record: (record['relType'], record['target'])):
        ET.SubElement(parent, tag, {
            'relType': record['relType'], 'target': record['target'],
            **_metadata(record.get('meta')),
        })


def _form(parent, tag, form, pos):
    attributes = {'writtenForm': str(form)}
    if tag == 'Lemma':
        attributes['partOfSpeech'] = pos
    elif form.id:
        attributes['id'] = form.id
    if form.script:
        attributes['script'] = form.script
    element = ET.SubElement(parent, tag, attributes)
    for pronunciation in form.pronunciations():
        attrs = {key: getattr(pronunciation, key) for key in ('variety', 'notation', 'audio')
                 if getattr(pronunciation, key)}
        if not pronunciation.phonemic:
            attrs['phonemic'] = 'false'
        ET.SubElement(element, 'Pronunciation', attrs).text = pronunciation.value
    for form_tag in form.tags():
        ET.SubElement(element, 'Tag', {'category': form_tag.category}).text = form_tag.tag


def _frames(lexicon):
    # Scope IDs to the source lexicon so multilingual frame names cannot collide.
    rows = connect().execute('''
        SELECT rowid, id, frame FROM syntactic_behaviours
         WHERE lexicon_rowid = ? ORDER BY id, frame
    ''', (lexicon._id,))
    return {rowid: {
        'id': f'{lexicon.id}-frame-' + (identifier or hashlib.sha256(label.encode('utf-8')).hexdigest()),
        'subcategorizationFrame': label,
    } for rowid, identifier, label in rows}


def _sense(parent, sense, rank, lexids, frames):
    attributes = {'id': sense.id, 'synset': sense.synset().id, 'n': str(rank),
                  **_metadata(sense.metadata())}
    if not sense.lexicalized():
        attributes['lexicalized'] = 'false'
    if sense.adjposition():
        attributes['adjposition'] = sense.adjposition()
    rows = connect().execute('''
        SELECT syntactic_behaviour_rowid FROM syntactic_behaviour_senses
         WHERE sense_rowid = ?
    ''', (sense._id,))
    subcat = sorted({frames[rowid]['id'] for rowid, in rows if rowid in frames})
    if subcat:
        attributes['subcat'] = ' '.join(subcat)
    element = ET.SubElement(parent, 'Sense', attributes)
    _relations(element, 'SenseRelation', _export._export_sense_relations(sense._id, lexids))
    _text(element, 'Example', _export._export_examples(sense._id, 'senses', lexids))
    for count in _export._export_counts(sense._id, lexids):
        ET.SubElement(element, 'Count', _metadata(count.get('meta'))).text = str(count['value'])


def _synset(parent, synset, lexids):
    ili_definition = _export._export_ili_definition(synset._id)
    ili = getattr(synset.ili, 'id', None) or ('in' if ili_definition else '')
    attributes = {'id': synset.id, 'ili': ili, 'partOfSpeech': synset.pos,
                  **_metadata(synset.metadata())}
    members = [word.id for word in synset.words()]
    if members:
        attributes['members'] = ' '.join(members)
    lexfile = synset.lexfile() or synset.metadata().get('subject')
    if lexfile:
        attributes['lexfile'] = lexfile
    if not synset.lexicalized():
        attributes['lexicalized'] = 'false'
    element = ET.SubElement(parent, 'Synset', attributes)
    _text(element, 'Definition', _export._export_definitions(synset._id, lexids))
    if ili_definition and ili == 'in':
        _text(element, 'ILIDefinition', [ili_definition])
    _relations(element, 'SynsetRelation', _export._export_synset_relations(synset._id, lexids))
    _text(element, 'Example', _export._export_examples(synset._id, 'synsets', lexids))


def export_lmf(synsets):
    root = ET.Element('LexicalResource', {'xmlns:dc': DC})
    grouped = defaultdict(dict)
    for synset in synsets:
        raw = WordnetService.raw_synset(synset.id)
        lexicon = raw.lexicon()
        grouped[(lexicon.id, lexicon.version)][raw.id] = raw

    for key in sorted(grouped):
        selected = grouped[key]
        lexicon = next(iter(selected.values())).lexicon()
        lexids = (lexicon._id,)
        attributes = {name: getattr(lexicon, name) or '' for name in
                      ('id', 'label', 'language', 'email', 'license', 'version')}
        for name in ('url', 'citation', 'logo'):
            if getattr(lexicon, name):
                attributes[name] = getattr(lexicon, name)
        attributes.update(_metadata(lexicon.metadata()))
        element = ET.SubElement(root, 'Lexicon', attributes)
        for dependency in _export._export_requires(lexicon._id):
            attributes = {'ref': dependency['id'], 'version': dependency['version']}
            if dependency.get('url'):
                attributes['url'] = dependency['url']
            ET.SubElement(element, 'Requires', attributes)
        frames = _frames(lexicon)
        # An entry can belong to several returned synsets. Emit it once, with
        # only the selected senses, retaining their source order and rank.
        words = {word.id: word for raw in selected.values() for word in raw.words()}
        for identifier, word in sorted(words.items()):
            entry = ET.SubElement(element, 'LexicalEntry', {'id': identifier, **_metadata(word.metadata())})
            for index, form in enumerate(word.forms()):
                _form(entry, 'Form' if index else 'Lemma', form, word.pos)
            for rank, sense in enumerate(word.senses(), start=1):
                if sense.synset().id in selected:
                    _sense(entry, sense, rank, lexids, frames)
        for identifier in sorted(selected):
            _synset(element, selected[identifier], lexids)
        # Duplicated old-style frame declarations can share a label/identity.
        unique_frames = {frame['id']: frame for frame in frames.values()}
        for identifier in sorted(unique_frames):
            ET.SubElement(element, 'SyntacticBehaviour', unique_frames[identifier])

    ET.indent(root, space='  ')
    return (b'<?xml version="1.0" encoding="UTF-8"?>\n' + DOCTYPE.encode('ascii') + b'\n'
            + ET.tostring(root, encoding='utf-8') + b'\n')
