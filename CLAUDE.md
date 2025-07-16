# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the NCD (Non-Communicable Disease) Asthma Model repository - a health economics modeling system that simulates asthma interventions across different countries and scenarios. The model is built on the Spectrum framework and calculates disability-adjusted life years (DALYs), deaths averted, and economic outcomes for asthma treatment interventions.

## Common Development Commands

This is a python3-based project with no package.json. Common operations:

### Running Scripts
```bash
# Apply scenario to model
python3 scripts/apply_scenario.py --model model.json --scenario scenarios/asthma_cr1_scenario.json --output tmp/output.json

# Run validation suite
python3 -m validation_suite.cli --countries AFG --scenarios asthma_cr1_scenario

# Create country-specific scenarios
python3 scripts/create_country_scenarios.py

# Upload project to API
python3 scripts/upload_project.py

# Run economic analyses
python3 scripts/run_economic_analyses.py
```

### Dependencies
The project uses standard python3 libraries plus:
- `jsonpath-ng` for JSON manipulation
- SQLite for validation result storage
- Standard scientific python3 stack (likely numpy, pandas for data processing)

Install dependencies with: `pip install jsonpath-ng`

## Architecture Overview

### Core Components

1. **Model Definition** (`model.json`): Central JSON file defining the Asthma model structure with nodes, transitions, and parameters. Contains population states (DsFreeSus, AsthmaEpsd, Deceased) and calculation components.

2. **Scenario System** (`scenarios/`): JSON files defining intervention parameters:
   - `asthma_null_scenario.json`: Baseline with no interventions
   - `asthma_cr1_scenario.json`: CR1 intervention (acute treatment)
   - `asthma_cr3_scenario.json`: CR3 intervention (long-term management)

3. **Country Data** (`countries/`): JSON files listing countries and economic analysis configurations

4. **Validation Suite** (`validation_suite/`): Comprehensive testing framework with:
   - Database integration for tracking results
   - Multi-country validation orchestration
   - API client for external validation services
   - Analytics components for result processing

### Key Architecture Patterns

**JSONPath-based Parameter Application**: The `apply_scenario.py` script uses JSONPath expressions to dynamically modify model parameters, allowing flexible scenario configuration without hardcoded parameter locations.

**State-based Health Model**: The core model follows a state transition approach:
- `DsFreeSus` (Disease-free, susceptible population)
- `AsthmaEpsd` (Asthma episode state)
- `Deceased` (Death state)
- Surrogate nodes for calculations (disability, mortality effects)

**Validation Database**: SQLite database (`validation_results.db`) tracks validation runs, enabling incremental execution and result analysis across country/scenario combinations.

**Modular Validation Components**:
- `runner.py`: Orchestrates validation workflows
- `multi_country.py`: Handles batch country processing
- `api_client.py`: Interfaces with external validation APIs
- `analytics/`: Post-processing and analysis tools

### Data Flow

1. Base model (`model.json`) defines structure
2. Scenarios apply parameter modifications via JSONPath
3. Country-specific data populates epidemiological parameters
4. Validation suite tests model outputs across combinations
5. Results stored in database for tracking and analysis

### Treatment Interventions

The model simulates four asthma treatments:
- LowDoseBeclom (Low dose inhaled beclometasone + SABA)
- HighDoseBeclom (High dose inhaled beclometasone + SABA)
- InhaledShortActingBeta (Inhaled short acting beta agonist)
- AsthmaOralPrednisolone (Oral prednisolone + inhaled medications)

Each treatment has defined disability and mortality impacts, with coverage rates varying by scenario.

## Key File Locations

- `model.json`: Core model definition
- `scenarios/`: Intervention scenario definitions
- `scripts/apply_scenario.py`: Scenario application logic
- `validation_suite/cli.py`: Main validation entry point
- `validation_suite/runner.py`: Validation orchestration
- `countries/list_of_countries.json`: Country configurations
- `data/`: Epidemiological data files (CSV, Excel)
- `DOCUMENTATION.md`: Detailed model methodology and assumptions
