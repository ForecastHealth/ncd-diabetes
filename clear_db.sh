#!/bin/bash

# Clear all rows from validation_results.db while preserving table structure

DB_FILE="results.db"

if [ ! -f "$DB_FILE" ]; then
    echo "Error: $DB_FILE not found"
    exit 1
fi

echo "Clearing rows from validation database..."

sqlite3 "$DB_FILE" << EOF
DELETE FROM job_results;
DELETE FROM metrics;
DELETE FROM validation_runs;
EOF

echo "Database rows cleared successfully"
echo "Tables preserved: job_results, metrics, validation_runs"