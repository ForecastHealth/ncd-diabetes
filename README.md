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
- [Inputs and outputs](#inputs-and-outputs)
- [Method](#method)
- [Routine care](#routine-care)
- [Parameters](#parameters)
- [Data and evidence](#data-and-evidence)
- [Validation](#validation)
- [Assumptions and limitations](#assumptions-and-limitations)
- [Relationships](#relationships)
- [Status](#status)

## Purpose

This module models type 2 diabetes in adults. It projects new cases, three complications (diabetic retinopathy, diabetic nephropathy and lower-extremity amputation), the disability they cause and the deaths among people with diabetes. Retinopathy is damage to the retina and here stands for all vision loss due to diabetes. Nephropathy is kidney disease caused by diabetes.

The clinical diabetes interventions act on this module. Tobacco, alcohol, physical inactivity, diet, sugar-sweetened beverage and breastfeeding interventions also reach it through the risk-factor modules.

The client offers four diabetes interventions. Each has a code from Appendix 3, the World Health Organization (WHO) list of noncommunicable disease (NCD) best buys and other recommended interventions. Each code brings in one or two intervention modules:

| Code | Intervention | Modules it brings in | What it changes |
| --- | --- | --- | --- |
| D1 | Foot care to prevent amputation | `ncd-diabetes-neuropathyscr` | amputation incidence |
| D2 | Retinopathy screening and laser photocoagulation | `ncd-diabetes-retinopathyscrn` | retinopathy incidence |
| D3 | Glycaemic control, with home glucose monitoring for people on insulin | `ncd-diabetes-stdglyccontrol` (standard control, population in need 0.9) and `ncd-diabetes-intsvglyccontrol` (intensive control, population in need 0.1) | retinopathy, nephropathy and amputation incidence |
| D5 | Screening for proteinuria and treatment with an angiotensin-converting enzyme (ACE) inhibitor | `ncd-diabetes-nephropathyscr` | nephropathy incidence |

The population in need is the share of people with diabetes eligible for a service. D3 is a package: selecting it compiles both glycaemic-control modules together under the selection id `ncd-diabetes-d3`, and their parameters are owned by that id. The other diabetes codes in the catalogue registry (D6 to D10) have no module and are not offered.

## Inputs and outputs

The module requires two inputs from the demographic module: the reconciled opening population at risk and the background mortality rates, by sex and single year of age. It accepts one optional input, the risk-factor incidence modifier, a multiplier on diabetes incidence. Without it, incidence is unchanged.

It publishes, by sex, single year of age and year, the number of people in the diabetes episode state, new diabetes cases, diabetes deaths and the numbers of people with retinopathy, nephropathy and amputation. All are counts of people. The Impact page shows people living with diabetes and with complications, deaths from diabetes and its complications, and healthy years.

## Method

### States and transitions

The model follows each sex and single year of age from 0 to 100. Its living states are:

- a disease-free residual;
- the diabetes episode state (`DiabetesEpsd`), meaning diabetes without a modelled complication;
- three complication states: retinopathy, nephropathy and lower-extremity amputation.

The states are mutually exclusive. A person enters a complication state from the episode state and leaves the episode state when they do.

Diabetes is modelled as a marginal disease, so the disease-free residual is not a separate population. At each model-year opening it is set to the canonical population from the demographic module minus the people in the four diabetes states, by age and sex.

During the year, new diabetes cases and the three complication transitions compete in one continuous-hazard phase that starts from the opening balances. Deaths then apply to each diabetes state at that state's fatality rate, the annual rate of death from diabetes among people in the state. Retinopathy, nephropathy and amputation are entered only from the episode state. The model has no transitions between complication states and no remission.

### Onset age

This is a type 2 diabetes model. Its input from the Global Burden of Disease (GBD) study covers all diabetes, so the values below age 15 (2e-5 to 3e-4 a year) are mostly type 1 diabetes. Diabetes incidence and opening prevalence are therefore 0 below 15. The incidence node (`nLErvery`) and the opening-prevalence source ask the data service for `min_age` 15, and the parameter registry declares it as `minimum_onset_age`. The calibration reads the same incidence and prevalence.

### Calibration to observed deaths

Before the first model year, the shared `opening-state-reconciliation` preflight fits the model to observed deaths and prevalence, as declared in the opening-state contract (`data/diabetes-opening-state.contract.v3.json`). Baseline and comparison use one result, so they start from the same state. The fit has three parts.

Deaths. The death target is the WHO Global Health Estimates (GHE) 2021 diabetes death rates applied to the opening population. The GHE rates come in seven age bands (0-4, 5-14, 15-29, 30-49, 50-59, 60-69, 70 and over). Within each band, the target deaths are spread across single ages by the GBD age pattern of diabetes deaths. The four diabetes-state fatality rates (diabetes, retinopathy, amputation and nephropathy) are then scaled by one common factor for each sex and single age:

$$
f^{*}_{s,a,j} = \min\left(\lambda_{s,a}\, f_{s,a,j},\ 3\right)
$$

where $f_{s,a,j}$ is the source fatality rate of state $j$ for sex $s$ and age $a$ (deaths per person per year), $\lambda_{s,a}$ is the common scaling factor (dimensionless), chosen so that the opening year's deaths in the diabetes states equal the target, and $f^{*}_{s,a,j}$ is the fitted rate, capped at 3 a year. One common factor keeps the source ordering of the four fatality rates. Deaths in the nephropathy state count as diabetes deaths.

Opening complications. Observed diabetes prevalence is divided among the episode state and the three complication states in the shares that a cohort reaches at each age under the fitted rates. No complication state opens empty.

Other-cause deaths. People with diabetes die of causes other than diabetes more often than people without it. Their other-cause death rate is

$$
\mu^{\mathrm{dm}}_{s,a} = \rho_{s,b(a)}\, \mu^{\mathrm{oc}}_{s,a}, \qquad 1 \le \rho_{s,b(a)} \le 4
$$

where $\mu^{\mathrm{oc}}_{s,a}$ is the partition's other-cause death rate (all-cause deaths less diabetes deaths, per person per year), $b(a)$ is the age band containing age $a$, and $\rho_{s,b}$ is the relative mortality for that band (dimensionless). There are 12 age bands. Each $\rho$ is fitted so that the year's transitions and deaths carry observed prevalence forward unchanged. These deaths are not counted as diabetes deaths.

### Risk factors that change diabetes incidence

Risk-factor modules change diabetes incidence through one input, `incidence_modifier`, which multiplies the incidence of new diabetes. `risk-factor-reconciliation` builds it for each scenario, sex, age and year from every selected risk factor, so a selection reaches diabetes once however many risk factors it contains. The modifier is

$$
M = \frac{1 + \sum_r e_r^{\mathrm{scen}}}{1 + \sum_r e_r^{\mathrm{base}}} \; M_{\mathrm{BMI}} \; M_{\mathrm{bf}}
$$

where $e_r$ is the excess risk of risk factor $r$: the extra diabetes incidence its exposure adds, as a share of the incidence the population would have without it. The superscripts mark the scenario being run and the baseline. $M_{\mathrm{BMI}}$ is the multiplier from body-mass index (BMI) and the direct effect of sugar-sweetened beverages, and $M_{\mathrm{bf}}$ is the multiplier from breastfeeding. $M$ and both multipliers are dimensionless. A risk factor that is not selected enters at its baseline value, so it does not change the ratio. Because $M$ is a ratio of scenario risk to baseline risk, the observed incidence, which already reflects current risk factors, is not counted twice.

The BMI multiplier is

$$
M_{\mathrm{BMI}} = \mathrm{RR}_a^{\,\Delta B} \; r^{\,\Delta Q / s}
$$

where $\Delta B$ is the change in adult BMI (kg/m²) from a reference that baseline and comparison share, reaching full effect over 1 year along each cohort, and $\mathrm{RR}_a$ is the relative risk (RR) of diabetes per 1 kg/m² at age $a$. The second factor is the direct route of sugar-sweetened beverages: $\Delta Q$ is the change in adults' intake (litres a day), $s$ is a serving of 0.25 litres, and $r$ is the RR per daily serving. The default for $r$ is 1.13, adjusted for adiposity so it adds to the BMI route without counting weight twice. It is editable from 1 (route off) to 2, with 1.06 and 1.27 as the sensitivity values.

The breastfeeding multiplier is

$$
M_{\mathrm{bf}} = R_{12}^{\,\Delta m_{\mathrm{recent}}/12} \; R_{12,\mathrm{late}}^{\,\Delta m_{\mathrm{earlier}}/12}
$$

where $\Delta m_{\mathrm{recent}}$ is the change in a woman's months of breastfeeding for births within the last 15 years, $\Delta m_{\mathrm{earlier}}$ the change for earlier births, $R_{12}$ the RR of diabetes per 12 months of breastfeeding within 15 years of a birth (0.91), and $R_{12,\mathrm{late}}$ the RR per 12 months after that (0.96). For men $M_{\mathrm{bf}} = 1$.

The routes, and the modules that own their evidence, are:

| Risk factor | Interventions | How it reaches diabetes | Evidence (owning module) |
| --- | --- | --- | --- |
| Tobacco | T1 to T7 and the cessation services | excess risk of current and former smokers in the ratio | current smokers: Spectrum/OneHealth 6.31 RRs by sex and age; former smokers: 1.54 for the first 5 years after quitting, 1.18 at 5 to 10 years and 1.11 after, relative to never smokers (Pan et al.) (`risk-factor-tobacco`) |
| Alcohol | A1, A2, A3, A5 | excess risk of hazardous drinking in the ratio | Spectrum/OneHealth 6.31 RRs (`risk-factor-alcohol`) |
| Physical inactivity | P1, P2 | excess risk in the ratio, from age 25 | Spectrum/OneHealth 6.31 RRs (`risk-factor-physical-inactivity`) |
| BMI | the four healthy-diet policies (U1 to U4) through free sugars and energy; the sugar-sweetened beverage tax (U6); food-marketing restriction for children (U7); breastfeeding promotion (U9) through child BMI | $\mathrm{RR}_a^{\,\Delta B}$ in $M_{\mathrm{BMI}}$ | Singh et al. 2013 age-specific RRs: diabetes 3.07 per 5 kg/m² at ages 25 to 44, falling to 1.38 from 85, and 1 below 25 (`risk-factor-obesity`) |
| Sugar-sweetened beverages, direct | U6 | $r^{\,\Delta Q / s}$ in $M_{\mathrm{BMI}}$ | Imamura et al. 2015 (`risk-factor-ssb`) |
| Breastfeeding, maternal | U9 | $M_{\mathrm{bf}}$ | Aune et al. 2014; Stuebe et al. 2005 (`risk-factor-breastfeeding`) |

Spectrum is the Avenir Health suite of planning models, and its NCD module is used with the OneHealth Tool, the WHO-supported tool for costing national health plans. Version 6.31 is the release whose RRs these modules use.

### Clinical interventions

Each intervention module adds a component to this graph. A component reaches the people in the diabetes episode state times its population in need. Its coverage, the share of that population who receive the service, moves from the country's current coverage to the scenario's target. For complication $k$, the hazard of moving from the episode state to $k$ in year $t$ is multiplied by

$$
1 - \sum_j I_{j,k}\, n_j \left(c_{j,t} - c_{j,0}\right)
$$

where $j$ runs over the selected interventions that reduce complication $k$, $I_{j,k}$ is the impact (the proportional reduction in the incidence of $k$ among people covered by $j$), $n_j$ is the population in need, $c_{j,t}$ is coverage in year $t$ and $c_{j,0}$ is current coverage. All are proportions. Only coverage above the current level has an effect, so the baseline scenario, which holds coverage at the current level, has none. The effects of several interventions on one complication add.

No intervention changes the incidence of diabetes or the fatality of a diabetes state directly. Deaths and disability fall because fewer people reach a complication state. Each intervention's README gives its values.

### Disability

Each living diabetes state carries a disability weight, the fraction of a year of healthy life lost for each year lived in that state (0 is full health, 1 is equivalent to death). The metric modules use these weights to calculate years lived with disability (YLDs). The defaults are 0.080 for the episode state, 0.134 for retinopathy, 0.225 for amputation and 0.013 for nephropathy. Each is the GBD 2019 weight, or average of weights, for the GBD health states that the model state contains.

Because the living states are mutually exclusive, a person carries one of these weights. A person in a complication state does not also carry the episode weight. A person with two modelled conditions, one from this module and one from another, takes GBD's multiplicative combination

$$
w = 1 - (1 - w_1)(1 - w_2)
$$

where $w_1$ and $w_2$ are the two disability weights and $w$ is the combined weight.

## Routine care

Routine care is the care people with diabetes already receive. It is costed in both scenarios at each service's current coverage, so it appears in total health-system costs but not in the difference between scenarios. `resource_requirements.json` names four services by the module and resource block that declare them. Each is delivered to the episode state and all three complication states.

| Service | Declared by | Block |
| --- | --- | --- |
| Standard glycaemic control | `ncd-diabetes-stdglyccontrol` | `d3-standard-glycaemic-control` |
| Retinopathy screening and laser photocoagulation | `ncd-diabetes-retinopathyscrn` | `d2-retinopathy-screening` |
| Nephropathy screening and renal-protection follow-up | `ncd-diabetes-nephropathyscr` | `d5-nephropathy-screening-follow-up` |
| Foot care | `ncd-diabetes-neuropathyscr` | `d1-foot-care` |

This module does not copy the services' resources. For each service the compiler, the part of the platform that assembles the selected modules into one model, takes the quantities, cost items, population in need and current coverage from the declaring module. It costs the people in the four diabetes states times the population in need times the current coverage. Intensive glycaemic control is not routine care. It is costed only when D3 is selected. When an intervention is selected, its own block is also costed for the people it reaches, at current coverage in the baseline and at target coverage in the comparison. Routine care of the disease states continues beside it from the same declaration.

Staff time is priced from one shared salary item per staff type, `cost-item.workforce-salary.<type>`, where the type is `nurse`, `generalist-primary-care-doctor`, `specialist`, `therapist` or `counsellor`. A type is the same item in every module that uses it and can be edited on its own. The item is an annual salary whose default is the country's WHO-CHOICE annual salary for the type's skill level: 4 for doctors and specialists, 3 for nurses and therapists, 2 for counsellors. WHO-CHOICE (CHOosing Interventions that are Cost-Effective) is the WHO programme that publishes country unit costs. The cost of one staff minute is

$$
p = \frac{S}{126\,720}
$$

where $S$ is the annual salary in US dollars and $p$ is the cost in US dollars per minute. The divisor 126,720 is the number of working minutes in a year (8 hours a day, 22 days a month, 12 months), the convention the data service uses for its WHO-CHOICE cost per minute. Routine-care coverage is editable on the Diabetes card of the Scenarios page.

## Parameters

The module has one baseline template, `diabetes_baseline`, which changes nothing. Its parameter registry (`parameters/registry.v1.json`) declares five module-owned parameters. None is editable on the Scenarios page, and each has the same value in baseline and comparison.

| Parameter | Meaning | Baseline default | Comparison default | Range | Source |
| --- | --- | --- | --- | --- | --- |
| Diabetes disability weight (`diabetes_disability_weight`) | disability weight of diabetes without a modelled complication | 0.080 | 0.080 | fixed | GBD 2019 |
| Retinopathy disability weight (`diabetic_retinopathy_disability_weight`) | disability weight of retinopathy | 0.134 | 0.134 | fixed | GBD 2019 |
| Amputation disability weight (`lower_extremity_amputation_disability_weight`) | disability weight of lower-extremity amputation | 0.225 | 0.225 | fixed | GBD 2019 |
| Nephropathy disability weight (`diabetic_nephropathy_disability_weight`) | disability weight of nephropathy | 0.013 | 0.013 | fixed | GBD 2019 |
| Minimum onset age (`minimum_onset_age`) | first age, in years, with diabetes incidence and prevalence | 15 | 15 | fixed | module choice: type 2 diabetes only |

Incidence, complication and fatality rates come from the data service for the selected country. Intervention parameters and their baseline and comparison values belong to the intervention modules.

## Data and evidence

`model.json` is the executable graph. The module contract (`interface/diabetes-epidemiology-core.module.contract.v1.json`) declares its inputs, outputs and composition.

### Country data

| Input | Source | Data service request |
| --- | --- | --- |
| Diabetes incidence, ages 15 and over | GBD, as packaged in the Spectrum/OneHealth NCD defaults | `fhdb.epidemiology`, disease `Diabetes`, measure `incidence`, `min_age` 15 |
| Diabetes prevalence, ages 15 and over (opening state) | GBD, as above | measure `prevalence`, `min_age` 15 |
| Diabetes fatality and the GBD age pattern of deaths | GBD, as above | disease `Diabetes`, measure `deaths` |
| Nephropathy fatality | GBD chronic kidney disease deaths, as above | disease `CKD`, measure `deaths` |
| Retinopathy, nephropathy and amputation incidence; retinopathy and amputation fatality | Spectrum/OneHealth diabetes disease association file | `diabetes.get_observation` |
| Death target | WHO GHE 2021, diabetes deaths per person by sex and age band | `who_ghe.cause_death_rate`, cause `diabetes` |
| All-cause death probability | the platform's demographic data | `fhdb.mortality` |
| Years-of-life-lost weights | GBD reference life table, remaining life expectancy by age, 2019 values, the same for both sexes | `fhdb.yll_weights` |

The complication incidence and fatality rates are the Spectrum/OneHealth values. The primary studies behind them are not recorded.

### Disability weights

A model state that holds one GBD health state takes that state's weight. A state that combines several GBD sequelae (the specific consequences of a disease that GBD weights) takes the GBD 2019 global average for those sequelae: the cause's YLDs divided by its prevalent cases. That average weights each severity level by GBD's own severity distribution, which GBD models by location and does not publish as a table.

| Model state | GBD weight | GBD health states and mapping |
|---|---|---|
| Diabetes without a modelled complication (`Diabetes`, node `lrso7mga`) | 0.080 | Uncomplicated diabetes 0.049, diabetic neuropathy 0.133 and neuropathy with foot ulcer, which the model does not separate. GBD 2019 global average for type 2 diabetes: 35.15 million YLDs over 437.9 million cases. The average also contains the small share of YLDs from vision loss and amputation, which the model holds in their own states. |
| Diabetic retinopathy (`DiabeticRetinopathy`, node `ls9rs1ih`) | 0.134 | Vision loss due to diabetes: moderate 0.031, severe 0.184, blindness 0.187. GBD publishes no global severity split for diabetic vision loss, so the three levels have equal shares. |
| Lower-extremity amputation (`LowerExtrmAmpt`, node `ls9rvbes`) | 0.225 | GBD sequelae diabetic neuropathy with treated amputation (0.17) and with untreated amputation (0.28), each a combination of neuropathy (0.133) and one-leg amputation. GBD splits treated and untreated amputation by health-system access and publishes no split, so the two have equal shares. |
| Diabetic nephropathy (`DiabeticNephropathy`, node `ls9y3aia`) | 0.013 | Chronic kidney disease due to type 2 diabetes: stage III 0 without anaemia and 0.004–0.149 with it, stage IV 0.104, stage V 0.569, dialysis 0.571, transplant 0.024. GBD 2019 global average: 1.69 million YLDs over 129.6 million cases. Most cases are stage III without anaemia, which carries no weight. |

The module does not use the values in the Spectrum/OneHealth disease association file, which have no cited source: 0.031 for diabetes, 0.338 for retinopathy, 0.164 for amputation and 0.338 for nephropathy.

Sources:

- GBD 2019 Diseases and Injuries Collaborators. Global burden of 369 diseases and injuries in 204 countries and territories, 1990–2019: a systematic analysis for the Global Burden of Disease Study 2019. *Lancet* 2020;396:1204–22. Appendix 1 gives the disability-weight table in each cause section. Appendix 2, table S18, gives global prevalence and YLDs for 2019.
- Institute for Health Metrics and Evaluation (IHME). GBD 2019 disability-weights table and sequela-to-health-state list, which gives the combined amputation weights.
- Salomon JA et al. Disability weights for the Global Burden of Disease 2013 study. *Lancet Glob Health* 2015;3:e712–23, where the weights were estimated.

## Validation

The opening year's diabetes deaths equal the WHO GHE 2021 target in each sex and age band by construction. An Indonesia check, run with incidence and prevalence from age 0 rather than 15, compared the model with and without the calibration. Modelled diabetes deaths in 2025 were 138,960 with the uncalibrated GBD and Spectrum/OneHealth fatality and 63,646 with the calibration, the GHE 2021 level. Age-standardised prevalence from 2025 to 2050 changed by 0% with the calibration, against a rise of 4% without it. No result has been compared with an external estimate of the effect of a diabetes intervention.

## Assumptions and limitations

- Complications are simplified. Neuropathy and foot ulcer are not separate states, and their disability is inside the episode weight. A person can have only one complication, and there is no progression from one complication to another or remission from any of them. People with several complications therefore carry less disability than they would in reality.
- Type 1 diabetes in adults remains. Incidence and prevalence are 0 below 15, but from 15 the GBD input still covers all diabetes. Adults with type 1 diabetes are in the model and the interventions reach them.
- Complication rates have no traced primary source. Complication incidence and fatality are Spectrum/OneHealth values. The calibration fixes total diabetes deaths but not how they divide among the complication states.
- Nephropathy deaths are diabetes deaths. Deaths in the nephropathy state count towards the WHO diabetes death target.
- Other-cause relative mortality is a fit, not a measurement. It is chosen so that prevalence stays at its observed level and is bounded between 1 and 4. Where a bound binds, prevalence drifts from its observed level.
- The retinopathy and amputation disability weights assume equal shares of the GBD severity levels, because GBD publishes no global split.
- Intervention effects act only on complications. Interventions do not lower diabetes incidence or the fatality of diabetes without complications, and the module does not model screening yield, diagnosis, adherence or treatment pathways.
- Routine care can be counted twice in each scenario's gross cost. When a diabetes intervention is selected, people in the episode state who already receive that service at current coverage are costed both as routine care and in the intervention's block, in both scenarios. The difference between scenarios is unaffected, but each scenario's total health-system cost is overstated by that amount.
- The model is marginal. The disease-free state is a local residual, not an additional population, so the model must stay reconciled to the canonical population.

## Relationships

The demographic module supplies the canonical population and background mortality. `opening-state-reconciliation` initialises the diabetes states and applies the calibration. `risk-factor-reconciliation` supplies the incidence modifier. The intervention modules listed under Purpose own the clinical effects and their resources, and the compiler inserts their components into this graph. The metric modules (`metric-health-burden`, `metric-hyl`) calculate disability-adjusted life years and healthy years from the states, deaths and disability weights this module publishes.

## Status

The disease graph, module contract, baseline template, opening-state calibration, intervention extension points, risk-factor incidence modifier and routine-care declarations are implemented and run through the client's normal analysis path. The graph needs compiler lowering and is not a standalone national model.
