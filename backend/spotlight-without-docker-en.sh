wget https://repo1.maven.org/maven2/org/dbpedia/spotlight/rest/1.1/rest-1.1-jar-with-dependencies.jar
wget -O en.tar.gz http://downloads.dbpedia.org/repo/dbpedia/spotlight/spotlight-model/2022.03.01/spotlight-model_lang=en.tar.gz
tar xzf en.tar.gz
java -Xmx8G -jar rest-1.1-jar-with-dependencies.jar en http://localhost:2222/rest