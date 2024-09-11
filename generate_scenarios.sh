#!/bin/bash

# generate_scenarios_list.sh
# Generates a list of scenarios for each model.

# Function to process a single scenario file
process_scenario() {
    local scenario_path="$1"
    local scenario_name=$(jq -r '.name' "$scenario_path")
    local models=$(jq -r '.models[]' "$scenario_path")

    echo "$models" | while read -r model; do
        if [ -n "$model" ]; then
            echo "$model:$scenario_name:$scenario_path"
        fi
    done
}

# Main script
rm -f list_of_scenarios.json  # Remove existing file if it exists

# Process all JSON files in ./scenarios/*/
export -f process_scenario
find ./scenarios -type f -name "*.json" -exec bash -c 'process_scenario "$0"' {} \; | sort | uniq > temp_scenarios.txt

# Generate the JSON structure
echo "{" > list_of_scenarios.json
first_model=true

while IFS=: read -r model scenario_name scenario_path; do
    if [ "$first_model" = true ]; then
        first_model=false
    else
        echo "," >> list_of_scenarios.json
    fi

    echo "  \"$model\": [" >> list_of_scenarios.json
    first_scenario=true

    while IFS=: read -r model2 scenario_name2 scenario_path2; do
        if [ "$model" = "$model2" ]; then
            if [ "$first_scenario" = true ]; then
                first_scenario=false
            else
                echo "," >> list_of_scenarios.json
            fi

            cat << EOF >> list_of_scenarios.json
    {
      "name": "$scenario_name2",
      "path": "$scenario_path2"
    }
EOF
        fi
    done < temp_scenarios.txt

    echo "  ]" >> list_of_scenarios.json
done < temp_scenarios.txt

echo "}" >> list_of_scenarios.json

# Pretty-print the JSON
jq '.' list_of_scenarios.json > temp.json && mv temp.json list_of_scenarios.json

rm temp_scenarios.txt

echo "Generated list_of_scenarios.json"