# Scenario Build System

This system allows you to compose scenario files from reusable components, reducing duplication and making scenarios easier to maintain.

## Structure

```
build/
├── components/           # Reusable parameter components
│   ├── base.json        # Country parameter (included in all scenarios)
│   ├── low_dose_beclom.json
│   ├── high_dose_beclom.json
│   ├── oral_prednisolone.json
│   ├── inhaled_beta_agonist.json
│   └── tobacco_interventions.json
├── configs/             # YAML configuration files for scenarios
│   ├── asthma_baseline.yml
│   ├── asthma_cr1.yml
│   ├── asthma_cr3.yml
│   └── asthma_null.yml
├── build_scenario.py    # Build script
└── README.md           # This file
```

## Usage

### Build a Single Scenario

Build a scenario from its YAML configuration:

```bash
python3 build_scenario.py configs/asthma_baseline.yml
python3 build_scenario.py configs/asthma_cr1.yml
```

### Build All Scenarios

Build all scenarios defined in the configs/ directory:

```bash
python3 build_scenario.py --all
```

## Configuration Format

Each YAML configuration file specifies:
- **metadata**: Label, description, and authors
- **components**: List of component JSON files to include
- **overrides**: Parameter values to override after merging components
- **output**: Where to save the generated scenario

Example configuration (`configs/asthma_cr1.yml`):

```yaml
metadata:
  label: "Appendix 3 - CR1 Scenario"
  description: "Acute treatment of asthma exacerbations with inhaled bronchodilators and oral steroids."
  authors: []

components:
  - base.json
  - low_dose_beclom.json
  - high_dose_beclom.json
  - oral_prednisolone.json
  - inhaled_beta_agonist.json
  - tobacco_interventions.json

# Override specific values for CR1 scenario
overrides:
  "Oral Prednisolone Target Coverage":
    value: 0.95

output: ../scenarios/asthma_cr1.json
```

## Workflow

1. **Create/Edit YAML config**: Define which components to include and any overrides
2. **Build scenario**: Run `python3 build_scenario.py configs/your_scenario.yml`
3. **Optional manual editing**: Further customize the generated JSON if needed
4. **Maintain**: When base parameters change, update component files and rebuild all scenarios with `--all`

## Creating New Scenarios

1. Create a new YAML file in `configs/`:
   ```yaml
   metadata:
     label: "My New Scenario"
     description: "Description of what this scenario does"
   
   components:
     - base.json
     - low_dose_beclom.json
     # ... other components
   
   overrides:
     "Some Parameter Name":
       value: 0.75
   
   output: ../scenarios/my_new_scenario.json
   ```

2. Build it:
   ```bash
   python3 build_scenario.py configs/my_new_scenario.yml
   ```

## Benefits

- **DRY**: Country parameter paths defined once
- **Maintainable**: Update intervention parameters in one place
- **Composable**: Mix and match components as needed
- **Traceable**: Clear inheritance from components to final scenarios