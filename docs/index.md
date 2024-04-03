# The COPD Model, and its Scenarios
This document describes the COPD state-transition model, and the scenarios which are run using it.
If you are uncertain about the general appendix 3 methodologies, or have general queries, [please refer to the README](README.md).

## Link to Interactive tool
- [Click here to use the interactive tool](https://forecasthealth.org/ncd-chronic-respiratory-disease-copd/tool.html)

## Link to Models
- Baseline (as reference): [Link to Botech Online Model](https://botech.forecasthealth.org/?userId=appendix_3&modelId=copd_baseline)

##  The COPD Model and its design
### COPD Models creates three scenarios: Null_COPD, CR2, and CR4
The COPD Model refers to a "Model architecture": A structure of states and transitions, which can be used to run different scenarios.
A scenario is when the structure has a different set of transition rates between the states.

The COPD model is used to run two scenarios of treatment coverage: CR2 and CR4.
In addition, the COPD model is also used to run a "Null Scenario": Called COPD_Null.
We will explain the Null Scenario later.

### Structure of the COPD Model
COPD has three key states, `DsFreeSus`,  `COPDEpsd`, and `Deceased`.
`DsFreeSus` means "Disease free, susceptible", and this refers to the majority of the population.
`COPDEpsd` means "COPD Episode", and generally refers to people who have asthma and will experience an episode that year.
`Deceased` refers to the people in the model who have died, either through background mortality (`DsFreeSus -> Deceased`) or through the COPD episode (`COPDEpsd -> Deceased`).

In addition to these states, there are other "states" which are used to perform calculations, or collect useful statistics about the model.
This is something we have chosen to do in our model structure, so it's visible to users, but it is not strictly necessary.
For example, we have states for `Disability`, which collects information about the stock of `DsFreeSus`, `COPDEpsd` and `Deceased` and multiplies them against some disability weight.
We also have states to calculate births, migration, and the effects of interventions on disability and mortality.
Once again, we made these design decisions so that users can see how these work, but they aren't strictly necessary.
They can be done elsewhere, and simply rendered as a transition rate.

### The modelled treatments for COPD
For COPD, there are four treatments.
An intervention is something that has an effect on the main components of the model, such as disability, or mortality.
- InhaledSalbutamol
    - Name in Spectrum: Inhaled Salbutamol
- IpratropiumInhaler
    - Name in Spectrum: Ipratropium Inhaler
- OralPrednisolone
    - Name in Spectrum: Oral Prednisolone
 
While treatments are always present in the structure of the COPD model, their coverage differs depending on the scenario.

### Treatment Impacts
**NOTE** - These figures imply a modification of effect sizes.
E.g. `InhaledSalbutamol` reduces the Disability of `COPDEpsd` by 14.8% (-0.148).

- InhaledSalbutamol
    - Disability: -0.148
- IpratropiumInhaler
    - Disability:-0.169
- OralPrednisolone
    - Disability:-0.337

### Population in Need (PIN)
**NOTE** - Refers to the proportion of people in `COPDEpsd` who are "in need" of this treatment.
e.g. 30% of `COPDEpsd` are "in need" of `OralPrednisolone`
- InhaledSalbutamol: 1.0 (100% PIN)
- IpratropiumInhaler: 0.21
- OralPrednisolone: 0.337

### The Model has two key components
The COPD model is large, but can be broken down into two components.
![Both Components Together](./static/copd_both_components.png)

#### The main component moves people between states
![The Main Component](./static/copd_main_component.png)

The main component has the states we've introduced: `DsFreeSus`, `COPDEpsd`, `Deceased`, `Disability`, `Births`.
Importantly there are some other states which sit between states:
- `DsFreeSus Disability` sits between `DsFreeSus` and `Disability`
- `COPDEpsd Disability` sits between `COPDEpsd` and `Disability`
- `COPDEpsd Mortality` sits between `COPDEpsd` and `Deceased`

These states aren't really states in a true sense. 
Rather, these states set the value of the transition rates around them.
So, for example, `DsFreeSus Disability` is really the transition rate for `DsFreeSus -> Disability`.
In the nomenclature of the Botech protocol, we call this a "Surrogate node".
This is a structural decision we have made, but it doesn't change the results.
Rather, we do this, so we can show how the calculations work to determine the disability and mortality effects.

#### The calculation component sets the transition rates
![The Calculation Component](./static/copd_calculation_component.png)
The "Surrogate Nodes" mentioned above, are set by a series of calculations in the model.
We will explain these in detail below in the section "The Order of Operations".

### The COPD model scenarios
#### The COPD_Null scenario
In the COPD_Null, the coverage of all treatments is set to its baseline in the first year of the projection, then 0% afterwards.

#### Scenario CR2 - Acute treatment of COPD exacerbations with inhaled bronchodilators and oral steroids
In CR2:
- InhaledSalbutamol continues at its baseline coverage for the entirety of the run
- IpratropiumInhaler continues at its baseline coverage for the entirety of the run
- OralPrednisolone is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.

#### Scenario CR4 - Long-term management of COPD with inhaled bronchodilator
In CR4:
- InhaledSalbutamol is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.
- IpratropiumInhaler is set at its baseline coverage for the first year (2019) of the projection, and then to 95% coverage for the rest of the projection.
- OralPrednisolone continues at its baseline coverage for the entirety of the run

## The COPD Model and its key assumptions
**NOTE** - A document is a difficult place to put entire lists of assumptions, as many of the assumptions we have change over time, and many of the assumptions are arrays of values, which apply to males and females differently, as well as different ages.

Therefore, please look at `./data/copd.csv` as a reference guide for some assumptions.
Values for disability weights have come from `./data/COPD.xlsx` which is taken from Spectrum.
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
In the scale-up scenario, select treatments (one treatment in CR2, three treatments in CR4) are increased from baseline to 95% for the projection, starting in the second year.
For the treatments that aren't selected, they are left at the baseline level, and thus do not contribute to effect calculations.
Therefore, for a select treatment in Afghanistan: `effect = impact * (0.95 - 0.05) * population in need = impact * 0.9 * population in need`.

# What is the order of operations?
## What do we mean by the order of operations?
When you "run a model" you are telling the model to, for example:
- Put some values in `DsFreeSus` e.g. the population of Australia
- Move some of those values to `COPDEpsd` e.g. the incidence of COPD
- Move some values from `COPDEpsd -> DsFreeSus` e.g. the remission rate of COPD

However, the ordering of these can be important.
Therefore, the order of operations describes the order in which steps are taken each year the model runs.

## The order of operations
It may look complicated at first, but we can simplify it by working through one example.
We will use the example of `InhaledSalbutamol` to show this affects disability and mortality.
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
For example, `InhaledSalbutamol_Coverage - InhaledSalbutamol_StartingCoverage`.
The result of this calculation is stored in, e.g. `InhaledSalbutamol_Calculated_Coverage`

### 4. Calculate Disability Effects
Disability effects are calculated by: `PIN * Disability Impact * Coverage`
Therefore, using `InhaledSalbutamol` as an example, we multiply `InhaledSalbutamol_PIN`, `InhaledSalbutamol_Disability_Impact` and `InhaledSalbutamol_Calculated_Coverage`
We store this value in `InhaledSalbutamol_Disability_Effect`.

### 5. Transform the Disability Effects
Here, we transform a value to its inverse by subtractring it from one. 
E.g. 1 - 0.05 = 0.95.
We do this for `InhaledSalbutamol_Disability_Effect`, `IpratropiumInhaler_Disability_Effect`, `OralPrednisolone_Disability_Effect`. 
Therefore, the sequence might be: 1 - 0.05 - 0.03 - 0.02 - 0.00 = 0.90
We store this value in `Disability_Effect_Transform`. 

### 6. We calculate the "Blended Disability" for `COPDEpsd`
The default disability weight for `COPDEpsd` is not a static value.
Instead, it is determined by the following equation: `dw = 1 - ((1 - healthy_disability) * (1 - asthmaepsd_disability))`
We call this a "blended disability".

We calculate this in our model through the following:
- The constant loaded in `COPD_Disability` is subtracted from 1
- The constant loaded in `Healthy_Disability` is subtracted from 1
- This value is stored in `COPD_Blended_Disability`
- `COPD_Blended_Disability` is subtracted from 1, and stored in `Blended_Disability_Transform`

### 7. Calculate `COPDEpsd Disability` surrogate value
We now have two values:
1. The default `COPDEpsd` disability weight (stored in `Blended_Disability_Transform`)
2. Some modifier of that disability weight, based on treatment impact, population in need, and coverages, stored in `Disability_Effect_Transform`

Therefore, we do two operations in this step:
1. Move the value from `Blended_Disability_Transform` into `COPDEpsd Disability`
2. Multiply `Disability_Effect_Transform` against the value in `COPDEpsd Disability`

Once this is set in the surrogate, it is propagated to the edges surrounding it. 

### 8. Calculate `DsFreeSus Disability` Surrogate
The disability weight for `DsFreeSus` is simply just the `Healthy_Disability` value.
Therefore, we just move this value to the `DsFreeSus Disability` state

### 9. Repeat Steps 3 - 8 but for Mortality
To determine the value in `COPDEpsd Mortality`, we follow very similar steps as have been described for `COPDEpsd Disability`.
However, in COPD, no treatments have an effect on mortality as we understand it.

### 10. Record the number of births that will occur
For states `DsFreeSus` and `COPDEpsd` we multiply the number of fertile women, against their age specific fertility rates (UNDP Statistics), to calculate the number of births.
NOTE - These women don't given birth yet, but we calculate births now, before people move states or die, or age or migrate.
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Fertility_by_Age1.zip

### 11 - Exchange between DsFreeSus and COPDEpsd
`DsFree -> COPDEpsd` and `COPDEpsd -> DsFree` are transacted (the incidence of asthma and remission of asthma respectively).

### 12 - Disability is Recorded
`DsFree -> Disability`, `COPDEpsd -> Disability` and `Deceased -> Disability` are recorded.
Using `COPDEpsd` as an example, let's explain this.
First, the stock of persons in `COPDEpsd` is counted e.g. 3,000.
Then, this stock is multiplied against the disability weight calculated and stored in `COPDEpsd Disability` e.g. 0.1
Then, disability is calculated as `3000 * 0.1 = 300`.
This value is sent and stored into `Disability`.

The disability weight for `COPDEpsd` is taken from Spectrum by Avenir Health.
The disability weight for `DsFreeSus` is taken from Spectrum by Avenir Health but is originally from GBD we believe.

### 13 - Populations migrate
Migration rates calculated using the UNDP World Population Projections are used to increase or decrease the current populations of people in `DsFreeSus` and `COPDEpsd`.
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/EXCEL_FILES/1_General/WPP2022_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_REV1.xlsx

### 14 - People get older
People get older by 1 year. 
If a person was 100, they are removed from the model at this point.

### 15 - People die
People move to the `Deceased` state via: `DsFreeSus -> Deceased`, `COPDEpsd -> Deceased`
The background mortality rate for `DsFreeSus -> Deceased` is taken from the UNDP World Population Projections lifetables (we use the rate "qx").

Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Life_Table_Complete_Medium_Male_1950-2021.zip
Reference: https://population.un.org/wpp/Download/Files/1_Indicators%20(Standard)/CSV_FILES/WPP2022_Life_Table_Complete_Medium_Male_2022-2100.zip

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

# Test Results

| Country | Scenario  | STATUS_CODE | HYL          | Avenir HYL    | Ratio         | vs Baseline   |
|---------|-----------|-------------|--------------|---------------|---------------|---------------|
| AFG | baseline | 200 | 4,126,579,482 | N/A | N/A | 1.000000 |
| AFG | null | 200 | 4,126,579,482 | 5,757,189,149 | 0.716770 | 1.000000 |
| AFG | cr2 | 200 | 4,126,579,482 | 5,759,100,686 | 0.716532 | 1.000000 |
| AFG | cr4 | 200 | 4,126,579,482 | 5,766,207,170 | 0.715649 | 1.000000 |
| DZA | baseline | 200 | 3,413,762,017 | N/A | N/A | 1.000000 |
| DZA | null | 200 | 3,413,762,017 | 5,289,116,838 | 0.645431 | 1.000000 |
| DZA | cr2 | 200 | 3,413,762,017 | 5,290,811,515 | 0.645225 | 1.000000 |
| DZA | cr4 | 200 | 3,413,762,017 | 5,296,663,433 | 0.644512 | 1.000000 |
| AGO | baseline | 200 | 5,709,573,967 | N/A | N/A | 1.000000 |
| AGO | null | 200 | 5,709,573,967 | 12,042,158,896 | 0.474132 | 1.000000 |
| AGO | cr2 | 200 | 5,709,573,967 | 12,044,241,336 | 0.474050 | 1.000000 |
| AGO | cr4 | 200 | 5,709,573,967 | 12,053,017,357 | 0.473705 | 1.000000 |
| ARG | baseline | 200 | 2,723,950,869 | N/A | N/A | 1.000000 |
| ARG | null | 200 | 2,723,950,869 | 4,449,630,159 | 0.612175 | 1.000000 |
| ARG | cr2 | 200 | 2,723,950,869 | 4,451,972,285 | 0.611853 | 1.000000 |
| ARG | cr4 | 200 | 2,723,950,869 | 4,459,013,719 | 0.610886 | 1.000000 |
| BGD | baseline | 200 | 10,552,987,667 | N/A | N/A | 1.000000 |
| BGD | null | 200 | 10,552,987,667 | 13,677,176,014 | 0.771577 | 1.000000 |
| BGD | cr2 | 200 | 10,552,987,667 | 13,687,069,564 | 0.771019 | 1.000000 |
| BGD | cr4 | 200 | 10,552,987,667 | 13,724,747,645 | 0.768902 | 1.000000 |
| BRA | baseline | 200 | 11,492,596,312 | N/A | N/A | 1.000000 |
| BRA | null | 200 | 11,492,596,312 | 15,610,811,582 | 0.736195 | 1.000000 |
| BRA | cr2 | 200 | 11,492,596,312 | 15,619,659,263 | 0.735778 | 1.000000 |
| BRA | cr4 | 200 | 11,492,596,312 | 15,646,272,403 | 0.734526 | 1.000000 |
| BFA | baseline | 200 | 2,770,886,665 | N/A | N/A | 1.000000 |
| BFA | null | 200 | 2,770,886,665 | 5,448,439,531 | 0.508565 | 1.000000 |
| BFA | cr2 | 200 | 2,770,886,665 | 5,449,393,435 | 0.508476 | 1.000000 |
| BFA | cr4 | 200 | 2,770,886,665 | 5,453,279,586 | 0.508114 | 1.000000 |
| BDI | baseline | 200 | 1,592,347,738 | N/A | N/A | 1.000000 |
| BDI | null | 200 | 1,592,347,738 | 3,338,323,123 | 0.476990 | 1.000000 |
| BDI | cr2 | 200 | 1,592,347,738 | 3,338,979,011 | 0.476897 | 1.000000 |
| BDI | cr4 | 200 | 1,592,347,738 | 3,341,650,210 | 0.476515 | 1.000000 |
| CMR | baseline | 200 | 3,677,773,572 | N/A | N/A | 1.000000 |
| CMR | null | 200 | 3,677,773,572 | 6,029,655,943 | 0.609948 | 1.000000 |
| CMR | cr2 | 200 | 3,677,773,572 | 6,031,281,946 | 0.609783 | 1.000000 |
| CMR | cr4 | 200 | 3,677,773,572 | 6,038,133,103 | 0.609091 | 1.000000 |
| CAF | baseline | 200 | 386,789,534 | N/A | N/A | 1.000000 |
| CAF | null | 200 | 386,789,534 | 838,987,608 | 0.461019 | 1.000000 |
| CAF | cr2 | 200 | 386,789,534 | 839,191,422 | 0.460907 | 1.000000 |
| CAF | cr4 | 200 | 386,789,534 | 840,021,702 | 0.460452 | 1.000000 |
| TCD | baseline | 200 | 2,926,064,184 | N/A | N/A | 1.000000 |
| TCD | null | 200 | 2,926,064,184 | 4,131,917,958 | 0.708161 | 1.000000 |
| TCD | cr2 | 200 | 2,926,064,184 | 4,132,696,327 | 0.708028 | 1.000000 |
| TCD | cr4 | 200 | 2,926,064,184 | 4,135,867,643 | 0.707485 | 1.000000 |
| CHN | baseline | 200 | 60,048,382,408 | N/A | N/A | 1.000000 |
| CHN | null | 200 | 60,048,382,408 | 102,124,915,511 | 0.587990 | 1.000000 |
| CHN | cr2 | 200 | 60,048,382,408 | 102,178,417,943 | 0.587682 | 1.000000 |
| CHN | cr4 | 200 | 60,048,382,408 | 102,366,324,469 | 0.586603 | 1.000000 |
| COL | baseline | 200 | 3,577,409,955 | N/A | N/A | 1.000000 |
| COL | null | 200 | 3,577,409,955 | 4,057,584,780 | 0.881660 | 1.000000 |
| COL | cr2 | 200 | 3,577,409,955 | 4,059,685,817 | 0.881204 | 1.000000 |
| COL | cr4 | 200 | 3,577,409,955 | 4,066,004,830 | 0.879834 | 1.000000 |
| COD | baseline | 200 | 16,788,660,325 | N/A | N/A | 1.000000 |
| COD | null | 200 | 16,788,660,325 | 24,858,858,200 | 0.675359 | 1.000000 |
| COD | cr2 | 200 | 16,788,660,325 | 24,864,684,269 | 0.675201 | 1.000000 |
| COD | cr4 | 200 | 16,788,660,325 | 24,888,420,633 | 0.674557 | 1.000000 |
| CIV | baseline | 200 | 3,652,350,562 | N/A | N/A | 1.000000 |
| CIV | null | 200 | 3,652,350,562 | 6,170,958,634 | 0.591861 | 1.000000 |
| CIV | cr2 | 200 | 3,652,350,562 | 6,172,121,479 | 0.591750 | 1.000000 |
| CIV | cr4 | 200 | 3,652,350,562 | 6,177,020,189 | 0.591280 | 1.000000 |
| DOM | baseline | 200 | 727,757,829 | N/A | N/A | 1.000000 |
| DOM | null | 200 | 727,757,829 | 1,028,271,946 | 0.707748 | 1.000000 |
| DOM | cr2 | 200 | 727,757,829 | 1,028,511,630 | 0.707583 | 1.000000 |
| DOM | cr4 | 200 | 727,757,829 | 1,029,232,473 | 0.707088 | 1.000000 |
| ECU | baseline | 200 | 1,562,707,128 | N/A | N/A | 1.000000 |
| ECU | null | 200 | 1,562,707,128 | 1,892,583,046 | 0.825701 | 1.000000 |
| ECU | cr2 | 200 | 1,562,707,128 | 1,893,034,296 | 0.825504 | 1.000000 |
| ECU | cr4 | 200 | 1,562,707,128 | 1,894,391,312 | 0.824913 | 1.000000 |
| EGY | baseline | 200 | 9,763,892,494 | N/A | N/A | 1.000000 |
| EGY | null | 200 | 9,763,892,494 | 16,545,135,936 | 0.590137 | 1.000000 |
| EGY | cr2 | 200 | 9,763,892,494 | 16,551,131,939 | 0.589923 | 1.000000 |
| EGY | cr4 | 200 | 9,763,892,494 | 16,571,838,386 | 0.589186 | 1.000000 |
| ERI | baseline | 200 | 335,342,692 | N/A | N/A | 1.000000 |
| ERI | null | 200 | 335,342,692 | 671,973,039 | 0.499042 | 1.000000 |
| ERI | cr2 | 200 | 335,342,692 | 672,153,304 | 0.498908 | 1.000000 |
| ERI | cr4 | 200 | 335,342,692 | 672,887,138 | 0.498364 | 1.000000 |
| ETH | baseline | 200 | 14,322,258,414 | N/A | N/A | 1.000000 |
| ETH | null | 200 | 14,322,258,414 | 20,336,516,029 | 0.704263 | 1.000000 |
| ETH | cr2 | 200 | 14,322,258,414 | 20,340,252,305 | 0.704134 | 1.000000 |
| ETH | cr4 | 200 | 14,322,258,414 | 20,355,470,893 | 0.703607 | 1.000000 |
| GMB | baseline | 200 | 301,555,515 | N/A | N/A | 1.000000 |
| GMB | null | 200 | 301,555,515 | 590,155,049 | 0.510977 | 1.000000 |
| GMB | cr2 | 200 | 301,555,515 | 590,305,161 | 0.510847 | 1.000000 |
| GMB | cr4 | 200 | 301,555,515 | 590,916,869 | 0.510318 | 1.000000 |
| GHA | baseline | 200 | 3,330,452,502 | N/A | N/A | 1.000000 |
| GHA | null | 200 | 3,330,452,502 | 5,503,678,883 | 0.605132 | 1.000000 |
| GHA | cr2 | 200 | 3,330,452,502 | 5,505,011,987 | 0.604986 | 1.000000 |
| GHA | cr4 | 200 | 3,330,452,502 | 5,510,626,243 | 0.604369 | 1.000000 |
| GTM | baseline | 200 | 1,344,238,381 | N/A | N/A | 1.000000 |
| GTM | null | 200 | 1,344,238,381 | 2,410,772,091 | 0.557597 | 1.000000 |
| GTM | cr2 | 200 | 1,344,238,381 | 2,411,145,766 | 0.557510 | 1.000000 |
| GTM | cr4 | 200 | 1,344,238,381 | 2,412,269,754 | 0.557250 | 1.000000 |
| GIN | baseline | 200 | 1,583,378,243 | N/A | N/A | 1.000000 |
| GIN | null | 200 | 1,583,378,243 | 3,025,650,651 | 0.523318 | 1.000000 |
| GIN | cr2 | 200 | 1,583,378,243 | 3,026,425,379 | 0.523184 | 1.000000 |
| GIN | cr4 | 200 | 1,583,378,243 | 3,029,581,402 | 0.522639 | 1.000000 |
| GNB | baseline | 200 | 220,866,006 | N/A | N/A | 1.000000 |
| GNB | null | 200 | 220,866,006 | 392,220,922 | 0.563116 | 1.000000 |
| GNB | cr2 | 200 | 220,866,006 | 392,322,678 | 0.562970 | 1.000000 |
| GNB | cr4 | 200 | 220,866,006 | 392,737,228 | 0.562376 | 1.000000 |
| HTI | baseline | 200 | 816,857,151 | N/A | N/A | 1.000000 |
| HTI | null | 200 | 816,857,151 | 1,263,411,557 | 0.646549 | 1.000000 |
| HTI | cr2 | 200 | 816,857,151 | 1,263,766,603 | 0.646367 | 1.000000 |
| HTI | cr4 | 200 | 816,857,151 | 1,264,819,030 | 0.645829 | 1.000000 |
| IND | baseline | 200 | 85,534,355,417 | N/A | N/A | 1.000000 |
| IND | null | 200 | 85,534,355,417 | 121,199,282,157 | 0.705733 | 1.000000 |
| IND | cr2 | 200 | 85,534,355,417 | 121,284,622,732 | 0.705237 | 1.000000 |
| IND | cr4 | 200 | 85,534,355,417 | 121,609,729,993 | 0.703351 | 1.000000 |
| IDN | baseline | 200 | 17,201,802,440 | N/A | N/A | 1.000000 |
| IDN | null | 200 | 17,201,802,440 | 26,284,526,644 | 0.654446 | 1.000000 |
| IDN | cr2 | 200 | 17,201,802,440 | 26,295,438,953 | 0.654174 | 1.000000 |
| IDN | cr4 | 200 | 17,201,802,440 | 26,333,798,314 | 0.653221 | 1.000000 |
| IRN | baseline | 200 | 5,096,333,071 | N/A | N/A | 1.000000 |
| IRN | null | 200 | 5,096,333,071 | 8,038,170,056 | 0.634017 | 1.000000 |
| IRN | cr2 | 200 | 5,096,333,071 | 8,041,536,614 | 0.633751 | 1.000000 |
| IRN | cr4 | 200 | 5,096,333,071 | 8,053,368,363 | 0.632820 | 1.000000 |
| IRQ | baseline | 200 | 4,703,679,811 | N/A | N/A | 1.000000 |
| IRQ | null | 200 | 4,703,679,811 | 7,659,097,078 | 0.614130 | 1.000000 |
| IRQ | cr2 | 200 | 4,703,679,811 | 7,660,062,117 | 0.614052 | 1.000000 |
| IRQ | cr4 | 200 | 4,703,679,811 | 7,663,451,467 | 0.613781 | 1.000000 |
| JOR | baseline | 200 | 1,054,502,289 | N/A | N/A | 1.000000 |
| JOR | null | 200 | 1,054,502,289 | 1,139,470,665 | 0.925432 | 1.000000 |
| JOR | cr2 | 200 | 1,054,502,289 | 1,139,786,625 | 0.925175 | 1.000000 |
| JOR | cr4 | 200 | 1,054,502,289 | 1,140,897,400 | 0.924274 | 1.000000 |
| KAZ | baseline | 200 | 1,534,395,708 | N/A | N/A | 1.000000 |
| KAZ | null | 200 | 1,534,395,708 | 2,185,380,812 | 0.702118 | 1.000000 |
| KAZ | cr2 | 200 | 1,534,395,708 | 2,186,468,794 | 0.701769 | 1.000000 |
| KAZ | cr4 | 200 | 1,534,395,708 | 2,190,717,851 | 0.700408 | 1.000000 |
| KEN | baseline | 200 | 5,110,205,914 | N/A | N/A | 1.000000 |
| KEN | null | 200 | 5,110,205,914 | 8,975,975,455 | 0.569320 | 1.000000 |
| KEN | cr2 | 200 | 5,110,205,914 | 8,978,429,262 | 0.569165 | 1.000000 |
| KEN | cr4 | 200 | 5,110,205,914 | 8,988,765,687 | 0.568510 | 1.000000 |
| MDG | baseline | 200 | 3,510,978,586 | N/A | N/A | 1.000000 |
| MDG | null | 200 | 3,510,978,586 | 6,383,284,443 | 0.550027 | 1.000000 |
| MDG | cr2 | 200 | 3,510,978,586 | 6,385,140,377 | 0.549867 | 1.000000 |
| MDG | cr4 | 200 | 3,510,978,586 | 6,392,700,511 | 0.549217 | 1.000000 |
| MWI | baseline | 200 | 2,539,644,902 | N/A | N/A | 1.000000 |
| MWI | null | 200 | 2,539,644,902 | 4,411,875,451 | 0.575638 | 1.000000 |
| MWI | cr2 | 200 | 2,539,644,902 | 4,412,762,103 | 0.575523 | 1.000000 |
| MWI | cr4 | 200 | 2,539,644,902 | 4,416,372,317 | 0.575052 | 1.000000 |
| MYS | baseline | 200 | 2,151,521,761 | N/A | N/A | 1.000000 |
| MYS | null | 200 | 2,151,521,761 | 2,987,674,497 | 0.720133 | 1.000000 |
| MYS | cr2 | 200 | 2,151,521,761 | 2,988,872,804 | 0.719844 | 1.000000 |
| MYS | cr4 | 200 | 2,151,521,761 | 2,993,085,869 | 0.718831 | 1.000000 |
| MLI | baseline | 200 | 3,591,524,921 | N/A | N/A | 1.000000 |
| MLI | null | 200 | 3,591,524,921 | 5,708,764,760 | 0.629125 | 1.000000 |
| MLI | cr2 | 200 | 3,591,524,921 | 5,710,324,642 | 0.628953 | 1.000000 |
| MLI | cr4 | 200 | 3,591,524,921 | 5,716,679,648 | 0.628254 | 1.000000 |
| MEX | baseline | 200 | 7,647,943,459 | N/A | N/A | 1.000000 |
| MEX | null | 200 | 7,647,943,459 | 12,015,658,250 | 0.636498 | 1.000000 |
| MEX | cr2 | 200 | 7,647,943,459 | 12,020,330,063 | 0.636251 | 1.000000 |
| MEX | cr4 | 200 | 7,647,943,459 | 12,034,386,737 | 0.635508 | 1.000000 |
| MAR | baseline | 200 | 2,436,658,270 | N/A | N/A | 1.000000 |
| MAR | null | 200 | 2,436,658,270 | 3,708,673,490 | 0.657016 | 1.000000 |
| MAR | cr2 | 200 | 2,436,658,270 | 3,710,087,692 | 0.656766 | 1.000000 |
| MAR | cr4 | 200 | 2,436,658,270 | 3,714,971,930 | 0.655902 | 1.000000 |
| MOZ | baseline | 200 | 4,430,737,188 | N/A | N/A | 1.000000 |
| MOZ | null | 200 | 4,430,737,188 | 8,336,131,518 | 0.531510 | 1.000000 |
| MOZ | cr2 | 200 | 4,430,737,188 | 8,337,790,435 | 0.531404 | 1.000000 |
| MOZ | cr4 | 200 | 4,430,737,188 | 8,344,544,138 | 0.530974 | 1.000000 |
| MMR | baseline | 200 | 3,147,549,136 | N/A | N/A | 1.000000 |
| MMR | null | 200 | 3,147,549,136 | 4,857,991,110 | 0.647912 | 1.000000 |
| MMR | cr2 | 200 | 3,147,549,136 | 4,861,431,828 | 0.647453 | 1.000000 |
| MMR | cr4 | 200 | 3,147,549,136 | 4,873,303,494 | 0.645876 | 1.000000 |
| NPL | baseline | 200 | 3,395,020,484 | N/A | N/A | 1.000000 |
| NPL | null | 200 | 3,395,020,484 | 2,307,240,350 | 1.471464 | 1.000000 |
| NPL | cr2 | 200 | 3,395,020,484 | 2,308,964,889 | 1.470365 | 1.000000 |
| NPL | cr4 | 200 | 3,395,020,484 | 2,315,539,324 | 1.466190 | 1.000000 |
| NER | baseline | 200 | 6,017,858,349 | N/A | N/A | 1.000000 |
| NER | null | 200 | 6,017,858,349 | 11,420,972,478 | 0.526913 | 1.000000 |
| NER | cr2 | 200 | 6,017,858,349 | 11,422,800,583 | 0.526829 | 1.000000 |
| NER | cr4 | 200 | 6,017,858,349 | 11,430,248,161 | 0.526485 | 1.000000 |
| NGA | baseline | 200 | 25,745,381,192 | N/A | N/A | 1.000000 |
| NGA | null | 200 | 25,745,381,192 | 49,018,091,215 | 0.525222 | 1.000000 |
| NGA | cr2 | 200 | 25,745,381,192 | 49,024,907,305 | 0.525149 | 1.000000 |
| NGA | cr4 | 200 | 25,745,381,192 | 49,053,629,767 | 0.524842 | 1.000000 |
| PAK | baseline | 200 | 21,593,703,421 | N/A | N/A | 1.000000 |
| PAK | null | 200 | 21,593,703,421 | 31,344,848,291 | 0.688908 | 1.000000 |
| PAK | cr2 | 200 | 21,593,703,421 | 31,357,357,000 | 0.688633 | 1.000000 |
| PAK | cr4 | 200 | 21,593,703,421 | 31,404,978,096 | 0.687589 | 1.000000 |
| PER | baseline | 200 | 3,025,056,261 | N/A | N/A | 1.000000 |
| PER | null | 200 | 3,025,056,261 | 3,160,672,467 | 0.957093 | 1.000000 |
| PER | cr2 | 200 | 3,025,056,261 | 3,161,363,007 | 0.956884 | 1.000000 |
| PER | cr4 | 200 | 3,025,056,261 | 3,163,440,360 | 0.956255 | 1.000000 |
| PHL | baseline | 200 | 9,209,239,113 | N/A | N/A | 1.000000 |
| PHL | null | 200 | 9,209,239,113 | 12,249,784,546 | 0.751788 | 1.000000 |
| PHL | cr2 | 200 | 9,209,239,113 | 12,254,697,345 | 0.751486 | 1.000000 |
| PHL | cr4 | 200 | 9,209,239,113 | 12,271,668,376 | 0.750447 | 1.000000 |
| RUS | baseline | 200 | 7,222,947,130 | N/A | N/A | 1.000000 |
| RUS | null | 200 | 7,222,947,130 | 10,089,985,601 | 0.715853 | 1.000000 |
| RUS | cr2 | 200 | 7,222,947,130 | 10,093,670,855 | 0.715592 | 1.000000 |
| RUS | cr4 | 200 | 7,222,947,130 | 10,105,031,661 | 0.714787 | 1.000000 |
| RWA | baseline | 200 | 1,509,396,334 | N/A | N/A | 1.000000 |
| RWA | null | 200 | 1,509,396,334 | 2,549,210,912 | 0.592103 | 1.000000 |
| RWA | cr2 | 200 | 1,509,396,334 | 2,549,940,274 | 0.591934 | 1.000000 |
| RWA | cr4 | 200 | 1,509,396,334 | 2,552,910,746 | 0.591245 | 1.000000 |
| SLE | baseline | 200 | 862,747,365 | N/A | N/A | 1.000000 |
| SLE | null | 200 | 862,747,365 | 1,183,548,504 | 0.728950 | 1.000000 |
| SLE | cr2 | 200 | 862,747,365 | 1,183,855,232 | 0.728761 | 1.000000 |
| SLE | cr4 | 200 | 862,747,365 | 1,185,105,261 | 0.727992 | 1.000000 |
| ZAF | baseline | 200 | 3,894,855,452 | N/A | N/A | 1.000000 |
| ZAF | null | 200 | 3,894,855,452 | 6,039,370,839 | 0.644911 | 1.000000 |
| ZAF | cr2 | 200 | 3,894,855,452 | 6,041,784,000 | 0.644653 | 1.000000 |
| ZAF | cr4 | 200 | 3,894,855,452 | 6,052,304,781 | 0.643533 | 1.000000 |
| LKA | baseline | 200 | 1,091,119,379 | N/A | N/A | 1.000000 |
| LKA | null | 200 | 1,091,119,379 | 1,742,441,334 | 0.626202 | 1.000000 |
| LKA | cr2 | 200 | 1,091,119,379 | 1,743,383,030 | 0.625863 | 1.000000 |
| LKA | cr4 | 200 | 1,091,119,379 | 1,746,635,650 | 0.624698 | 1.000000 |
| SDN | baseline | 200 | 6,021,264,310 | N/A | N/A | 1.000000 |
| SDN | null | 200 | 6,021,264,310 | 9,373,569,794 | 0.642366 | 1.000000 |
| SDN | cr2 | 200 | 6,021,264,310 | 9,375,867,521 | 0.642209 | 1.000000 |
| SDN | cr4 | 200 | 6,021,264,310 | 9,385,224,679 | 0.641568 | 1.000000 |
| TJK | baseline | 200 | 1,039,910,054 | N/A | N/A | 1.000000 |
| TJK | null | 200 | 1,039,910,054 | 1,990,453,667 | 0.522449 | 1.000000 |
| TJK | cr2 | 200 | 1,039,910,054 | 1,990,882,857 | 0.522336 | 1.000000 |
| TJK | cr4 | 200 | 1,039,910,054 | 1,992,477,057 | 0.521918 | 1.000000 |
| TZA | baseline | 200 | 9,900,440,041 | N/A | N/A | 1.000000 |
| TZA | null | 200 | 9,900,440,041 | 18,348,581,297 | 0.539575 | 1.000000 |
| TZA | cr2 | 200 | 9,900,440,041 | 18,351,291,503 | 0.539496 | 1.000000 |
| TZA | cr4 | 200 | 9,900,440,041 | 18,362,708,409 | 0.539160 | 1.000000 |
| THA | baseline | 200 | 3,058,821,760 | N/A | N/A | 1.000000 |
| THA | null | 200 | 3,058,821,760 | 4,246,282,646 | 0.720353 | 1.000000 |
| THA | cr2 | 200 | 3,058,821,760 | 4,248,481,189 | 0.719980 | 1.000000 |
| THA | cr4 | 200 | 3,058,821,760 | 4,256,213,279 | 0.718672 | 1.000000 |
| TGO | baseline | 200 | 1,140,885,739 | N/A | N/A | 1.000000 |
| TGO | null | 200 | 1,140,885,739 | 1,776,257,921 | 0.642297 | 1.000000 |
| TGO | cr2 | 200 | 1,140,885,739 | 1,776,715,320 | 0.642132 | 1.000000 |
| TGO | cr4 | 200 | 1,140,885,739 | 1,778,578,064 | 0.641459 | 1.000000 |
| TUR | baseline | 200 | 4,909,246,270 | N/A | N/A | 1.000000 |
| TUR | null | 200 | 4,909,246,270 | 7,288,670,337 | 0.673545 | 1.000000 |
| TUR | cr2 | 200 | 4,909,246,270 | 7,294,409,969 | 0.673015 | 1.000000 |
| TUR | cr4 | 200 | 4,909,246,270 | 7,314,589,936 | 0.671158 | 1.000000 |
| UGA | baseline | 200 | 6,323,859,701 | N/A | N/A | 1.000000 |
| UGA | null | 200 | 6,323,859,701 | 9,639,984,192 | 0.656003 | 1.000000 |
| UGA | cr2 | 200 | 6,323,859,701 | 9,642,066,311 | 0.655861 | 1.000000 |
| UGA | cr4 | 200 | 6,323,859,701 | 9,650,545,721 | 0.655285 | 1.000000 |
| UKR | baseline | 200 | 1,676,223,501 | N/A | N/A | 1.000000 |
| UKR | null | 200 | 1,676,223,501 | 2,437,457,411 | 0.687693 | 1.000000 |
| UKR | cr2 | 200 | 1,676,223,501 | 2,438,485,888 | 0.687403 | 1.000000 |
| UKR | cr4 | 200 | 1,676,223,501 | 2,441,631,760 | 0.686518 | 1.000000 |
| UZB | baseline | 200 | 2,588,935,389 | N/A | N/A | 1.000000 |
| UZB | null | 200 | 2,588,935,389 | 3,635,700,566 | 0.712087 | 1.000000 |
| UZB | cr2 | 200 | 2,588,935,389 | 3,636,654,500 | 0.711900 | 1.000000 |
| UZB | cr4 | 200 | 2,588,935,389 | 3,640,285,635 | 0.711190 | 1.000000 |
| VNM | baseline | 200 | 5,702,144,567 | N/A | N/A | 1.000000 |
| VNM | null | 200 | 5,702,144,567 | 8,385,266,087 | 0.680020 | 1.000000 |
| VNM | cr2 | 200 | 5,702,144,567 | 8,390,585,041 | 0.679588 | 1.000000 |
| VNM | cr4 | 200 | 5,702,144,567 | 8,408,958,655 | 0.678104 | 1.000000 |
