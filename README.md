---
title: Diabetes epidemiology
module_identifier: ncd-diabetes
owner: Forecast Health
last_updated: 2026-09-30
status: Executable source module
---

# Diabetes epidemiology

## Contents

- [Purpose](#purpose)
- [Method](#method)
- [Inputs and outputs](#inputs-and-outputs)
- [Parameters and templates](#parameters-and-templates)
- [Data and evidence](#data-and-evidence)
- [Relationships](#relationships)
- [Assumptions and limitations](#assumptions-and-limitations)
- [Status](#status)

## Purpose

This module models diabetes incidence, the diabetes episode state, diabetic retinopathy, nephropathy, lower-extremity amputation, disability, and cause-specific mortality within the canonical demographic population.

## Method

Diabetes is a marginal disease process. Its living-state partition contains a derived disease-free residual, the diabetes episode state and three complication states. At each model-year opening, the coordinator sets the residual to the canonical population minus the declared diabetes and complication states, by age and sex. During the year, incidence and complication transitions compete in a continuous-hazard phase based on the phase-opening balances. Background mortality then applies to the disease states.

Risk-factor modules can modify diabetes incidence. Clinical components can reduce the incidence of retinopathy, nephropathy, and lower-extremity amputation through disease-owned extension points. Post-run metric modules calculate healthy years and disease burden from the raw state and mortality outputs.

### Calibration to observed deaths

The [opening-state contract](data/diabetes-opening-state.contract.v3.json) declares a rate calibration that the shared `opening-state-reconciliation` preflight applies before the first model year, with one result for baseline and every comparison. The four diabetes-state fatality inputs (diabetes, retinopathy, lower-extremity amputation and nephropathy) are scaled by one common factor by sex and single age so that the opening year's deaths in the diabetes states equal WHO Global Health Estimates 2021 diabetes death rates applied to the opening population, distributed within each GHE age band by the GBD age pattern of diabetes deaths. Observed total diabetes prevalence is divided among uncomplicated diabetes and the three complication states in the shares a cohort reaches at each age under the fitted rates, instead of opening the complication states at zero. Deaths in the nephropathy state count as diabetes deaths.

## Inputs and outputs

Required inputs are the reconciled opening population at risk and background mortality rates. An incidence modifier is optional. The module publishes diabetes episode population, diabetes incidence, diabetes-specific mortality, and populations with retinopathy, nephropathy, and lower-extremity amputation.

## Parameters and templates

The source module exposes only `diabetes_baseline`. The disease parameter registry is empty because clinical intervention parameters and comparison values live in separate intervention repositories.

## Data and evidence

[`model.json`](model.json) is the executable graph. The [module contract](interface/diabetes-epidemiology-core.module.contract.v1.json) defines composition and runtime semantics. The opening-state recipe defines baseline initialization. The contract identifies Spectrum/OneHealth diabetes material and the current module cleanup as default provenance.

Routine care is declared in [`resource_requirements.json`](resource_requirements.json) as `routine_care_services`: each entry names a service by the module and block that declare it, `ncd-diabetes-stdglyccontrol` (`d3-standard-glycaemic-control`), `ncd-diabetes-retinopathyscrn` (`d2-retinopathy-screening`), `ncd-diabetes-nephropathyscr` (`d5-nephropathy-screening-follow-up`) and `ncd-diabetes-neuropathyscr` (`d1-foot-care`), with the disease states it is delivered to. This module does not copy the services' resources. The compiler takes the quantities, cost items, population in need and baseline coverage from each service's own declaration and costs the service at its baseline coverage in both scenarios. When the owning intervention is selected, its block also costs the service for the population the intervention reaches, at baseline coverage in the baseline scenario and at the target coverage in the comparison; routine care of the disease states continues beside it from the same declaration.

Staff time is priced from one shared salary item per staff type, `cost-item.workforce-salary.<type>`: `nurse`, `generalist-primary-care-doctor`, `specialist`, `therapist` and `counsellor`. A type is the same item in every module that uses it, so a generalist minute costs the same everywhere, and each type can be edited on its own: a specialist can be paid differently from a generalist doctor. The item is an annual salary. Its default is the country's WHO-CHOICE annual salary from the data service for the type's cadre (skill level 4 for doctors and specialists, 3 for nurses and therapists, 2 for counsellors); the cadre is the default source, not the item. A staff minute costs that salary divided by 126,720 working minutes a year (8 hours, 22 days a month, 12 months). The data service uses this convention for its WHO-CHOICE cost per minute, and every clinical staff cost has used it. The per-minute values in the resource graphs are defaults for use without a country. Tobacco policy programme roles are separate staff types, since none is the same job as a clinical one.

## Relationships

The demographic module supplies canonical population and background mortality. `opening-state-reconciliation` initializes the disease partition. Separate repositories own standard and intensive glycaemic control, retinopathy screening, nephropathy screening and blood-pressure control, and comprehensive foot care.

Routine care references the standard glycaemic control, retinopathy screening, nephropathy screening and follow-up, and comprehensive foot care services declared by those repositories. The services are applied to the diabetes episode and complication states without changing disease transitions. The intervention graph slices count their reached population from the diabetes episode state, the population whose complication transitions their effects reduce, while routine care counts people in the diabetes episode and complication states.

## Assumptions and limitations

The disease-free state is a local residual, not an additional population. The model is a marginal diabetes estimate and must remain reconciled to the canonical population. Intervention graph slices modify complication incidence but do not model detailed screening, diagnosis, adherence, or treatment pathways.

## Status

The disease graph, compiler contract, baseline template, opening-state recipe, intervention extension points, and routine-care declarations are implemented. The source graph requires compiler lowering and is not a standalone national model.
