docker pull dbpedia/dbpedia-spotlight
docker volume create spotlight-models-en
docker run -ti \
 --restart unless-stopped \
 --name dbpedia-spotlight.en \
 --mount source=spotlight-models-en,target=/opt/spotlight \
 -p 2222:80 \
 dbpedia/dbpedia-spotlight \
 spotlight.sh en