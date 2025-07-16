#!/bin/bash

# ==============================================================================
# transfer.sh
#
# Synchronizes the structure and non-data files from the ncd-asthma model
# directory to the ncd-copd directory.
#
# It is designed to update scripts, validation tools, and other project
# scaffolding while preserving the unique data and configuration of the
# COPD model.
# ==============================================================================

# --- Configuration ---
# Set the source and destination directories.
# Using ~ for the home directory is fine here.
SOURCE_DIR=~/Models/ncd-asthma
DEST_DIR=~/Models/ncd-diabetes

# --- Pre-run Checks ---
# Ensure the source and destination directories actually exist.
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' not found."
    exit 1
fi

if [ ! -d "$DEST_DIR" ]; then
    echo "Error: Destination directory '$DEST_DIR' not found."
    exit 1
fi

echo "Source:      $SOURCE_DIR"
echo "Destination: $DEST_DIR"
echo "--------------------------------------------------"

# --- Synchronization using rsync ---
#
# -a: Archive mode (preserves permissions, ownership, timestamps, etc.)
# -v: Verbose mode (shows what's being transferred)
# --delete: Deletes files in DEST_DIR that do not exist in SOURCE_DIR.
#           This is crucial for removing obsolete files and directories.
# --exclude: Specifies patterns of files/directories to NOT touch.
#
# We are excluding the specific files and directories you requested to keep
# in the COPD project, as well as temporary/result files that shouldn't be copied.
#
rsync -avC --delete\
    --exclude 'model.json' \
    --exclude 'project.csv' \
    --exclude 'DOCUMENTATION.md' \
    --exclude 'data/' \
    --exclude 'scenarios/' \
    --exclude 'results.db' \
    --exclude 'tmp/' \
    --exclude 'transfer.sh' \
    "$SOURCE_DIR/" "$DEST_DIR/"

echo "--------------------------------------------------"
echo "✅ Synchronization complete."
echo "The following were NOT modified in the destination:"
echo "  - model.json"
echo "  - project.csv"
echo "  - DOCUMENTATION.md"
echo "  - The entire 'data/' directory"
echo "  - The entire 'scenarios/' directory"
