# Generic WordNet Browser
A Generic Browser Application for lookup and browsing of words inside a WordNet for any language.

## Setup the language combinations 
Any language in the WordNet format can be used in this application. There are two configuration files that need to be changed, one in the backend and one in the frontend.
### Backend configuration
Under the `backend` folder there is a file called `post_install_scripts.py`. This file needs to be configured with the languages you want to have available in the application. The comments in the file explain which variables need to be changed. Languages can be downloaded from the official WordNet repository by inserting language codes in the `OMW_LANG` list variable. Custom developed WordNets can also be used by inserting download links to the zipped WordNet XML file in the `OTHER_URI` list variable.

Some European Languages ('de', 'fr', 'es', 'pt', 'it', 'nl') have more complete WordNets with the same amount of synsets as the English WordNet. In order to achieve this, parts of these WordNets have been constructed automatically, with the purpose to create complete multilingual WordNets. To use these WordNets, they must be specified in the `EU_LANGS` list variable. The `EU_LANGS` list variable should always have 'en' included in it, since English serves as a pivot language that enables the multilingual connection between the languages with the so-called Interlingual Indicator (ILI). If you don't want English equivalents of words in other languages to be displayed, it can be filtered out in the frontend. In the same directory where the `post_install_scripts.py` file is located, there are also examples of other configurations that can be used or adapted as seen fit.

### Frontend configuration
Under the `frontend\src\app\config` folder there is a file called `app-config.ts`. The configurations in this file should be self-explanatory, but it is important that the languages configured in this file should match the languages specified in `post_install_scripts.py` in the backend. In the same directory where the `app-config.py` file is located, there are also examples of other configurations that can be used or adapted as seen fit.

## Execution
After the configurations have been completed, the application can be started by running the docker containers from the root folder:
```bash
docker-compose up
```
## Sample Projects
Below are some sample projects that have been configured and deployed using this open source project:
<ul>
<li>European Languages: <a href="https://wn.yovisto.com/wordnet" target="_blank">https://wn.yovisto.com/wordnet</a></li>
<li>German: <a href="https://wn.yovisto.com/wordnet-de" target="_blank">https://wn.yovisto.com/wordnet-de</a></li>
<li>Afrikaans: <a href="https://wn.yovisto.com/wordnet-af" target="_blank">https://wn.yovisto.com/wordnet-af</a></li>
<li>South African Indigenous Languages: <a href="https://wn.yovisto.com/wordnet-south-africa" target="_blank">https://wn.yovisto.com/wordnet-south-africa</a></li>
<li>Ukrainian: <a href="https://wn.yovisto.com/wordnet-ua" target="_blank">https://wn.yovisto.com/wordnet-ua</a></li>
</ul>


