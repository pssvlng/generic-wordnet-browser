import os
import numpy as np
import urllib

# DEV Configurations
cors_dev_config = {
    "origins": ["http://localhost:4200"],  
}

# PROD Configurations
cors_prod_config = {
    "origins": ["https://127.0.0.1:80"],  
}

def getWordNetEmbeddings():
    file_name = 'embeddings.npy'
    if os.path.exists(file_name):
        return np.load(file_name)
    else:                
        uri = "https://www.dropbox.com/scl/fi/a9lbbzst9wqb0p0aaews4/embeddings.npy?rlkey=ocu6ql9k5zcxiguxu1yygekbj&st=y5mgsupd&dl=1"
        urllib.request.urlretrieve(uri, file_name)
        return np.load(file_name)
