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
            echo "  --scenarios   Comma-separated list of scenarios to run (default: all asthma and tobacco scenarios)"
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
    # Default: run asthma_baseline, asthma_cr1, and all tobacco scenarios
    SCENARIOS=(asthma_baseline asthma_cr1 tobacco_t1 tobacco_t2 tobacco_t3 tobacco_t4 tobacco_t5 tobacco_t6)
    log_step "Using default scenarios: ${SCENARIOS[*]}"
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

# Step 3: Process analytics
log_step "Step 3: Processing analytics..."

# Determine baseline scenario (usually the first one that contains 'baseline')
BASELINE_SCENARIO=""
for scenario in "${SCENARIOS[@]}"; do
    if [[ "$scenario" == *"baseline"* ]]; then
        BASELINE_SCENARIO="$scenario"
        break
    fi
done

if [ -z "$BASELINE_SCENARIO" ]; then
    # Default to first scenario if no baseline found
    BASELINE_SCENARIO="${SCENARIOS[0]}"
    log_warning "No baseline scenario found, using $BASELINE_SCENARIO as baseline"
else
    log "Using $BASELINE_SCENARIO as baseline scenario"
fi

PROCESS_CMD="python3 scripts/process_analytics.py --baseline $BASELINE_SCENARIO"
log "Running command: $PROCESS_CMD"

if $PROCESS_CMD 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Analytics processed successfully"
else
    log_error "Failed to process analytics"
    exit 1
fi

# Find the generated results file
RESULTS_FILE=$(ls -t results/analytics_results_*.csv 2>/dev/null | head -1)

if [ -z "$RESULTS_FILE" ] || [ ! -f "$RESULTS_FILE" ]; then
    log_error "No results file was generated"
    exit 1
fi

log_success "Results file created: $RESULTS_FILE"

# Step 4: Upload results to database (if configured)
if [ "$SKIP_UPLOAD" = false ]; then
    log_step "Step 4: Uploading results to database..."
    
    if ./upload_results.sh "$RESULTS_FILE" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Results uploaded successfully"
    else
        log_error "Failed to upload results to database"
        exit 1
    fi
else
    log_warning "Step 4: Skipping database upload (no configuration)"
fi

# Summary
log ""
log "=========================================="
log "${GREEN}Investment Case Process Completed Successfully!${NC}"
log "=========================================="
log "Summary:"
log "  - Scenarios processed: ${SCENARIOS[*]}"
log "  - Countries processed: $COUNTRY_COUNT"
log "  - Results file: $RESULTS_FILE"
log "  - Log file: $LOG_FILE"

TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - VALIDATION_START))
log "  - Total time: $((TOTAL_DURATION / 60)) minutes and $((TOTAL_DURATION % 60)) seconds"

if [ "$SKIP_UPLOAD" = true ]; then
    log ""
    log "${YELLOW}Note:${NC} Database upload was skipped. To enable it:"
    log "  1. Create a .env.local file with DB_HOST, DB_USER, DB_PASS, DB_NAME"
    log "  2. Run: ./upload_results.sh $RESULTS_FILE"
fi

log ""
log "Finished at: $(date)"