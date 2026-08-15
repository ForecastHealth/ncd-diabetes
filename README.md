---
title: Diabetes epidemiology
module_identifier: ncd-diabetes
owner: Forecast Health
last_updated: 2026-08-15
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

Diabetes is a marginal disease process. Its living-state partition contains a derived disease-free residual, the diabetes episode state, and three complication states. Observed prevalence informs the opening disease state. During each model year, incidence and complication transitions compete in a continuous-hazard phase based on the phase-opening balances. Background mortality is then applied sequentially to survivors.

Risk-factor modules can modify diabetes incidence. Clinical components can reduce the incidence of retinopathy, nephropathy, and lower-extremity amputation through disease-owned extension points. Post-run metric modules calculate healthy years and disease burden from the raw state and mortality outputs.

## Inputs and outputs

Required inputs are the reconciled opening population at risk and background mortality rates. An incidence modifier is optional. The module publishes diabetes episode population, diabetes incidence, diabetes-specific mortality, and populations with retinopathy, nephropathy, and lower-extremity amputation.

## Parameters and templates

The source module exposes only `diabetes_baseline`. The disease parameter registry is empty because clinical intervention parameters and comparison values live in separate intervention repositories.

## Data and evidence

[`model.json`](model.json) is the executable graph. The [module contract](interface/diabetes-epidemiology-core.module.contract.v1.json) defines composition and runtime semantics. The opening-state recipe defines baseline initialization. The contract identifies Spectrum/OneHealth diabetes material and the current module cleanup as default provenance.

## Relationships

The demographic module supplies canonical population and background mortality. `opening-state-reconciliation` initializes the disease partition. Separate repositories own standard and intensive glycaemic control, retinopathy screening, nephropathy screening and blood-pressure control, and comprehensive foot care.

The routine-care declaration uses the preserved Spectrum/OneHealth-derived resource structures for standard glycaemic control, retinopathy screening, nephropathy screening and follow-up, and comprehensive foot care. These services are applied to the full living diabetes-state partition without changing disease transitions.

## Assumptions and limitations

The disease-free state is a local residual, not an additional population. The model is a marginal diabetes estimate and must remain reconciled to the canonical population. Intervention graph slices modify complication incidence but do not model detailed screening, diagnosis, adherence, or treatment pathways.

## Status

The disease graph, compiler contract, baseline template, opening-state recipe, intervention extension points, and routine-care declarations are implemented. The source graph requires compiler lowering and is not a standalone national model.
