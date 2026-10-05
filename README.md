---
title: Diabetes epidemiology
module_identifier: ncd-diabetes
owner: Forecast Health
last_updated: 2026-10-05
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

## Inputs and outputs

Required inputs are the reconciled opening population at risk and background mortality rates. An incidence modifier is optional. The module publishes diabetes episode population, diabetes incidence, diabetes-specific mortality, and populations with retinopathy, nephropathy, and lower-extremity amputation.

## Parameters and templates

The source module exposes only `diabetes_baseline`. The parameter registry declares the four disability weights below as module-owned parameters that are not editable in a scenario; each places its value on its weight node in `model.json`. Clinical intervention parameters and comparison values live in separate intervention repositories.

## Data and evidence

[`model.json`](model.json) is the executable graph. The [module contract](interface/diabetes-epidemiology-core.module.contract.v1.json) defines composition and runtime semantics. The opening-state recipe defines baseline initialization. The contract identifies Spectrum/OneHealth diabetes material and the current module cleanup as default provenance.

Routine care is declared in [`resource_requirements.json`](resource_requirements.json) as `routine_care_services`: each entry names a service by the module and block that declare it, `ncd-diabetes-stdglyccontrol` (`d3-standard-glycaemic-control`), `ncd-diabetes-retinopathyscrn` (`d2-retinopathy-screening`), `ncd-diabetes-nephropathyscr` (`d5-nephropathy-screening-follow-up`) and `ncd-diabetes-neuropathyscr` (`d1-foot-care`), with the disease states it is delivered to. This module does not copy the services' resources. The compiler takes the quantities, cost items, population in need and baseline coverage from each service's own declaration and costs the service at its baseline coverage in both scenarios. When the owning intervention is selected, its block also costs the service for the population the intervention reaches, at baseline coverage in the baseline scenario and at the target coverage in the comparison; routine care of the disease states continues beside it from the same declaration.

Staff time is priced from one shared salary item per staff type, `cost-item.workforce-salary.<type>`: `nurse`, `generalist-primary-care-doctor`, `specialist`, `therapist` and `counsellor`. A type is the same item in every module that uses it, so a generalist minute costs the same everywhere, and each type can be edited on its own: a specialist can be paid differently from a generalist doctor. The item is an annual salary. Its default is the country's WHO-CHOICE annual salary from the data service for the type's cadre (skill level 4 for doctors and specialists, 3 for nurses and therapists, 2 for counsellors); the cadre is the default source, not the item. A staff minute costs that salary divided by 126,720 working minutes a year (8 hours, 22 days a month, 12 months). The data service uses this convention for its WHO-CHOICE cost per minute, and every clinical staff cost has used it. The per-minute values in the resource graphs are defaults for use without a country. Tobacco policy programme roles are separate staff types, since none is the same job as a clinical one.

### Disability weights

A model state that holds one GBD health state takes that state's weight. A state that combines several GBD sequelae takes the GBD 2019 global average for those sequelae, which is the cause's years lived with disability divided by its prevalent cases. That average weights each severity level by GBD's own severity distribution, which GBD models by location and does not publish as a table. A person with two modelled conditions takes GBD's multiplicative combination, 1 − (1 − w1)(1 − w2).

| Model state | Old | GBD weight | GBD health states and mapping |
|---|---|---|---|
| Diabetes without a modelled complication (`Diabetes`, node `lrso7mga`) | 0.031 | 0.080 | Uncomplicated diabetes 0.049, diabetic neuropathy 0.133 and neuropathy with foot ulcer, which the model does not separate. GBD 2019 global average for type 2 diabetes: 35.15 million YLDs over 437.9 million cases. The average also contains the small share of YLDs from vision loss and amputation, which the model holds in their own states. |
| Diabetic retinopathy (`DiabeticRetinopathy`, node `ls9rs1ih`) | 0.338 | 0.134 | Vision loss due to diabetes: moderate 0.031, severe 0.184, blindness 0.187. GBD publishes no global severity split for diabetic vision loss, so the three levels have equal shares. |
| Lower-extremity amputation (`LowerExtrmAmpt`, node `ls9rvbes`) | 0.164 | 0.225 | GBD sequelae diabetic neuropathy with treated amputation (0.17) and with untreated amputation (0.28), each a combination of neuropathy (0.133) and one-leg amputation. GBD splits treated and untreated amputation by health-system access and publishes no split, so the two have equal shares. |
| Diabetic nephropathy (`DiabeticNephropathy`, node `ls9y3aia`) | 0.338 | 0.013 | Chronic kidney disease due to type 2 diabetes: stage III 0 without anaemia and 0.004–0.149 with it, stage IV 0.104, stage V 0.569, dialysis 0.571, transplant 0.024. GBD 2019 global average: 1.69 million YLDs over 129.6 million cases. Most cases are stage III without anaemia, which carries no weight. |

Until October 2026 the module used 0.031 for diabetes, 0.338 for retinopathy, 0.164 for amputation and 0.338 for nephropathy, from the Spectrum/OneHealth disease association file without a cited source. Sources: GBD 2019 Diseases and Injuries Collaborators, *Lancet* 2020;396:1204–22, appendix 1 (the disability-weight table in each cause section) and appendix 2, table S18 (global prevalence and years lived with disability, 2019); the IHME GBD 2019 disability-weights table and its sequela-to-health-state list, which gives the combined amputation weights; Salomon JA et al., *Lancet Glob Health* 2015;3:e712–23, where the weights were estimated.

## Relationships

The demographic module supplies canonical population and background mortality. `opening-state-reconciliation` initializes the disease partition. Separate repositories own standard and intensive glycaemic control, retinopathy screening, nephropathy screening and blood-pressure control, and comprehensive foot care.

Routine care references the standard glycaemic control, retinopathy screening, nephropathy screening and follow-up, and comprehensive foot care services declared by those repositories. The services are applied to the diabetes episode and complication states without changing disease transitions. The intervention graph slices count their reached population from the diabetes episode state, the population whose complication transitions their effects reduce, while routine care counts people in the diabetes episode and complication states.

## Assumptions and limitations

The disease-free state is a local residual, not an additional population. The model is a marginal diabetes estimate and must remain reconciled to the canonical population. Intervention graph slices modify complication incidence but do not model detailed screening, diagnosis, adherence, or treatment pathways.

## Status

The disease graph, compiler contract, baseline template, opening-state recipe, intervention extension points, and routine-care declarations are implemented. The source graph requires compiler lowering and is not a standalone national model.
