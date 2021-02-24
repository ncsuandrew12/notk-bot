#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${DIR}/common.bash

set -e

serverID=$(jq -r '.production.serverID' ${ROOT_DIR}/bin/config.json)
secretFile=$(jq -r '.production.secretFile' ${ROOT_DIR}/bin/config.json)

token=$(jq -r '.token' ${ROOT_DIR}/bin/$secretFile)

echo "Restarting server!"

curl "https://games.plox.host/api/client/servers/${serverID}/power" \
  -H "Authorization: Bearer ${token}" \
  -H 'Content-Type: application/json' \
  -H "Accept: Application/vnd.pterodactyl.v1+json" \
  -X POST \
  -b 'pterodactyl_session'='eyJpdiI6InhIVXp5ZE43WlMxUU1NQ1pyNWRFa1E9PSIsInZhbHVlIjoiQTNpcE9JV3FlcmZ6Ym9vS0dBTmxXMGtST2xyTFJvVEM5NWVWbVFJSnV6S1dwcTVGWHBhZzdjMHpkN0RNdDVkQiIsIm1hYyI6IjAxYTI5NDY1OWMzNDJlZWU2OTc3ZDYxYzIyMzlhZTFiYWY1ZjgwMjAwZjY3MDU4ZDYwMzhjOTRmYjMzNDliN2YifQ%3D%3D' \
  -d '{
  "signal": "restart"
}'

echo "Server restarted!"
