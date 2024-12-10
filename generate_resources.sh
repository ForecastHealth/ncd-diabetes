#!/bin/bash
find ./resources -name '*.json' -print0 | while IFS= read -r -d '' file; do
    title=$(jq -r '.metadata.name // empty' "$file")
    
    # If title is missing, use the filename
    [ -z "$title" ] && title=$(basename "$file")
    
    # Get just the filename without the path
    filename=$(basename "$file")
    
    # Output the JSON object for this report
    echo "{\"name\": \"$title\", \"filename\": \"$filename\"}"
done | jq -s 'sort_by(.title) | { resources: . }' > list_of_resources.json

echo "Generated list_of_resources.json"
