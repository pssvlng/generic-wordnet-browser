"""A lookup document and its equivalent OntoLex/WordNet RDF graph."""

from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from wordnet_service import WordnetService


ONTOLEX = Namespace('http://www.w3.org/ns/lemon/ontolex#')
LIME = Namespace('http://www.w3.org/ns/lemon/lime#')
WN = Namespace('https://globalwordnet.github.io/schemas/wn#')
ILI = Namespace('http://ili.globalwordnet.org/ili/')
POS = dict(n='noun', v='verb', a='adjective', s='adjective_satellite',
           r='adverb', t='named_entity', c='conjunction', p='adposition',
           x='other_pos', u='unknown_pos')


def resource_uri(base, language, kind, value):
    return f'{base}/{quote(language, safe="")}/{kind}/{quote(value, safe="")}'


def export_document(synsets, *, base, kind, value, languages, relation=None):
    """Use native lexical ids and source metadata, without inventing licences.

    pld resolves queries; wn supplies the lexical-entry/sense identifiers and
    stored relations which pld's public API does not expose in full.
    """
    records = []
    for synset in synsets:
        raw = WordnetService.raw_synset(synset.id)
        lexicon = raw.lexicon()
        language = lexicon.language
        uri = resource_uri(base, language, 'synset', raw.id)

        def synset_ref(target):
            lang = target.lexicon().language
            return {'id': target.id, 'language': lang,
                    'uri': resource_uri(base, lang, 'synset', target.id)}

        def sense_ref(sense):
            parent = synset_ref(sense.synset())
            return {'id': sense.id, 'uri': parent['uri'] + '#sense-' + quote(sense.id, safe='')}

        entries = []
        for word in sorted(raw.words(), key=lambda word: word.id):
            entry_uri = resource_uri(base, language, 'lemma', word.lemma()) + '#entry-' + quote(word.id, safe='')
            senses = []
            for sense in sorted(word.senses(), key=lambda sense: sense.id):
                if sense.synset().id != raw.id:
                    continue
                senses.append({
                    **sense_ref(sense), 'examples': sense.examples(),
                    'relations': {name: sorted((sense_ref(target) for target in targets), key=lambda ref: ref['uri'])
                                  for name, targets in sorted(sense.relations().items())},
                })
            entries.append({'id': word.id, 'uri': entry_uri, 'lemma': word.lemma(), 'senses': senses})

        records.append({
            'id': raw.id, 'wordKey': synset.id, 'uri': uri, 'language': language,
            'ili': synset.ili, 'partOfSpeech': synset.pos, 'lemmas': synset.lemmas(),
            'definition': synset.definition(), 'examples': synset.examples(),
            'lexicon': {
                'id': lexicon.id, 'version': lexicon.version, 'language': language,
                'label': lexicon.label, 'license': lexicon.license, 'url': lexicon.url,
                'uri': f'{base}/#lexicon-{quote(lexicon.id + ":" + lexicon.version, safe="")}',
            },
            'entries': entries,
            'relations': {name: sorted((synset_ref(target) for target in targets), key=lambda ref: ref['uri'])
                          for name, targets in sorted(raw.relations().items())},
        })
    return {
        'schemaVersion': 1,
        'query': {'type': kind, 'value': value, 'languages': languages, 'relation': relation},
        'count': len(records), 'synsets': sorted(records, key=lambda item: item['uri']),
    }


def export_graph(document):
    graph = Graph()
    for prefix, namespace in [('ontolex', ONTOLEX), ('lime', LIME), ('wn', WN),
                              ('ili', ILI), ('dct', DCTERMS), ('owl', OWL)]:
        graph.bind(prefix, namespace)

    def text_node(subject, predicate, text, language, suffix, node_type):
        node = URIRef(str(subject) + ('-' if '#' in str(subject) else '#') + suffix)
        graph.add((subject, predicate, node))
        graph.add((node, RDF.type, node_type))
        graph.add((node, RDF.value, Literal(text, lang=language)))

    for item in document['synsets']:
        subject = URIRef(item['uri'])
        # These application aliases are not BCP-47 language tags.
        language = {'ua': 'uk', 'jp': 'ja'}.get(item['language'], item['language'])
        lexicon = item['lexicon']
        lexicon_uri = URIRef(lexicon['uri'])
        pos = WN[POS[item['partOfSpeech']]]
        graph.add((subject, RDF.type, ONTOLEX.LexicalConcept))
        graph.add((subject, DCTERMS.identifier, Literal(item['id'])))
        graph.add((subject, DCTERMS.source, lexicon_uri))
        graph.add((subject, WN.partOfSpeech, pos))
        graph.add((lexicon_uri, RDF.type, LIME.Lexicon))
        graph.add((lexicon_uri, LIME.language, Literal(language)))
        graph.add((lexicon_uri, OWL.versionInfo, Literal(lexicon['version'])))
        graph.add((lexicon_uri, RDFS.label, Literal(lexicon['label'])))
        if lexicon['license']:
            license = lexicon['license']
            graph.add((lexicon_uri, DCTERMS.license,
                       URIRef(license) if license.startswith(('https://', 'http://')) else Literal(license)))
        if lexicon['url']:
            graph.add((lexicon_uri, RDFS.seeAlso, URIRef(lexicon['url'])))
        if item['ili']:
            graph.add((subject, WN.ili, ILI[item['ili']]))
        for lemma in item['lemmas']:
            graph.add((subject, RDFS.label, Literal(lemma, lang=language)))
        if item['definition']:
            text_node(subject, WN.definition, item['definition'], language, 'definition', WN.Definition)
        for index, example in enumerate(item['examples']):
            text_node(subject, WN.example, example, language, f'example-{index}', WN.Example)
        for relation, targets in item['relations'].items():
            for target in targets:
                graph.add((subject, WN[relation], URIRef(target['uri'])))
        for entry in item['entries']:
            entry_uri = URIRef(entry['uri'])
            form = URIRef(entry['uri'] + '-form')
            graph.add((lexicon_uri, LIME.entry, entry_uri))
            graph.add((entry_uri, RDF.type, ONTOLEX.LexicalEntry))
            graph.add((entry_uri, ONTOLEX.canonicalForm, form))
            graph.add((form, RDF.type, ONTOLEX.Form))
            graph.add((form, ONTOLEX.writtenRep, Literal(entry['lemma'], lang=language)))
            graph.add((entry_uri, WN.partOfSpeech, pos))
            graph.add((entry_uri, ONTOLEX.evokes, subject))
            for sense in entry['senses']:
                sense_uri = URIRef(sense['uri'])
                graph.add((entry_uri, ONTOLEX.sense, sense_uri))
                graph.add((sense_uri, RDF.type, ONTOLEX.LexicalSense))
                graph.add((sense_uri, ONTOLEX.isLexicalizedSenseOf, subject))
                graph.add((subject, ONTOLEX.lexicalizedSense, sense_uri))
                for relation, targets in sense['relations'].items():
                    for target in targets:
                        graph.add((sense_uri, WN[relation], URIRef(target['uri'])))
                for index, example in enumerate(sense['examples']):
                    text_node(sense_uri, WN.example, example, language, f'example-{index}', WN.Example)
    return graph
