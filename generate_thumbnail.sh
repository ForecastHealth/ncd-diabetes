#!/bin/bash

# Check if source file exists
if [ -f ./static/thumbnail.png ]; then
    echo "Converting thumbnail..."
    convert ./static/thumbnail.png -resize 1000x564 thumbnail.png
    echo "Thumbnail created successfully"
else 
    echo "Error: ./static/thumbnail.png not found"
    exit 1
fi
