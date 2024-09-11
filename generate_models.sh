#!/bin/bash
find ./models -name '*.json' -print0 | while IFS= read -r -d '' file; do
    name=$(jq -r '.metadata.name // empty' "$file")
    [ -z "$name" ] && name=$(basename "$file")
    echo "{\"name\": \"$name\", \"path\": \"$file\"}"
done | jq -s 'sort_by(.name) | { models: . }' > list_of_models.json
echo "Generated list_of_models.json"