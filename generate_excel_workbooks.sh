#!/bin/bash

# Initialize an empty JSON object
echo "{" > list_of_excel_workbooks.json

# Find all .xlsx files and process them
find ./excel_workbooks -name '*.xlsx' | while read -r filepath; do
  # Extract the filename without the path
  filename=$(basename "$filepath")
  
  # Add entry to the JSON
  echo "  \"$filename\": [" >> list_of_excel_workbooks.json
  echo "    {" >> list_of_excel_workbooks.json
  echo "      \"name\": \"$filename\"," >> list_of_excel_workbooks.json
  echo "      \"path\": \"$filepath\"" >> list_of_excel_workbooks.json
  echo "    }" >> list_of_excel_workbooks.json
  echo "  ]," >> list_of_excel_workbooks.json
done

# Remove the trailing comma from the last entry and close the JSON object
sed -i '$ s/,$//' list_of_excel_workbooks.json
echo "}" >> list_of_excel_workbooks.json

echo "Generated list_of_excel_workbooks.json"
