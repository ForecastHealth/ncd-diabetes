#!/bin/bash
set -e

# Make sure jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq is required but not installed. Please install jq and try again."
    exit 1
fi

# Load GitHub token from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$GITHUB_ACCESS_TOKEN" ]; then
    echo "GitHub access token not found. Please set GITHUB_ACCESS_TOKEN in your .env file."
    exit 1
fi

ORG="ForecastHealth"
TOPICS=("model")
REPOS=""

# Function to make GitHub API requests
github_api_get() {
    curl -s -H "Authorization: Bearer $GITHUB_ACCESS_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "$@"
}

# Function to search repositories
search_repos() {
    local page=1
    while true; do
        local response=$(github_api_get "https://api.github.com/search/repositories?q=topic:model+org:$ORG&page=$page&per_page=100")
        local items=$(echo "$response" | jq -r '.items')
        if [ "$(echo "$items" | jq 'length')" -eq "0" ]; then
            break
        fi
        REPOS+="$items"
        ((page++))
    done
}

# Function to get all topics
get_all_topics() {
    echo "$REPOS" | jq -r '.[].topics[]' | sort | uniq -c | sort -rn
}

# Function to filter repositories
filter_repos() {
    local topics_json=$(printf '%s\n' "${TOPICS[@]}" | jq -R . | jq -s .)
    echo "$REPOS" | jq --argjson topics "$topics_json" '
        .[] | select(.topics as $repo_topics | ($topics | all(. as $topic | $repo_topics | index($topic) != null)))
    '
}

# Function to download JSON files from a specific directory
download_json_files() {
    local repo_name=$(echo "$1" | jq -r '.name')
    local repo_full_name=$(echo "$1" | jq -r '.full_name')
    local directory="$2"
    
    echo "Processing $directory directory in repository: $repo_name"
    
    local contents=$(github_api_get "https://api.github.com/repos/$repo_full_name/contents/$directory")
    if [ "$(echo "$contents" | jq -r 'type')" = "array" ]; then
        echo "$contents" | jq -c '.[]' | while read -r item; do
            local file_name=$(echo "$item" | jq -r '.name')
            if [[ $file_name == *.json ]]; then
                local download_url=$(echo "$item" | jq -r '.download_url')
                mkdir -p "$directory/$repo_name"
                curl -s -o "$directory/$repo_name/$file_name" "$download_url"
                echo "Downloaded: $directory/$repo_name/$file_name"
            fi
        done
    else
        echo "No '$directory' directory found in $repo_name"
    fi
}

# Main script
echo "Searching for repositories with 'model' topic in $ORG organization..."
search_repos
repo_count=$(echo "$REPOS" | jq 'length')
echo "Found $repo_count repositories with 'model' topic"

echo -e "\nAvailable topics (with occurrence count):"
get_all_topics

echo -e "\nEnter additional topics to filter by (space-separated), or press Enter to continue:"
read -r user_input
if [ -n "$user_input" ]; then
    IFS=' ' read -ra user_topics <<< "$user_input"
    TOPICS+=("${user_topics[@]}")
fi

echo "Filtering repositories..."
filtered_repos=$(filter_repos)
filtered_count=$(echo "$filtered_repos" | jq -s 'length')
echo "Found $filtered_count repositories matching the selected topics: ${TOPICS[*]}"

echo "Processing filtered repositories..."
echo "$filtered_repos" | jq -c '.' | while read -r repo; do
    download_json_files "$repo" "models"
    download_json_files "$repo" "scenarios"
done

echo "Script completed."