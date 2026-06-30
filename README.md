# NCD Diabetes Module

This repository owns the diabetes epidemiology core graph, diabetes clinical intervention parameters, diabetes scenario templates, and diabetes validation command surface. It is shaped as a compiled-together botech disease module: the local materializer applies diabetes-owned templates, while demographic opening population and background mortality are supplied by the compiler or proof lowerer.

The current command surface is `python scripts/orchestrator_scenarios.py catalog`, `python scripts/orchestrator_scenarios.py templates`, and `python scripts/orchestrator_scenarios.py materialize --template-id diabetes_d1 --output-dir /tmp/diabetes-d1`. Run `python scripts/validate_module_contract.py` before using or syncing the module.
