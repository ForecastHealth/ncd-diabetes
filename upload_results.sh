#!/bin/bash

# Check if CSV file is provided as argument
if [ -z "$1" ]; then
    echo "Usage: $0 <csv_file_path>"
    echo "Example: $0 results/analytics_results_20250818_123317.csv"
    exit 1
fi

RESULTS_FILE="$1"

# Check if file exists
if [ ! -f "$RESULTS_FILE" ]; then
    echo "Error: File $RESULTS_FILE does not exist"
    exit 1
fi

# Source environment variables
source .env.local

# Set up PGPASSWORD environment variable for non-interactive password entry
export PGPASSWORD=$DB_PASS

# Create the schema if it doesn't exist
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "CREATE SCHEMA IF NOT EXISTS who_bloomberg_investment_case;"

# Extract filename without path and extension for table name
FILENAME=$(basename "$RESULTS_FILE" .csv)
TABLE_NAME="who_bloomberg_investment_case.${FILENAME}"

# Create the table with the new CSV structure matching NEW_SCHEMA.md with timestamp and cumulative values
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "DROP TABLE IF EXISTS $TABLE_NAME;"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "CREATE TABLE $TABLE_NAME (
    country VARCHAR(3),
    scenario TEXT,
    metric TEXT,
    year DATE,
    value NUMERIC,
    cum_value NUMERIC,
    source TEXT
);"

# Load the data from the CSV file into the table
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\copy $TABLE_NAME (country, scenario, metric, year, value, cum_value, source) FROM '$RESULTS_FILE' DELIMITER ',' CSV HEADER;"

echo "Uploaded $RESULTS_FILE to $TABLE_NAME"

# Unset the PGPASSWORD variable for security
unset PGPASSWORD
