---
title: Diabetes epidemiology
module_identifier: ncd-diabetes
owner: Forecast Health
last_updated: 2026-10-10
status: Executable disease module, calibrated to WHO deaths and run through the client's normal analysis path
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

This module models type 2 diabetes in adults: new cases, three complications (diabetic retinopathy, diabetic nephropathy and lower-extremity amputation), the disability they cause and the deaths among people with diabetes. It is the disease that the clinical diabetes interventions act on, and one of the diseases that tobacco, alcohol, physical inactivity, diet, sugar-sweetened beverages and breastfeeding reach through the risk-factor modules.

The client offers four diabetes interventions. Each has a code from the WHO list of NCD best buys and other recommended interventions (the "Appendix 3" codes), and each code brings in one or two intervention modules:

| Code | Intervention | Modules it brings in | What it changes |
| --- | --- | --- | --- |
| D1 | Foot care to prevent amputation | `ncd-diabetes-neuropathyscr` | amputation incidence |
| D2 | Retinopathy screening and laser photocoagulation | `ncd-diabetes-retinopathyscrn` | retinopathy incidence |
| D3 | Glycaemic control, with home glucose monitoring for people on insulin | `ncd-diabetes-stdglyccontrol` (standard control, population in need 0.9) and `ncd-diabetes-intsvglyccontrol` (intensive control, population in need 0.1) | retinopathy, nephropathy and amputation incidence |
| D5 | Screening for proteinuria and treatment with an angiotensin-converting enzyme (ACE) inhibitor | `ncd-diabetes-nephropathyscr` | nephropathy incidence |

D3 is a package: selecting it compiles both glycaemic-control modules together under the selection id `ncd-diabetes-d3`, and their parameters are owned by that id. The other diabetes codes in the catalogue registry (D6 to D10) have no module and are not offered.

## Method

### States and transitions

The model follows each sex and single year of age from 0 to 100. Its living states are a disease-free residual, diabetes without a modelled complication (the diabetes episode state, `DiabetesEpsd`) and the three complication states. The states are mutually exclusive: a person enters a complication state from the episode state and leaves the episode state when they do. Diabetes is modelled as a marginal disease, so the disease-free residual is not a separate population. At each model-year opening it is set to the canonical population from the demographic module minus the people in the four diabetes states, by age and sex.

During the year, new diabetes cases and the three complication transitions compete in one continuous-hazard phase that starts from the opening balances. Deaths then apply to each diabetes state at that state's fatality rate. Retinopathy, nephropathy and amputation are entered only from the episode state; the model has no transitions between complication states and no remission.

### Calibration to observed deaths

Before the first model year, the shared `opening-state-reconciliation` preflight fits the model to observed deaths and prevalence, as declared in the [opening-state contract](data/diabetes-opening-state.contract.v3.json). Baseline and comparison use one result, so they start from the same state.

- **Deaths.** The four diabetes-state fatality rates (diabetes, retinopathy, amputation and nephropathy) are scaled by one common factor for each sex and single age, so that the opening year's deaths in the diabetes states equal the WHO Global Health Estimates (GHE) 2021 diabetes death rates applied to the opening population. The target uses seven GHE age bands (0-4, 5-14, 15-29, 30-49, 50-59, 60-69, 70 and over); within each band the deaths are spread by the Global Burden of Disease (GBD) age pattern of diabetes deaths. One common factor keeps the source ordering of the four fatality rates. Each scaled rate is capped at 3 a year. Deaths in the nephropathy state count as diabetes deaths.
- **Opening complications.** Observed diabetes prevalence is divided among the episode state and the three complication states in the shares that a cohort reaches at each age under the fitted rates, instead of opening every complication state empty.
- **Other-cause deaths.** People with diabetes also die of causes other than diabetes more often than people without it. Their other-cause death rate is the partition's other-cause rate (all-cause deaths less diabetes deaths) times a relative mortality fitted for each of 12 age bands, between 1 and 4, so that the year's transitions and deaths carry observed prevalence forward unchanged. These deaths are not counted as diabetes deaths.

### Onset age

This is a type 2 diabetes model. Its GBD input covers all diabetes, so values below 15 (2e-5 to 3e-4 a year) are mostly type 1. Diabetes incidence and opening prevalence are 0 below 15: the incidence node (`nLErvery`) and the opening-prevalence source ask the data service for `min_age` 15, and the registry declares it as `minimum_onset_age`. The calibration reads the same incidence and prevalence.

### Risk factors that change diabetes incidence

Risk-factor modules change diabetes incidence through one input, `incidence_modifier`, which multiplies the incidence of new diabetes. `risk-factor-reconciliation` builds it for each scenario, sex, age and year from every selected risk factor, so a selection reaches diabetes once however many risk factors it contains. The modifier is

    M = [(1 + Σ e_scenario) / (1 + Σ e_baseline)] × M_BMI × M_breastfeeding

where each `e` is the excess risk of one risk factor: the extra diabetes incidence its exposure adds, as a share of the incidence the population would have without it. A risk factor that is not selected enters at its baseline value, so it does not change the ratio. The routes are:

| Risk factor | Interventions | How it reaches diabetes | Evidence (owning module) |
| --- | --- | --- | --- |
| Tobacco | T1 to T7 and the cessation services | excess risk of current and former smokers in the ratio | current smokers: Spectrum/OneHealth 6.31 relative risks by sex and age; former smokers: 1.54 for the first 5 years after quitting, 1.18 at 5 to 10 years and 1.11 after, relative to never smokers (Pan et al.) (`risk-factor-tobacco`) |
| Alcohol | A1, A2, A3, A5 | excess risk of hazardous drinking in the ratio | Spectrum/OneHealth 6.31 relative risks (`risk-factor-alcohol`) |
| Physical inactivity | P1, P2 | excess risk in the ratio, from age 25 | Spectrum/OneHealth 6.31 relative risks (`risk-factor-physical-inactivity`) |
| Body-mass index (BMI) | the four healthy-diet policies (U1 to U4) through free sugars and energy; the sugar-sweetened beverage tax (U6); food-marketing restriction for children (U7); breastfeeding promotion (U9) through child BMI | `M_BMI`: the change in adult BMI from a reference that baseline and comparison share, reaching full effect over 1 year along each cohort, raised to the relative risk per 1 kg/m² | Singh et al. 2013 age-specific relative risks, diabetes 3.07 per 5 kg/m² at ages 25 to 44 falling to 1.38 from 85, 1 below 25 (`risk-factor-obesity`) |
| Sugar-sweetened beverages, direct | U6 | multiplied into `M_BMI`: relative risk 1.13 per 250 mL a day of change in adults' intake, adjusted for adiposity so it adds to the BMI route without counting weight twice; editable from 1 (route off) to 2, with 1.06 and 1.27 as the sensitivity values | Imamura et al. 2015 (`risk-factor-ssb`) |
| Breastfeeding, maternal | U9 | `M_breastfeeding`: women's incidence falls with the change in their months of breastfeeding, relative risk 0.91 per 12 months within 15 years of a birth and 0.96 after; 1 for men | Aune et al. 2014; Stuebe et al. 2005 (`risk-factor-breastfeeding`) |

Because `M` is a ratio of scenario to baseline risk, the observed incidence, which already reflects today's risk factors, is not counted twice.

### Clinical interventions

The intervention modules each add a component to this graph. A component reaches the people in the diabetes episode state, `DiabetesEpsd`, times its population in need (the share of people with diabetes eligible for it). Its coverage moves from the country's current (baseline) coverage to the scenario's target. For complication `c`, the incidence out of the episode state is multiplied by

    1 − Σ_k  impact_k,c × population in need_k × (coverage_k,t − baseline coverage_k)

where `k` runs over the selected interventions that reduce `c` and `impact` is the proportional reduction in that complication's incidence among people covered. Only coverage above the current level has an effect, so the baseline scenario, which holds coverage at the current level, has none. The effects of several interventions on one complication add. No intervention changes the incidence of diabetes or the fatality of a diabetes state directly; deaths and disability fall because fewer people reach a complication state. The intervention READMEs give each module's values.

## Inputs and outputs

Required inputs are the reconciled opening population at risk and background mortality rates from the demographic module. The risk-factor incidence modifier is optional; without it incidence is unchanged. The module publishes the diabetes episode population, new diabetes cases, diabetes deaths and the populations with retinopathy, nephropathy and amputation, by sex, age and year. The Impact page shows people living with diabetes and with complications, deaths from diabetes and its complications, and healthy years.

## Parameters and templates

The module has one baseline template, `diabetes_baseline`, which changes nothing. Its parameter registry ([`parameters/registry.v1.json`](parameters/registry.v1.json)) declares five module-owned parameters, none editable on the Scenarios page:

| Parameter | Value | Meaning |
| --- | --- | --- |
| `diabetes_disability_weight` | 0.080 | disability weight of diabetes without a modelled complication |
| `diabetic_retinopathy_disability_weight` | 0.134 | disability weight of retinopathy |
| `lower_extremity_amputation_disability_weight` | 0.225 | disability weight of amputation |
| `diabetic_nephropathy_disability_weight` | 0.013 | disability weight of nephropathy |
| `minimum_onset_age` | 15 | first age with diabetes incidence and prevalence |

Incidence, complication and fatality rates come from the data service for the selected country (see Data and evidence). Intervention parameters and their baseline and comparison values belong to the intervention modules. Routine-care coverage is editable on the Diabetes card of the Scenarios page (see Routine care).

## Data and evidence

[`model.json`](model.json) is the executable graph. The [module contract](interface/diabetes-epidemiology-core.module.contract.v1.json) declares its inputs, outputs and composition.

### Country data

| Input | Source | Data service request |
| --- | --- | --- |
| Diabetes incidence, ages 15 and over | GBD, as packaged in the Spectrum/OneHealth NCD defaults | `fhdb.epidemiology`, disease `Diabetes`, measure `incidence`, `min_age` 15 |
| Diabetes prevalence, ages 15 and over (opening state) | GBD, as above | measure `prevalence`, `min_age` 15 |
| Diabetes fatality and the GBD age pattern of deaths | GBD, as above | disease `Diabetes`, measure `deaths` |
| Nephropathy fatality | GBD chronic kidney disease deaths, as above | disease `CKD`, measure `deaths` |
| Retinopathy, nephropathy and amputation incidence; retinopathy and amputation fatality | Spectrum/OneHealth diabetes disease association file | `diabetes.get_observation` |
| Death target | WHO Global Health Estimates 2021, diabetes deaths per person by sex and age band | `who_ghe.cause_death_rate`, cause `diabetes` |
| All-cause death probability | the platform's demographic data | `fhdb.mortality` |
| Years-of-life-lost weights | GBD reference life table, remaining life expectancy by age, 2019 values, the same for both sexes | `fhdb.yll_weights` |

The complication incidence and fatality rates are the Spectrum/OneHealth values; the primary studies behind them are not recorded.

### Disability weights

A model state that holds one GBD health state takes that state's weight. A state that combines several GBD sequelae takes the GBD 2019 global average for those sequelae, which is the cause's years lived with disability (YLDs) divided by its prevalent cases. That average weights each severity level by GBD's own severity distribution, which GBD models by location and does not publish as a table. A person with two modelled conditions takes GBD's multiplicative combination, 1 − (1 − w1)(1 − w2).

| Model state | GBD weight | GBD health states and mapping |
|---|---|---|
| Diabetes without a modelled complication (`Diabetes`, node `lrso7mga`) | 0.080 | Uncomplicated diabetes 0.049, diabetic neuropathy 0.133 and neuropathy with foot ulcer, which the model does not separate. GBD 2019 global average for type 2 diabetes: 35.15 million YLDs over 437.9 million cases. The average also contains the small share of YLDs from vision loss and amputation, which the model holds in their own states. |
| Diabetic retinopathy (`DiabeticRetinopathy`, node `ls9rs1ih`) | 0.134 | Vision loss due to diabetes: moderate 0.031, severe 0.184, blindness 0.187. GBD publishes no global severity split for diabetic vision loss, so the three levels have equal shares. |
| Lower-extremity amputation (`LowerExtrmAmpt`, node `ls9rvbes`) | 0.225 | GBD sequelae diabetic neuropathy with treated amputation (0.17) and with untreated amputation (0.28), each a combination of neuropathy (0.133) and one-leg amputation. GBD splits treated and untreated amputation by health-system access and publishes no split, so the two have equal shares. |
| Diabetic nephropathy (`DiabeticNephropathy`, node `ls9y3aia`) | 0.013 | Chronic kidney disease due to type 2 diabetes: stage III 0 without anaemia and 0.004–0.149 with it, stage IV 0.104, stage V 0.569, dialysis 0.571, transplant 0.024. GBD 2019 global average: 1.69 million YLDs over 129.6 million cases. Most cases are stage III without anaemia, which carries no weight. |

Because the living states are mutually exclusive, a person carries one of these weights: a person in a complication state does not also carry the episode weight. The weights replace values from the Spectrum/OneHealth disease association file that had no cited source (0.031 for diabetes, 0.338 for retinopathy, 0.164 for amputation and 0.338 for nephropathy). Sources: GBD 2019 Diseases and Injuries Collaborators, *Lancet* 2020;396:1204–22, appendix 1 (the disability-weight table in each cause section) and appendix 2, table S18 (global prevalence and years lived with disability, 2019); the IHME GBD 2019 disability-weights table and its sequela-to-health-state list, which gives the combined amputation weights; Salomon JA et al., *Lancet Glob Health* 2015;3:e712–23, where the weights were estimated.

### Routine care

Routine care is the care people with diabetes already receive. It is costed in both scenarios at each service's current coverage, so it appears in total health-system costs but not in the difference between scenarios. [`resource_requirements.json`](resource_requirements.json) names four services by the module and resource block that declare them, and the disease states each is delivered to (the episode state and all three complication states):

| Service | Declared by | Block |
| --- | --- | --- |
| Standard glycaemic control | `ncd-diabetes-stdglyccontrol` | `d3-standard-glycaemic-control` |
| Retinopathy screening and laser photocoagulation | `ncd-diabetes-retinopathyscrn` | `d2-retinopathy-screening` |
| Nephropathy screening and renal-protection follow-up | `ncd-diabetes-nephropathyscr` | `d5-nephropathy-screening-follow-up` |
| Foot care | `ncd-diabetes-neuropathyscr` | `d1-foot-care` |

This module does not copy the services' resources. For each service the compiler takes the quantities, cost items, population in need and current coverage from the declaring module, and costs people in the four diabetes states times the population in need times the current coverage. Intensive glycaemic control is not routine care; it is costed only when D3 is selected. When an intervention is selected, its own block is also costed for the people it reaches, at current coverage in the baseline and at target coverage in the comparison; routine care of the disease states continues beside it from the same declaration.

Staff time is priced from one shared salary item per staff type, `cost-item.workforce-salary.<type>` (`nurse`, `generalist-primary-care-doctor`, `specialist`, `therapist`, `counsellor`). A type is the same item in every module that uses it and can be edited on its own. The item is an annual salary whose default is the country's WHO-CHOICE annual salary for the type's skill level (4 for doctors and specialists, 3 for nurses and therapists, 2 for counsellors). A staff minute costs that salary divided by 126,720 working minutes a year (8 hours, 22 days a month, 12 months), the convention the data service uses for its WHO-CHOICE cost per minute.

### Validation

The opening year's diabetes deaths equal the WHO GHE 2021 target in each sex and age band by construction. In the client's Indonesia check when the calibration was introduced (before the onset age was set to 15), modelled diabetes deaths in 2025 fell from 138,960 (uncalibrated GBD/Spectrum fatality) to 63,646 (the GHE 2021 level), and age-standardised prevalence from 2025 to 2050 changed by 0% instead of rising 4%. No result has been compared with an external estimate of the effect of a diabetes intervention.

## Relationships

The demographic module supplies the canonical population and background mortality. `opening-state-reconciliation` initialises the diabetes states and applies the calibration. `risk-factor-reconciliation` supplies the incidence modifier. The intervention modules listed under Purpose own the clinical effects and their resources, and the compiler inserts their components into this graph. The metric modules (`metric-health-burden`, `metric-hyl`) calculate disability-adjusted life years and healthy years from the states, deaths and disability weights this module publishes.

## Assumptions and limitations

- **Complications are simplified.** Neuropathy and foot ulcer are not separate states; their disability is inside the episode weight. A person can have only one complication, and there is no progression from one complication to another or remission from any of them. The consequence is that people with several complications carry less disability than they would in reality.
- **Type 1 diabetes in adults remains.** Incidence and prevalence are set to 0 below 15, but from 15 the GBD input still covers all diabetes, so adults with type 1 diabetes are in the model and the interventions reach them.
- **Complication rates have no traced primary source.** Complication incidence and fatality are Spectrum/OneHealth values. The calibration fixes total diabetes deaths but not how they divide among the complication states.
- **Nephropathy deaths are diabetes deaths.** Deaths in the nephropathy state count towards the WHO diabetes death target.
- **Other-cause relative mortality is a fit, not a measurement.** It is chosen so that prevalence stays at its observed level; it is bounded between 1 and 4, and where the bound binds prevalence drifts.
- **Equal-share assumptions in the disability weights.** Retinopathy and amputation weights assume equal shares of the GBD severity levels, because GBD publishes no global split.
- **Intervention effects act only on complications.** Interventions do not lower diabetes incidence or the fatality of diabetes without complications, and they do not model screening yield, diagnosis, adherence or treatment pathways.
- **Routine care can be counted twice in each scenario's gross cost.** When a diabetes intervention is selected, people in the episode state who already receive that service at current coverage are costed both as routine care and in the intervention's block, in both scenarios. The difference between scenarios is unaffected, but each scenario's total health-system cost is overstated by that amount.
- **One marginal model.** The disease-free state is a local residual, not an additional population, so the model must stay reconciled to the canonical population.

## Status

The disease graph, module contract, baseline template, opening-state calibration, intervention extension points, risk-factor incidence modifier and routine-care declarations are implemented and run through the client's normal analysis path. The graph needs compiler lowering and is not a standalone national model.
