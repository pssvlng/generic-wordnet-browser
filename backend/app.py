import os
import tempfile
import uuid
from gtts import gTTS
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics import DistanceMetric

from flask import Flask, Response, request, send_file
from flask_cors import cross_origin

from passivlingo_dictionary.Dictionary import Dictionary
from passivlingo_dictionary.models.SearchParam import SearchParam
from config import getWordNetEmbeddings
from encoders.WordEncoder import WordEncoder
from helpers.CommonHelper import CommonHelper
from helpers.Constants import AUDIO_LANG_MAP, POS_MAPPINGS
from imageCreation.CombinedImageWrapper import main
import wn

app = Flask(__name__)

# Load model and data
MODEL = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
DF = pd.read_csv('wordnet_txt_embeddings_input.csv', sep='\t', header=0, index_col=None)
EMBEDDING_ARR = getWordNetEmbeddings()

def error_response(message: str, status: int = 400) -> Response:
    return Response(response=f'{{"error": "{message}"}}', status=status, mimetype="application/json")

# Dictionary endpoints
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
        dict_obj = Dictionary()
        param = SearchParam()
        param.wordkey = wordkey
        param.category = category
        param.lang = lang
        param.woi = woi
        param.lemma = lemma
        param.pos = pos
        param.filterLang = filterLang        
        param.ili = ili
        results = dict_obj.findWords(param)
        results = CommonHelper.getLodViews(results)
        return Response(WordEncoder().encode(results), mimetype='application/json')
    except ValueError as err:
        return error_response(str(err), status=404)

@app.route('/api/dict/examples/', methods=['GET'])
@cross_origin()
def examples():
    wordkey = request.args.get('wordkey')
    if not wordkey:
        return error_response("Invalid argument list: 'wordkey' is required", status=404)

    dict_obj = Dictionary()
    results = dict_obj.getExampleSentences(wordkey)
    return Response(WordEncoder().encode(results), mimetype='application/json')

@app.route('/api/dict/related/', methods=['GET'])
@cross_origin()
def get_related():
    def get_exclusions(ili: str) -> list:
        exclusions = [ili]
        dict_obj = Dictionary()
        param = SearchParam()    
        param.lang = lang
        param.filterLang = filterLang
        param.wordkey = wordkey
        exclusions.append(ili)
        for category in ['hypernym', 'hyponym', 'holonym', 'meronym', 'entailment', 'antonym']:
            param.category = category
            sub_results = dict_obj.findWords(param)
            exclusions.extend([r.ili for r in sub_results])
        return exclusions

    wordkey = request.args.get('wordkey')
    ili = request.args.get('ili')
    lang = request.args.get('lang')
    filterLang = request.args['filterlang']
    
    if None in [ili, lang]:
        return error_response("Invalid argument list: 'ili' and 'lang' are required", status=404)

    try:
        synset = wn.synsets(ili=ili, lang='en')[0]
        query_txt = f'{", ".join(synset.lemmas())} (Part of Speech = {POS_MAPPINGS[synset.pos]}): {synset.definition()}'
        if synset.pos in ["n", "v"]:
            query_txt = f'{", ".join(synset.lemmas())} (Part of Speech = {POS_MAPPINGS[synset.pos]}, Category = {synset.metadata()["subject"].split(".")[1]}): {synset.definition()}'

        query_embedding = MODEL.encode(query_txt)
        dist = DistanceMetric.get_metric('euclidean')
        dist_arr = dist.pairwise(EMBEDDING_ARR, query_embedding.reshape(1, -1)).flatten()
        idist_arr_sorted = np.argsort(dist_arr)

        exclusions = get_exclusions(ili)
        final_results = []
        dict_obj = Dictionary()
        param = SearchParam()
        param.lang = lang  
        param.filterLang = filterLang        
        for val in DF['ili'].iloc[idist_arr_sorted[:10 + len(exclusions)]].values:
            if val not in exclusions:
                param.ili = val
                words = dict_obj.findWords(param)
                if len(words) != 0:                        
                    final_result = CommonHelper.getLodViews([words[0]])
                    final_results.extend(final_result)
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