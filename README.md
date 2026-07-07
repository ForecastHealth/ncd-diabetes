# NCD Diabetes Module

This repository owns the diabetes epidemiology core graph. It is shaped as a compiled-together botech disease module: demographic opening population and background mortality are supplied by the compiler or proof lowerer.

Clinical diabetes intervention graph slices now live in sibling intervention repositories. The diabetes module keeps neutral incidence transform extension points, but it no longer owns intervention coverage, effect-size, population-in-need, resource-population, or Appendix 3 comparison-template logic.

The current command surface is `python scripts/orchestrator_scenarios.py catalog`, `python scripts/orchestrator_scenarios.py templates`, and `python scripts/orchestrator_scenarios.py materialize --template-id diabetes_baseline --output-dir /tmp/diabetes-baseline`. Run `python scripts/validate_module_contract.py` before using or syncing the module.
