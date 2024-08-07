#!/bin/bash

find ./models -name '*.json' -print0 | while IFS= read -r -d '' file; do
    name=$(jq -r '.metadata.file_id // empty' "$file")
    [ -z "$name" ] && name=$(basename "$file")
    echo "{\"name\": \"$name\", \"path\": \"$file\"}"
done | jq -s '{ models: . }' > list_of_models.json

echo "Generated list_of_models.json"