#!/bin/bash
#param1: language code (e.g., en, de, es)

FILE_TO_COPY="docker-compose-$1.yml"
DESTINATION="docker-compose.yml"
sudo cp "$FILE_TO_COPY" "$DESTINATION"
echo "Copied '$FILE_TO_COPY' to '$DESTINATION'"

FILE_TO_COPY="backend/post_install_scripts.$1.py"
DESTINATION="backend/post_install_scripts.py"
sudo cp "$FILE_TO_COPY" "$DESTINATION"
echo "Copied '$FILE_TO_COPY' to '$DESTINATION'"

FILE_TO_COPY="frontend/src/app/config/app-config.$1.ts"
DESTINATION="frontend/src/app/config/app-config.ts"
sudo cp "$FILE_TO_COPY" "$DESTINATION"
echo "Copied '$FILE_TO_COPY' to '$DESTINATION'"

if [ "$1" = "eu" ]; then
    BASE_URL="/wordnet/"
else
    BASE_URL="/wordnet-$1/"
fi
FILE="frontend/angular.json"
sudo sed -i "s|\"baseHref\": \"/\"|\"baseHref\": \"$BASE_URL\"|" "$FILE"

echo "Proxy Path '$BASE_URL' set for '$1'."

NETWORK_NAME="lang-network"
if ! sudo docker network ls | grep -q "$NETWORK_NAME"; then    
    sudo docker network create "$NETWORK_NAME"
    echo "Network '$NETWORK_NAME' created."
else
    echo "Network '$NETWORK_NAME' already exists."
fi

if ! sudo podman network ls | grep -q "$NETWORK_NAME"; then    
    sudo podman network create "$NETWORK_NAME"
    echo "Network '$NETWORK_NAME' created."
else
    echo "Network '$NETWORK_NAME' already exists."
fi

exit 0
