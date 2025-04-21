import os
import wn
import urllib.request
import zipfile
import nltk
import pandas as pd

# This is necessary to initialize the WordNet database inside the docker container
wn.download('ewn:2020')
wn.remove('ewn:2020')

EU_DOWNLOAD_URI = 'https://github.com/pssvlng/open-european-wordnets-{type}/raw/main/{lang}_{type}.zip'
EU_LANGS = ['en']
OMW_LANG = []
OTHER_URI = ['https://github.com/pssvlng/ua-wordnet/raw/refs/heads/master/uaWordNet.zip']

df = pd.DataFrame({'lang': EU_LANGS})
df['download_status'] = False
get_download_uri = lambda uri, placeholder, new_value: uri.replace(placeholder, new_value)

for lang in EU_LANGS:
    for type in ['hybrid', 'inferred']:
        download_uri = get_download_uri(EU_DOWNLOAD_URI, '{lang}', lang)
        download_uri = get_download_uri(download_uri, '{type}', type)
        try:
            urllib.request.urlretrieve(download_uri, f'{lang}_{type}.zip')
            with zipfile.ZipFile(f'{lang}_{type}.zip', 'r') as zip_ref:
                zip_ref.extractall('')
                wn.add(f'{lang}_{type}.xml')
            df.loc[df['lang'] == lang, 'download_status'] = True
            break
        except Exception as e:
            print(f"Failed to download {lang}_{type}.zip: {e}")            
        finally:            
            if os.path.exists(f'{lang}_{type}.zip'):
                os.remove(f'{lang}_{type}.zip')
            if os.path.exists(f'{lang}_{type}.xml'):
                os.remove(f'{lang}_{type}.xml')

for uri in OTHER_URI:
    try:
        file_name = uri.split('/')[-1]
        urllib.request.urlretrieve(uri, file_name)
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall('')
            wn.add(file_name.replace('.zip', '.xml'))
    except Exception as e:
        print(f"Failed to download {file_name} from {uri}: {e}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        if os.path.exists(file_name.replace('.zip', '.xml')):
            os.remove(file_name.replace('.zip', '.xml'))

for index, row in df[df['download_status'] == False].iterrows():
    try:
        lang = row['lang']
        wn.download(f'omw-{lang}')
    except Exception as e:
        print(f"Failed to download omw-{lang}: {e}")

for lang in OMW_LANG:
    try:
        wn.download(f'omw-{lang}')
    except Exception as e:
        print(f"Failed to download omw-{lang}: {e}")        
    
nltk.download('stopwords')
nltk.download('wordnet')

