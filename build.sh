#!/bin/bash

# Create necessary directories
mkdir -p docs/models/ docs/scenarios/

# Run the new shell scripts to generate model and scenario lists
./generate_models.sh
./generate_scenarios.sh
./generate_excel_workbooks.sh

# Copy JSON files to docs directory
cp ./pages_config.json ./docs/
cp ./list_of_countries.json ./docs/
cp ./list_of_models.json ./docs/
cp ./list_of_scenarios.json ./docs/
cp ./list_of_results.json ./docs/
cp ./list_of_excel_workbooks.json ./docs/

# Copy model and scenario JSON files while preserving directory structure
rsync -av --include='*/' --include='*.json' --exclude='*' ./models/ ./docs/models/
rsync -av --include='*/' --include='*.json' --exclude='*' ./scenarios/ ./docs/scenarios/
rsync -av --include='*/' --include='*.xlsx' --exclude='*' ./excel_workbooks/ ./docs/excel_workbooks/

# Convert DOCUMENTATION.md to HTML
pandoc DOCUMENTATION.md -o docs/documentation.html --standalone --template=docs/documentation_template.html

# Convert DISCLAIMER.md to HTML and replace the content in index.html
pandoc DISCLAIMER.md -o disclaimer.html
disclaimer_content=$(cat disclaimer.html)
disclaimer_content="${disclaimer_content//\\/\\\\}"
disclaimer_content="${disclaimer_content//\//\\/}"
disclaimer_content="${disclaimer_content//&/\\&}"
disclaimer_content="${disclaimer_content//$'\n'/\\n}"
sed -i.bak "/<div id=\"disclaimer\" class=\"disclaimer\">/,/<\/div>/c\\<div id=\"disclaimer\" class=\"disclaimer\">\\n$disclaimer_content\\n<\/div>" docs/index.html && rm docs/index.html.bak
rm disclaimer.html

echo "Build process completed."
