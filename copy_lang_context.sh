#!/bin/bash

FILE_TO_COPY="docker-compose-$1.yml"
DESTINATION="docker-compose.yml"
cp "$FILE_TO_COPY" "$DESTINATION"
echo "Copied '$FILE_TO_COPY' to '$DESTINATION'"

FILE_TO_COPY="backend/post_install_scripts.$1.py"
DESTINATION="backend/post_install_scripts.py"
cp "$FILE_TO_COPY" "$DESTINATION"
echo "Copied '$FILE_TO_COPY' to '$DESTINATION'"

FILE_TO_COPY="frontend/src/app/config/app-config.$1.ts"
DESTINATION="frontend/src/app/config/app-config.ts"
cp "$FILE_TO_COPY" "$DESTINATION"
echo "Copied '$FILE_TO_COPY' to '$DESTINATION'"

PORT_NUMBER=$2
FILE="frontend/src/app/services/wordnet.service.ts"
sed -i "s/127.0.0.1:5000/127.0.0.1:${PORT_NUMBER}/" "$FILE"

echo "Port Number changed to '${PORT_NUMBER}' in '${FILE}'."

exit 0
