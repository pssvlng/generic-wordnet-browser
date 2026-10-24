import os
import tempfile
import json
from gtts import gTTS
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics import DistanceMetric

from flask import Flask, Response, request, send_file
from flask_cors import cross_origin

import passivlingo_dictionary as pld
from config import getWordNetEmbeddings
from encoders.WordEncoder import WordEncoder
from helpers.Constants import AUDIO_LANG_MAP, POS_MAPPINGS
from imageCreation.CombinedImageWrapper import main
from wordnet_service import RELATIONS, WordnetService
from lemmatizer_cache import LEMMATIZERS
from resource_routes import init_resources
import wn

app = Flask(__name__)
init_resources(app)

# Load model and data
MODEL = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
DF = pd.read_csv('wordnet_txt_embeddings_input.csv', sep='\t', header=0, index_col=None)
EMBEDDING_ARR = getWordNetEmbeddings()

# Load each configured language model once per worker, before serving searches.
LEMMATIZERS.warm(app.config['WORDNET_LANGUAGES'])

def error_response(message: str, status: int = 400) -> Response:
    return Response(response=json.dumps({'error': message}), status=status, mimetype="application/json")

# Dictionary endpoints
@app.route('/api/dict/lookup/<kind>/<path:value>', methods=['GET'])
@cross_origin()
def lookup(kind, value):
    try:
        allowed = app.config['WORDNET_LANGUAGES']
        languages = request.args.get('filterlang', ','.join(allowed)).split(',')
        if not languages or any(lang not in allowed for lang in languages):
            raise ValueError('Unsupported language; configured languages: ' + ', '.join(allowed))
        service = WordnetService(languages)
        results = service.lookup(kind, value, request.args.get('lang'), request.args.get('relation'))
        return Response(WordEncoder().encode(results), mimetype='application/json')
    except (ValueError, pld.Error, wn.Error) as err:
        return error_response(str(err), status=400)


@app.route('/api/dict/words/', methods=['GET'])
@cross_origin()
def words():
    
    wordkey = request.args['wordkey'] if 'wordkey' in request.args and request.args['wordkey'] else None
    category = request.args['category'] if 'category' in request.args and request.args['category'] else None
    lang = request.args['lang'] if 'lang' in request.args and request.args['lang'] else None
    woi = request.args['woi'] if 'woi' in request.args and request.args['woi'] else None
    lemma = request.args['lemma'] if 'lemma' in request.args and request.args['lemma'] else None
    pos = request.args['pos'] if 'pos' in request.args and request.args['pos'] else None
    filterLang = request.args['filterlang'] if 'filterlang' in request.args and request.args['filterlang'] else None
    ili = request.args['ili'] if 'ili' in request.args and request.args['ili'] else None
    
    if len(request.args) > 8:
        return error_response(
            'Invalid argument list, possible combinations: (ili, lang), (woi), (wordkey, lang, category), (woi, lang, category), (woi, lang, pos, lemma)',
            status=404
        )

    try:
        results = WordnetService(filterLang).search(
            wordkey=wordkey, category=category, lang=lang, woi=woi,
            lemma=lemma, pos=pos, ili=ili,
        )
        return Response(WordEncoder().encode(results), mimetype='application/json')
    except (ValueError, pld.Error, wn.Error) as err:
        return error_response(str(err), status=404)

@app.route('/api/dict/examples/', methods=['GET'])
@cross_origin()
def examples():
    wordkey = request.args.get('wordkey')
    if not wordkey:
        return error_response("Invalid argument list: 'wordkey' is required", status=404)

    try:
        results = WordnetService().synset(wordkey).examples()
        return Response(WordEncoder().encode(results), mimetype='application/json')
    except (ValueError, pld.Error, wn.Error) as err:
        return error_response(str(err), status=404)

@app.route('/api/dict/related/', methods=['GET'])
@cross_origin()
def get_related():
    wordkey = request.args.get('wordkey')
    ili = request.args.get('ili')
    lang = request.args.get('lang')
    filterLang = request.args.get('filterlang')
    
    if None in [ili, lang]:
        return error_response("Invalid argument list: 'ili' and 'lang' are required", status=404)

    try:
        service = WordnetService(filterLang)
        synset = wn.synsets(ili=ili, lang='en')[0]
        query_txt = f'{", ".join(synset.lemmas())} (Part of Speech = {POS_MAPPINGS[synset.pos]}): {synset.definition()}'
        if synset.pos in ["n", "v"]:
            query_txt = f'{", ".join(synset.lemmas())} (Part of Speech = {POS_MAPPINGS[synset.pos]}, Category = {synset.metadata()["subject"].split(".")[1]}): {synset.definition()}'

        query_embedding = MODEL.encode(query_txt)
        dist = DistanceMetric.get_metric('euclidean')
        dist_arr = dist.pairwise(EMBEDDING_ARR, query_embedding.reshape(1, -1)).flatten()
        idist_arr_sorted = np.argsort(dist_arr)

        source_synsets = [service.synset(wordkey)] if wordkey else service.synsets_from_ili(ili, lang)
        exclusions = {ili}
        for source in source_synsets:
            for category in RELATIONS:
                exclusions.update(related.ili for related in service.relations(source, category))
        final_results = []
        for val in DF['ili'].iloc[idist_arr_sorted[:10 + len(exclusions)]].values:
            if val not in exclusions:
                synsets = service.synsets_from_ili(val, lang)
                if synsets:
                    final_results.extend(service.serialize(synsets[:1]))
                if len(final_results) == 10:
                    break

        return Response(WordEncoder().encode(final_results), mimetype='application/json')
    except Exception as e:
        return error_response(str(e), status=500)

@app.route('/api/dict/image/', methods=['GET'])
@cross_origin()
def get_image():
    try:
        result = main(request.args)
        file_path = result["filePath"]
        return send_file(file_path, mimetype='image/png')
    except Exception as e:
        return error_response(str(e), status=500)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/api/dict/tts/', methods=['GET'])
@cross_origin()
def text_to_speech():
    text = request.args.get('text', '')
    lang = request.args.get('lang', 'en')

    if not text:
        return error_response("Text is required", status=400)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            filename = temp_file.name

        if lang in AUDIO_LANG_MAP:
            lang = AUDIO_LANG_MAP[lang]

        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        return send_file(filename, mimetype='audio/mpeg', as_attachment=True, download_name='audio.mp3')
    except Exception as e:
        return error_response(str(e), status=500)
    finally:
        if os.path.exists(filename):
            os.remove(filename)
