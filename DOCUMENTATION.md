# The Diabetes Model, and its Scenarios
This document describes the Diabetes state-transition model, and the scenarios which are run using it.
If you are uncertain about the general appendix 3 methodologies, or have general queries, [please refer to the README](README.md).

## Link to Models
- Baseline: [Link to Botech Online Model](https://botech.forecasthealth.org/?userId=appendix_3&modelId=diabetes_baseline)

##  The Diabetes Model and its design
### Diabetes Models creates several scenarios: Null_Diabetes, D1, D2, D3, D4, D5
The Diabetes Model refers to a "Model architecture": A structure of states and transitions, which can be used to run different scenarios.
A scenario is when the structure has a different set of transition rates between the states.

The Diabetes model is used to run two scenarios of treatment coverage: D1, D2, D3, D4 and D5
In addition, the Diabetes model is also used to run a "Null Scenario": Called Diabetes_Null.
We will explain the Null Scenario later.

### Structure of the Diabetes Model
Diabetes has several key states, `DsFreeSus`,  `DiabetesEpsd`, `DiabeticRetinopathy`, `LowerExtrmAmpt`, `DiabeticNephropathy` and `Deceased`.
`DsFreeSus` means "Disease free, susceptible", and this refers to the majority of the population.
`DiabetesEpsd` means "Diabetes Episode", and generally refers to people who have been diagnosed with diabetes.
`DiabeticRetinopathy` means "Diabetic Retinopathy" and refers to people who have retinopathy caused by diabetes.
`LowerExtrmAmpt` means "Lower Extremity Amputation" and refers to people who have had a lower limb, or part of that lower limb (e.g. a foot) amputated because of diabetes.
`DiabeticNephropathy` means "Diabetic Nephropathy", and refers to people who have nephropathy caused by diabetes.
`Deceased` refers to the people in the model who have died, either through background mortality (`DsFreeSus -> Deceased`) or through the Diabetes episode (`DiabetesEpsd -> Deceased`).

In addition to these states, there are other "states" which are used to perform calculations, or collect useful statistics about the model.
This is something we have chosen to do in our model structure, so it's visible to users, but it is not strictly necessary.
For example, we have states for `Disability`, which collects information about the stock of key states and multiplies them against some disability weight.
We also have states to calculate births, migration, and the effects of interventions on disability and mortality.
Once again, we made these design decisions so that users can see how these work, but they aren't strictly necessary.
They can be done elsewhere, and simply rendered as a transition rate.

### The modelled treatments for Diabetes
For Diabetes, there are five treatments.
An intervention is something that has an effect on the main components of the model, such as disability, or mortality.
- StdGlycControl
    - Name in Spectrum: Standard Glycemic control
- IntsvGlycControl
    - Name in Spectrum: Intensive Glycemic control
- RetinopathyScrn
    - Name in Spectrum: Retinopathy Screening + photocoagulation
- NeuropathyScr
    - Name in Spectrum: Neuropathy screening and preventive foot care
- NeprhopathyScr
    - Name in Spectrum: Nephropathy screening and treatment
 
While treatments are always present in the structure of the Diabetes model, their coverage differs depending on the scenario.

### Treatment Impacts
**NOTE** - These figures imply a modification of effect sizes.
E.g. `StdGlycControl` reduces the CFR of `DiabeticRetpathy` by 75% (-0.75).

- StdGlycControl
    - Incidence of `DiabeticRetpathy`: -0.75
    - Incidence of `LowerExtrmAmpt`: -0.286
    - Incidence of `DiabeticNephropathy`: -0.39
- IntsvGlycControl
    - Incidence of `DiabeticRetpathy`: -0.65
    - Incidence of `LowerExtrmAmpt`: -0.151
    - Incidence of `DiabeticNephropathy`: -0.39
- RetinopathyScrn
    - Incidence of `DiabeticRetpathy`: -0.20
- NeuropathyScr
    - Incidence of `DiabeticNephropathy`: -0.35
- NeprhopathyScr
    - Incidence of `DiabeticNephropathy`: -0.24

### Population in Need
**NOTE** - Refers to the proportion of people in `DiabetesEpsd` who are "in need" of this treatment.
e.g. 90% of `DiabetesEpsd` are "in need" of `StdGlycControl`
- StdGlycControl: 0.9
- IntsvGlycControl: 0.1
- RetinopathyScrn: 1.0
- NeuropathyScr: 1.0
- NeprhopathyScr: 1.0

### The Model has two key components
The Diabetes model is large, but can be broken down into two components.
![Both Components Together](./static/diabetes_both_components.png)

#### The main component moves people between states
![The Main Component](./static/diabetes_main_component.png)

The main component has the states we've introduced: `DsFreeSus`, `DiabetesEpsd`, `DiabeticRetinopathy`, `LowerExtrmAmpt`, `DiabeticNephropathy`, `Deceased`, `Disability`, `Births`.
Importantly there are some other states which sit between states:
- `DsFreeSus Disability` sits between `DsFreeSus` and `Disability`
- `DiabetesEpsd Disability` sits between `DiabetesEpsd` and `Disability`
- `DiabeticRetinopathy Disability` sits between `DiabeticRetinopathy` and `Disability`
- `LowerExtrmAmpt Disability` sits between `LowerExtrmAmpt` and `Disability`
- `DiabeticNephropathy Disability` sits between `DiabeticNephropathy` and `Disability`
- `DiabetesEpsd Mortality` sits between `DiabetesEpsd` and `Mortality`
- `DiabeticRetinopathy Mortality` sits between `DiabeticRetinopathy` and `Mortality`
- `LowerExtrmAmpt Mortality` sits between `LowerExtrmAmpt` and `Mortality`
- `DiabeticNephropathy Mortality` sits between `DiabeticNephropathy` and `Mortality`
- `DiabeticRetinopathy Incidence` sits between `DiabetesEpsd` and `DiabeticRetinopathy`
- `LowerExtrmAmpt Incidence` sits between `DiabetesEpsd` and `LowerExtrmAmpt`
- `DiabeticNephropathy Incidence` sits between `DiabetesEpsd` and `DiabeticNephropathy`

These states aren't really states in a true sense. 
Rather, these states set the value of the transition rates around them.
So, for example, `DsFreeSus Disability` is really the transition rate for `DsFreeSus -> Disability`.
In the nomenclature of the Botech protocol, we call this a "Surrogate node".
This is a structural decision we have made, but it doesn't change the results.
Rather, we do this, so we can show how the calculations work to determine the disability and mortality effects.

#### The calculation component sets the transition rates
![The Calculation Component](./static/diabetes_calculation_component.png)
The "Surrogate Nodes" mentioned above, are set by a series of calculations in the model.
We will explain these in detail below in the section "The Order of Operations".

### The Diabetes model scenarios
#### The Diabetes_Null scenario
In the Diabetes_Null, the coverage of all treatments is set to its baseline in the first year of the projection, then 0% afterwards.

#### Scenario D1 - Foot care to prevent amputation in people with diabetes (including educational programmes, access to appropriate footwear, multidisciplinary clinics)
In D1:
- NeuropathyScr is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.
- RetinopathyScrn continues at its baseline coverage for the entirety of the run
- NephropathyScr continues at its baseline coverage for the entirety of the run
- StdGlycControl continues at its baseline coverage for the entirety of the run
- IntsvGlycControl continues at its baseline coverage for the entirety of the run

#### Scenario D2 - Diabetic retinopathy screening for all diabetes patients and laser photocoagulation for prevention of blindness
In D2:
- NeuropathyScr continues at its baseline coverage for the entirety of the run
- RetinopathyScrn is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.
- NephropathyScr continues at its baseline coverage for the entirety of the run
- StdGlycControl continues at its baseline coverage for the entirety of the run
- IntsvGlycControl continues at its baseline coverage for the entirety of the run

#### Scenario D3 - Glycaemic control for people with diabetes, along with standard home glucose monitoring for people treated with insulin to reduce diabetes complications
In D3:
- NeuropathyScr continues at its baseline coverage for the entirety of the run
- RetinopathyScrn continues at its baseline coverage for the entirety of the run 
- NephropathyScr continues at its baseline coverage for the entirety of the run
- StdGlycControl is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.
- IntsvGlycControl is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.

#### Scenario D5 - Control of blood pressure in people with diabetes
In D5:
- NeuropathyScr continues at its baseline coverage for the entirety of the run
- RetinopathyScrn continues at its baseline coverage for the entirety of the run
- NephropathyScr is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.
- StdGlycControl continues at its baseline coverage for the entirety of the run
- IntsvGlycControl continues at its baseline coverage for the entirety of the run

#### Missing Diabetes Scenarios
Other diabetes scenarios involve the Cardiovascular Disease model, and will be introduced once that is built.

## The Diabetes Model and its key assumptions
**NOTE** - A document is a difficult place to put entire lists of assumptions, as many of the assumptions we have change over time, and many of the assumptions are arrays of values, which apply to males and females differently, as well as different ages.

Therefore, please look at `./data/diabetes.csv` as a reference guide for some assumptions.
Values for disability weights have come from `./data/Diabetes.xlsx` which is taken from Spectrum.
Furthermore, even though measures of incidence, prevalence, and mortality may appear in this document, the final values were taken from `./data/GBD_Country_DATA.xlsx`.

### The baseline scenario is the default scenario
The baseline scenario has a coverage rate that is static, and continues from the start year to the end year.
This is important, because it *completely removes the effect of the Calculation Component*. 
This is because, in essence, the effect of treatments is governed by the calculation: `effect = impact * coverage * population in need`.
However, coverage is no the current coverage, but the difference between the current coverage, and the starting coverage.
Therefore: `effect = impact * (current_coverage - starting_coverage) * population in need`.
Because `current_coverage - starting_coverage = 0`, there is no effect to add to the default values for disability and mortality.

### The null scenario reduces the coverage, and therefore the impacts
In the null scenario, all treatments are reduced from the baseline coverage to zero.
For example, in Afghanistan, it is assumed that the baseline coverage rate is 5%.
Therefore: `effect = impact * (0 - 0.05) * population in need = impact * -0.05 * population in need`.
Therefore, in this country, the null scenario implies a 5% reduction in the impact of the four treatments.

### The scale-up scenario increases the coverage, and therefor the impacts
In the scale-up scenario, select treatments are increased from baseline to 95% for the projection, starting in the second year.
For the treatments that aren't selected, they are left at the baseline level, and thus do not contribute to effect calculations.
Therefore, for a select treatment in Afghanistan: `effect = impact * (0.95 - 0.05) * population in need = impact * 0.9 * population in need`.

# What is the order of operations?
## What do we mean by the order of operations?
When you "run a model" you are telling the model to, for example:
- Put some values in `DsFreeSus` e.g. the population of Australia
- Move some of those values to `DiabetesEpsd` e.g. the incidence of Diabetes
- Move some values from `DiabetesEpsd -> DsFreeSus` e.g. the remission rate of Diabetes

However, the ordering of these can be important.
Therefore, the order of operations describes the order in which steps are taken each year the model runs.

## The order of operations
It may look complicated at first, but we can simplify it by working through one example.
We will use the example of `LowDoseBeclom` to show this affects disability and mortality.
Importantly, for all these calculations, do not imagine these are people being transferred between states.
Rather, imagine this is an alternative to using Microsoft Excel, for calculating some values that will become a transition rate.

### 1. Generate the population of the country in 2019
We do this using the UNDP World Population Prospects Data, for country, year.
The data that is returned is the number of people for sex, age (through 100).
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Population1JanuaryBySingleAgeSex_Medium_1950-2021.zip
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Population1JanuaryBySingleAgeSex_Medium_2022-2100.zip

### 2. Generate values for constants in the Calculation Component
We need to load the constants which are used to calculate the effects on disability and mortality. 
This is the second step of the model. 

### 3. Calculate the Coverage Rate
The coverage rate is calculated by `Coverage - Starting Coverage`.
For example, `RetinopathyScrn_Coverage - RetinopathyScrn_StartingCoverage`.
The result of this calculation is stored in, e.g. `RetinopathyScrn_Calculated_Coverage`

### 4. Calculate Incidence Effects
Disability effects are calculated by: `PIN * Incidence Impact * Coverage`
Therefore, using `RetinopathyScrn` as an example, we multiply `RetinopathyScrn_PIN`, `RetinopathyScrn_DiabeticRetinopathy_Incidence_Impact` and `RetinopathyScrn_Calculated_Coverage`
We store this value in `RetinopathyScrn_Incidence_Effect`.

### 5. Transform the Incidence Effects
Here, we transform a value to its inverse by subtractring it from one. 
E.g. 1 - 0.05 = 0.95.
Therefore, the sequence might be: 1 - 0.05 - 0.03 - 0.02 - 0.00 = 0.90
We store this value in the variable referring to the state of interest: `DiabeticRetinopathy_Transform`, `LowerExtrmAmpt_Transform`,`DiabeticNeprhopathy_Transform`

### 6. We calculate the "Blended Disability" for `DiabetesEpsd`, `DiabeticRetinopathy`, `LowerExtrmAmpt` and `DiabeticNephropathy`
(We'll use `DiabetesEpsd`  as an example in this section)

The default disability weight for `DiabetesEpsd` is not a static value.
Instead, it is determined by the following equation: `dw = 1 - ((1 - healthy_disability) * (1 - DiabetesEpsd_disability))`
We call this a "blended disability".

We calculate this in our model through the following:
- The constant loaded in `Diabetes_Disability` is subtracted from 1
- The constant loaded in `Healthy_Disability` is subtracted from 1
- This value is stored in `DiabetesEpsd_Blended_Disability`
- `DiabetesEpsd_Blended_Disability` is subtracted from 1, and stored in `DiabetesEpsd_Disability_Transform`

### 7. Calculate the Surrogate Values
In Diabetes, we have surrogates for incidence, disability, and mortality.
In this step, we calculate the surrogate values.
As a reminder, "surrogate values" really mean "the final transition rates between a source and a target".

For incidence, we:
1. Add the incidence rates to their respective surrogate (e.g. `DiabeticRetinopathy_Incidence_Rate` to `DiabeticRetinopathy Incidence`)
2. Multiply the transformed effect against the surrogate (e.g. `DiabeticRetinopathy_Transform` to `DiabeticRetinopathy Incidence`)

For disability, we:
1. Move the value from `Blended_Disability_Transform` into `DiabetesEpsd Disability`
2. Multiply `Disability_Effect_Transform` against the value in `DiabetesEpsd Disability`

For mortality:
1. Add the mortality rates to their respective surrogate

Once this is set in the surrogate, it is propagated to the edges surrounding it. 

### 8. Calculate the `DsFreeSus Disability` Surrogate
The disability weight for `DsFreeSus` is simply just the `Healthy_Disability` value.
Therefore, we just move this value to the `DsFreeSus Disability` state

### 9. Record the number of births that will occur
For states `DsFreeSus`, `DiabetesEpsd`, `DiabeticRetinopathy`, `LowerExtrmAmpt` and `DiabeticNephropathy` we multiply the number of fertile women, against their age specific fertility rates (UNDP Statistics), to calculate the number of births.
NOTE - These women don't given birth yet, but we calculate births now, before people move states or die, or age or migrate.
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Fertility_by_Age1.zip

### 10 - Movement around the main states
`DsFreeSus` move to `DiabetesEpsd` (if this is the first year, the prevalent population is moved first).
`DiabetesEpsd` move to `DiabeticRetinopathy`, `LowerExtrmAmpt` and `DiabeticNephropathy` (if this is the first year, the prevalent population is moved first).
Note - there is no remission from these states.

### 12 - Disability is Recorded
`DsFree -> Disability`, `DiabetesEpsd -> Disability`, `DiabeticRetinopathy -> Disability`, `LowerExtrmAmpt -> Disability`, `DiabeticNephropathy -> Disability` and `Deceased -> Disability` are recorded.
Using `DiabetesEpsd` as an example, let's explain this.
First, the stock of persons in `DiabetesEpsd` is counted e.g. 3,000.
Then, this stock is multiplied against the disability weight calculated and stored in `DiabetesEpsd Disability` e.g. 0.1
Then, disability is calculated as `3000 * 0.1 = 300`.
This value is sent and stored into `Disability`.

The disability weight for `DiabetesEpsd`, `DiabeticRetinopathy`, `LowerExtrmAmpt`, and `DiabeticNephropathy` is taken from Spectrum by Avenir Health.
In particular, they are taken from the `Diabetes.xlsx` file in the Spectrum repository.
The disability weight for `DsFreeSus` is taken from the Spectrum repository but is originally from GBD we believe.

### 13 - Populations migrate
Migration rates calculated using the UNDP World Population Projections are used to increase or decrease the current populations of people in `DsFreeSus`, `DiabetesEpsd`, `DiabeticRetinopathy`, `LowerExtrmAmpt` and `DiabeticNephropathy`.
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/EXCEL_FILES/1_General/WPP2022_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_REV1.xlsx

### 14 - People get older
People get older by 1 year. 
If a person was 100, they are removed from the model at this point.

### 15 - People die
People move to the `Deceased` state via: `DsFreeSus -> Deceased` 
The background mortality rate for `DsFreeSus -> Deceased` is taken from the UNDP World Population Projections lifetables (we use the rate "qx").
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Life_Table_Complete_Medium_Male_1950-2021.zip
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Life_Table_Complete_Medium_Male_2022-2100.zip

People move to the `Deceased` state via: `DiabetesEpsd -> Deceased` 
This mortality rate was taken from `GBD_Country_Data.xlsx` in the Spectrum repository.

People move to the `Deceased` state via: `DiabeticRetinopathy -> Deceased`, `LowerExtrmAmpt -> ...` and `DiabeticNephropathy -> ...`
This mortality rate was taken from `Diabetes.xlsx` in the Spectrum repository.


### 16 - Women give birth
The births that were stored in the `Births` state are transmitted to `DsFreeSus`.
The number of males and females are governed by the sex ratio from the UNDP World Population Projections database.

Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/EXCEL_FILES/1_General/WPP2022_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_REV1.xlsx

### 17 - Constants are cleared
Any constants or intermediate values that were calculated are cleared from the model, so they don't contribute to calculations in the next year.

### 18 - The timestep is incremented.
If the year was 2019, it is now 2020. 
If the year was 2020, it is now 2021.
If the year was 2119, the model simulation ends.

# Outstanding Issues / Clarifications / Questions
- Our current demographic projection may differ substantially from previous model's demographic project.
    - Changes to fertility rates, background mortality, and migration rates may all affect the magnitude of the results.
- We are not sure if there has been discounting on effects.
- We are not sure if there are added effects on mortality for assumptions which use `Diabetes.xlsx`
- We are not sure if the prevalence for `DiabeticRetinopathy`, `LowerExtrmAmpt` and `DiabeticNephropathy` are proportion of `DsFreeSus` or `DiabetesEpsd`. We think it is probably `DsFreeSus`.


[Link to Results](https://forecasthealth.org/who-appendix3-cr/)
