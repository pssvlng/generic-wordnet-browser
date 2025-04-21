docker pull dbpedia/dbpedia-spotlight
docker volume create spotlight-models-de
docker run -ti \
 --restart unless-stopped \
 --name dbpedia-spotlight.de \
 --mount source=spotlight-models-de,target=/opt/spotlight \
 -p 2223:80 \
 dbpedia/dbpedia-spotlight \
 spotlight.sh de