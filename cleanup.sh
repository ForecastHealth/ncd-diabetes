#!/bin/bash

# Cleanup script to remove directories and files from models/ and scenarios/

# Function to safely remove a directory
remove_directory() {
    local dir="$1"
    if [ -d "$dir" ]; then
        echo "Removing contents of $dir"
        rm -rf "${dir:?}"/*
        echo "Removed contents of $dir"
    else
        echo "$dir does not exist. Skipping."
    fi
}

# Main script
echo "Starting cleanup process..."

# Clean up models directory
remove_directory "models"

# Clean up scenarios directory
remove_directory "scenarios"

# Clean up docs/models directory
remove_directory "./docs/models"

# Clean up docs/scenarios directory
remove_directory "./docs/scenarios"

echo "Cleanup process completed."
