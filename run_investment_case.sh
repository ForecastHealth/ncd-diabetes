#!/bin/bash

# Investment Case Automation Script
# Automates the process described in INVESTMENT_CASE_INSTRUCTIONS.md
# Usage: ./run_investment_case.sh [--scenarios scenario1,scenario2] [--force]

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
COUNTRIES_FILE="./countries/list_of_pruned_countries.json"
SCENARIOS_DIR="./scenarios"
MODEL_FILE="./model.json"
ENVIRONMENT="appendix_3"
MAX_INSTANCES=100  # Same as TUI default, adjust as needed
FORCE_RUN=false
SELECTED_SCENARIOS=""
LOG_FILE="investment_case_$(date +%Y%m%d_%H%M%S).log"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --scenarios)
            SELECTED_SCENARIOS="$2"
            shift 2
            ;;
        --force)
            FORCE_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--scenarios scenario1,scenario2] [--force]"
            echo ""
            echo "Options:"
            echo "  --scenarios   Comma-separated list of scenarios to run (default: all scenarios in scenarios/ directory)"
            echo "  --force       Force re-run of all validations"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Logging functions
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_step() {
    log "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ${GREEN}▶${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_success() {
    log "${GREEN}✓${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Start logging
log "=========================================="
log "Investment Case Automation Script"
log "Started at: $(date)"
log "=========================================="

# Check prerequisites
log_step "Checking prerequisites..."

if ! command_exists python3; then
    log_error "Python3 is not installed"
    exit 1
fi

if [ ! -f "$MODEL_FILE" ]; then
    log_error "Model file not found: $MODEL_FILE"
    exit 1
fi

if [ ! -f "$COUNTRIES_FILE" ]; then
    log_error "Countries file not found: $COUNTRIES_FILE"
    exit 1
fi

if [ ! -d "$SCENARIOS_DIR" ]; then
    log_error "Scenarios directory not found: $SCENARIOS_DIR"
    exit 1
fi

# Check if .env.local exists for database upload
if [ ! -f ".env.local" ]; then
    log_warning ".env.local file not found. Database upload will be skipped."
    SKIP_UPLOAD=true
else
    SKIP_UPLOAD=false
    source .env.local
    # Check if required variables are set
    if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASS" ] || [ -z "$DB_NAME" ]; then
        log_warning "Database credentials not fully configured in .env.local. Upload will be skipped."
        SKIP_UPLOAD=true
    fi
fi

log_success "Prerequisites check completed"

# Determine which scenarios to run
if [ -z "$SELECTED_SCENARIOS" ]; then
    # Default: run all scenarios found in the scenarios directory
    SCENARIOS=()
    for scenario_file in "$SCENARIOS_DIR"/*.json; do
        if [ -f "$scenario_file" ]; then
            # Extract filename without path and .json extension
            scenario_name=$(basename "$scenario_file" .json)
            SCENARIOS+=("$scenario_name")
        fi
    done
    log_step "Using all scenarios from $SCENARIOS_DIR: ${SCENARIOS[*]}"
else
    # Parse comma-separated scenarios
    IFS=',' read -ra SCENARIOS <<< "$SELECTED_SCENARIOS"
    log_step "Using specified scenarios: ${SCENARIOS[*]}"
fi

# Validate scenarios exist
for scenario in "${SCENARIOS[@]}"; do
    if [ ! -f "$SCENARIOS_DIR/${scenario}.json" ]; then
        log_error "Scenario file not found: $SCENARIOS_DIR/${scenario}.json"
        exit 1
    fi
done

# Extract country count for progress tracking
COUNTRY_COUNT=$(python3 -c "import json; data = json.load(open('$COUNTRIES_FILE')); print(len(data['countries']))")
log_step "Will process ${#SCENARIOS[@]} scenarios across $COUNTRY_COUNT countries"

# Step 1: Run validation for each scenario
log_step "Step 1: Running validations..."
log "This may take a while as it processes ${#SCENARIOS[@]} scenarios × $COUNTRY_COUNT countries"

VALIDATION_START=$(date +%s)

# Build the CLI command
CLI_CMD="python3 -m validation_suite.cli"
CLI_CMD="$CLI_CMD --countries-file $COUNTRIES_FILE"
CLI_CMD="$CLI_CMD --scenarios-dir $SCENARIOS_DIR"
CLI_CMD="$CLI_CMD --model $MODEL_FILE"
CLI_CMD="$CLI_CMD --environment $ENVIRONMENT"
CLI_CMD="$CLI_CMD --max-instances $MAX_INSTANCES"
CLI_CMD="$CLI_CMD --scenarios ${SCENARIOS[*]}"
CLI_CMD="$CLI_CMD --database validation_results.db"  # Specify database file

if [ "$FORCE_RUN" = true ]; then
    CLI_CMD="$CLI_CMD --force"
fi

# Run validation
log "Running command: $CLI_CMD"
if $CLI_CMD 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Validation completed successfully"
else
    log_error "Validation failed"
    exit 1
fi

VALIDATION_END=$(date +%s)
VALIDATION_DURATION=$((VALIDATION_END - VALIDATION_START))
log "Validation took $((VALIDATION_DURATION / 60)) minutes and $((VALIDATION_DURATION % 60)) seconds"

# The validation suite saves results to CSV files, wait for them to be written
sleep 2

# Check if validation_results.csv was created
if [ ! -f "validation_results.csv" ]; then
    log_warning "validation_results.csv not found, checking for CSV files..."
    # Look for any CSV files that were just created
    LATEST_CSV=$(ls -t *.csv 2>/dev/null | head -1)
    if [ -n "$LATEST_CSV" ] && [ -f "$LATEST_CSV" ]; then
        log "Found CSV file: $LATEST_CSV"
        # Use this as our validation results
        cp "$LATEST_CSV" validation_results.csv
        log_success "Using $LATEST_CSV as validation_results.csv"
    else
        log_error "No validation results CSV was created"
        exit 1
    fi
fi

# Step 2: Fetch analytics data
log_step "Step 2: Fetching analytics data..."
log "This requires 5-second delays between API calls per their rate limiting"

FETCH_START=$(date +%s)

if python3 scripts/fetch_analytics.py --csv validation_results.csv 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Analytics data fetched successfully"
else
    log_error "Failed to fetch analytics data"
    exit 1
fi

FETCH_END=$(date +%s)
FETCH_DURATION=$((FETCH_END - FETCH_START))
log "Fetching took $((FETCH_DURATION / 60)) minutes and $((FETCH_DURATION % 60)) seconds"

# Step 3: Process completed - manual steps required
log_step "Step 3: Validation and fetching completed"
log_success "Automated steps completed successfully!"
log ""
log "${YELLOW}Manual steps required:${NC}"
log "  1. Run: python3 scripts/process_analytics.py --baseline <baseline_scenario>"
log "  2. Upload results to database if needed"

# Summary
log ""
log "=========================================="
log "${GREEN}Automated Steps Completed Successfully!${NC}"
log "=========================================="
log "Summary:"
log "  - Scenarios processed: ${SCENARIOS[*]}"
log "  - Countries processed: $COUNTRY_COUNT"
log "  - Log file: $LOG_FILE"

TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - VALIDATION_START))
log "  - Total time: $((TOTAL_DURATION / 60)) minutes and $((TOTAL_DURATION % 60)) seconds"

log ""
log "Finished at: $(date)"