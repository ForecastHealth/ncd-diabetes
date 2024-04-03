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
| AFG | null | 200 | 4,126,365,059 | 5,757,189,149 | 0.716733 | 0.999948 |
| AFG | cr2 | 200 | 4,127,276,498 | 5,759,100,686 | 0.716653 | 1.000169 |
| AFG | cr4 | 200 | 4,129,742,080 | 5,766,207,170 | 0.716197 | 1.000766 |
| DZA | baseline | 200 | 3,413,762,017 | N/A | N/A | 1.000000 |
| DZA | null | 200 | 3,413,545,264 | 5,289,116,838 | 0.645390 | 0.999937 |
| DZA | cr2 | 200 | 3,414,466,608 | 5,290,811,515 | 0.645358 | 1.000206 |
| DZA | cr4 | 200 | 3,416,958,984 | 5,296,663,433 | 0.645115 | 1.000936 |
| AGO | baseline | 200 | 5,709,573,967 | N/A | N/A | 1.000000 |
| AGO | null | 200 | 5,709,323,713 | 12,042,158,896 | 0.474111 | 0.999956 |
| AGO | cr2 | 200 | 5,710,387,459 | 12,044,241,336 | 0.474118 | 1.000142 |
| AGO | cr4 | 200 | 5,713,265,056 | 12,053,017,357 | 0.474011 | 1.000646 |
| ARG | baseline | 200 | 2,723,950,869 | N/A | N/A | 1.000000 |
| ARG | null | 200 | 2,723,639,032 | 4,449,630,159 | 0.612105 | 0.999886 |
| ARG | cr2 | 200 | 2,724,964,544 | 4,451,972,285 | 0.612080 | 1.000372 |
| ARG | cr4 | 200 | 2,728,550,256 | 4,459,013,719 | 0.611918 | 1.001688 |
| BGD | baseline | 200 | 10,552,987,667 | N/A | N/A | 1.000000 |
| BGD | null | 200 | 10,551,498,810 | 13,677,176,014 | 0.771468 | 0.999859 |
| BGD | cr2 | 200 | 10,557,827,432 | 13,687,069,564 | 0.771372 | 1.000459 |
| BGD | cr4 | 200 | 10,574,947,325 | 13,724,747,645 | 0.770502 | 1.002081 |
| BRA | baseline | 200 | 11,492,596,312 | N/A | N/A | 1.000000 |
| BRA | null | 200 | 11,491,363,689 | 15,610,811,582 | 0.736116 | 0.999893 |
| BRA | cr2 | 200 | 11,496,603,148 | 15,619,659,263 | 0.736034 | 1.000349 |
| BRA | cr4 | 200 | 11,510,776,686 | 15,646,272,403 | 0.735688 | 1.001582 |
| BFA | baseline | 200 | 2,770,886,665 | N/A | N/A | 1.000000 |
| BFA | null | 200 | 2,770,787,233 | 5,448,439,531 | 0.508547 | 0.999964 |
| BFA | cr2 | 200 | 2,771,209,887 | 5,449,393,435 | 0.508535 | 1.000117 |
| BFA | cr4 | 200 | 2,772,353,233 | 5,453,279,586 | 0.508383 | 1.000529 |
| BDI | baseline | 200 | 1,592,347,738 | N/A | N/A | 1.000000 |
| BDI | null | 200 | 1,592,279,563 | 3,338,323,123 | 0.476970 | 0.999957 |
| BDI | cr2 | 200 | 1,592,569,350 | 3,338,979,011 | 0.476963 | 1.000139 |
| BDI | cr4 | 200 | 1,593,353,270 | 3,341,650,210 | 0.476816 | 1.000631 |
| CMR | baseline | 200 | 3,677,773,572 | N/A | N/A | 1.000000 |
| CMR | null | 200 | 3,677,570,257 | 6,029,655,943 | 0.609914 | 0.999945 |
| CMR | cr2 | 200 | 3,678,434,481 | 6,031,281,946 | 0.609893 | 1.000180 |
| CMR | cr4 | 200 | 3,680,772,341 | 6,038,133,103 | 0.609588 | 1.000815 |
| CAF | baseline | 200 | 386,789,534 | N/A | N/A | 1.000000 |
| CAF | null | 200 | 386,775,443 | 838,987,608 | 0.461003 | 0.999964 |
| CAF | cr2 | 200 | 386,835,338 | 839,191,422 | 0.460962 | 1.000118 |
| CAF | cr4 | 200 | 386,997,364 | 840,021,702 | 0.460699 | 1.000537 |
| TCD | baseline | 200 | 2,926,064,184 | N/A | N/A | 1.000000 |
| TCD | null | 200 | 2,925,959,592 | 4,131,917,958 | 0.708136 | 0.999964 |
| TCD | cr2 | 200 | 2,926,404,177 | 4,132,696,327 | 0.708110 | 1.000116 |
| TCD | cr4 | 200 | 2,927,606,848 | 4,135,867,643 | 0.707858 | 1.000527 |
| CHN | baseline | 200 | 60,048,382,408 | N/A | N/A | 1.000000 |
| CHN | null | 200 | 60,040,157,835 | 102,124,915,511 | 0.587909 | 0.999863 |
| CHN | cr2 | 200 | 60,075,117,687 | 102,178,417,943 | 0.587943 | 1.000445 |
| CHN | cr4 | 200 | 60,169,689,440 | 102,366,324,469 | 0.587788 | 1.002020 |
| COL | baseline | 200 | 3,577,409,955 | N/A | N/A | 1.000000 |
| COL | null | 200 | 3,577,042,522 | 4,057,584,780 | 0.881569 | 0.999897 |
| COL | cr2 | 200 | 3,578,604,356 | 4,059,685,817 | 0.881498 | 1.000334 |
| COL | cr4 | 200 | 3,582,829,356 | 4,066,004,830 | 0.881167 | 1.001515 |
| COD | baseline | 200 | 16,788,660,325 | N/A | N/A | 1.000000 |
| COD | null | 200 | 16,787,917,517 | 24,858,858,200 | 0.675329 | 0.999956 |
| COD | cr2 | 200 | 16,791,074,940 | 24,864,684,269 | 0.675298 | 1.000144 |
| COD | cr4 | 200 | 16,799,616,251 | 24,888,420,633 | 0.674997 | 1.000653 |
| CIV | baseline | 200 | 3,652,350,562 | N/A | N/A | 1.000000 |
| CIV | null | 200 | 3,652,206,613 | 6,170,958,634 | 0.591838 | 0.999961 |
| CIV | cr2 | 200 | 3,652,818,492 | 6,172,121,479 | 0.591825 | 1.000128 |
| CIV | cr4 | 200 | 3,654,473,717 | 6,177,020,189 | 0.591624 | 1.000581 |
| DOM | baseline | 200 | 727,757,829 | N/A | N/A | 1.000000 |
| DOM | null | 200 | 727,729,167 | 1,028,271,946 | 0.707721 | 0.999961 |
| DOM | cr2 | 200 | 727,850,998 | 1,028,511,630 | 0.707674 | 1.000128 |
| DOM | cr4 | 200 | 728,180,568 | 1,029,232,473 | 0.707499 | 1.000581 |
| ECU | baseline | 200 | 1,562,707,128 | N/A | N/A | 1.000000 |
| ECU | null | 200 | 1,562,685,282 | 1,892,583,046 | 0.825689 | 0.999986 |
| ECU | cr2 | 200 | 1,562,778,142 | 1,893,034,296 | 0.825541 | 1.000045 |
| ECU | cr4 | 200 | 1,563,029,343 | 1,894,391,312 | 0.825083 | 1.000206 |
| EGY | baseline | 200 | 9,763,892,494 | N/A | N/A | 1.000000 |
| EGY | null | 200 | 9,763,137,696 | 16,545,135,936 | 0.590091 | 0.999923 |
| EGY | cr2 | 200 | 9,766,346,087 | 16,551,131,939 | 0.590071 | 1.000251 |
| EGY | cr4 | 200 | 9,775,025,275 | 16,571,838,386 | 0.589858 | 1.001140 |
| ERI | baseline | 200 | 335,342,692 | N/A | N/A | 1.000000 |
| ERI | null | 200 | 335,323,539 | 671,973,039 | 0.499013 | 0.999943 |
| ERI | cr2 | 200 | 335,404,951 | 672,153,304 | 0.499001 | 1.000186 |
| ERI | cr4 | 200 | 335,625,185 | 672,887,138 | 0.498784 | 1.000842 |
| ETH | baseline | 200 | 14,322,258,414 | N/A | N/A | 1.000000 |
| ETH | null | 200 | 14,321,754,987 | 20,336,516,029 | 0.704238 | 0.999965 |
| ETH | cr2 | 200 | 14,323,894,885 | 20,340,252,305 | 0.704214 | 1.000114 |
| ETH | cr4 | 200 | 14,329,683,640 | 20,355,470,893 | 0.703972 | 1.000518 |
| GMB | baseline | 200 | 301,555,515 | N/A | N/A | 1.000000 |
| GMB | null | 200 | 301,538,693 | 590,155,049 | 0.510948 | 0.999944 |
| GMB | cr2 | 200 | 301,610,195 | 590,305,161 | 0.510939 | 1.000181 |
| GMB | cr4 | 200 | 301,803,619 | 590,916,869 | 0.510738 | 1.000823 |
| GHA | baseline | 200 | 3,330,452,502 | N/A | N/A | 1.000000 |
| GHA | null | 200 | 3,330,289,157 | 5,503,678,883 | 0.605102 | 0.999951 |
| GHA | cr2 | 200 | 3,330,983,480 | 5,505,011,987 | 0.605082 | 1.000159 |
| GHA | cr4 | 200 | 3,332,861,730 | 5,510,626,243 | 0.604806 | 1.000723 |
| GTM | baseline | 200 | 1,344,238,381 | N/A | N/A | 1.000000 |
| GTM | null | 200 | 1,344,201,800 | 2,410,772,091 | 0.557581 | 0.999973 |
| GTM | cr2 | 200 | 1,344,357,291 | 2,411,145,766 | 0.557560 | 1.000088 |
| GTM | cr4 | 200 | 1,344,777,918 | 2,412,269,754 | 0.557474 | 1.000401 |
| GIN | baseline | 200 | 1,583,378,243 | N/A | N/A | 1.000000 |
| GIN | null | 200 | 1,583,295,181 | 3,025,650,651 | 0.523291 | 0.999948 |
| GIN | cr2 | 200 | 1,583,648,248 | 3,026,425,379 | 0.523274 | 1.000171 |
| GIN | cr4 | 200 | 1,584,603,349 | 3,029,581,402 | 0.523044 | 1.000774 |
| GNB | baseline | 200 | 220,866,006 | N/A | N/A | 1.000000 |
| GNB | null | 200 | 220,854,098 | 392,220,922 | 0.563086 | 0.999946 |
| GNB | cr2 | 200 | 220,904,718 | 392,322,678 | 0.563069 | 1.000175 |
| GNB | cr4 | 200 | 221,041,654 | 392,737,228 | 0.562823 | 1.000795 |
| HTI | baseline | 200 | 816,857,151 | N/A | N/A | 1.000000 |
| HTI | null | 200 | 816,823,187 | 1,263,411,557 | 0.646522 | 0.999958 |
| HTI | cr2 | 200 | 816,967,555 | 1,263,766,603 | 0.646454 | 1.000135 |
| HTI | cr4 | 200 | 817,358,091 | 1,264,819,030 | 0.646225 | 1.000613 |
| IND | baseline | 200 | 85,534,355,417 | N/A | N/A | 1.000000 |
| IND | null | 200 | 85,520,850,820 | 121,199,282,157 | 0.705622 | 0.999842 |
| IND | cr2 | 200 | 85,578,254,252 | 121,284,622,732 | 0.705599 | 1.000513 |
| IND | cr4 | 200 | 85,733,539,323 | 121,609,729,993 | 0.704989 | 1.002329 |
| IDN | baseline | 200 | 17,201,802,440 | N/A | N/A | 1.000000 |
| IDN | null | 200 | 17,200,459,203 | 26,284,526,644 | 0.654395 | 0.999922 |
| IDN | cr2 | 200 | 17,206,168,846 | 26,295,438,953 | 0.654340 | 1.000254 |
| IDN | cr4 | 200 | 17,221,614,303 | 26,333,798,314 | 0.653974 | 1.001152 |
| IRN | baseline | 200 | 5,096,333,071 | N/A | N/A | 1.000000 |
| IRN | null | 200 | 5,095,865,395 | 8,038,170,056 | 0.633958 | 0.999908 |
| IRN | cr2 | 200 | 5,097,853,327 | 8,041,536,614 | 0.633940 | 1.000298 |
| IRN | cr4 | 200 | 5,103,230,988 | 8,053,368,363 | 0.633677 | 1.001354 |
| IRQ | baseline | 200 | 4,703,679,811 | N/A | N/A | 1.000000 |
| IRQ | null | 200 | 4,703,562,938 | 7,659,097,078 | 0.614115 | 0.999975 |
| IRQ | cr2 | 200 | 4,704,059,727 | 7,660,062,117 | 0.614102 | 1.000081 |
| IRQ | cr4 | 200 | 4,705,403,616 | 7,663,451,467 | 0.614006 | 1.000366 |
| JOR | baseline | 200 | 1,054,502,289 | N/A | N/A | 1.000000 |
| JOR | null | 200 | 1,054,445,132 | 1,139,470,665 | 0.925382 | 0.999946 |
| JOR | cr2 | 200 | 1,054,688,085 | 1,139,786,625 | 0.925338 | 1.000176 |
| JOR | cr4 | 200 | 1,055,345,309 | 1,140,897,400 | 0.925013 | 1.000799 |
| KAZ | baseline | 200 | 1,534,395,708 | N/A | N/A | 1.000000 |
| KAZ | null | 200 | 1,534,252,437 | 2,185,380,812 | 0.702053 | 0.999907 |
| KAZ | cr2 | 200 | 1,534,861,434 | 2,186,468,794 | 0.701982 | 1.000304 |
| KAZ | cr4 | 200 | 1,536,508,865 | 2,190,717,851 | 0.701372 | 1.001377 |
| KEN | baseline | 200 | 5,110,205,914 | N/A | N/A | 1.000000 |
| KEN | null | 200 | 5,109,949,017 | 8,975,975,455 | 0.569292 | 0.999950 |
| KEN | cr2 | 200 | 5,111,040,996 | 8,978,429,262 | 0.569258 | 1.000163 |
| KEN | cr4 | 200 | 5,113,994,967 | 8,988,765,687 | 0.568932 | 1.000741 |
| MDG | baseline | 200 | 3,510,978,586 | N/A | N/A | 1.000000 |
| MDG | null | 200 | 3,510,753,603 | 6,383,284,443 | 0.549992 | 0.999936 |
| MDG | cr2 | 200 | 3,511,709,926 | 6,385,140,377 | 0.549982 | 1.000208 |
| MDG | cr4 | 200 | 3,514,296,927 | 6,392,700,511 | 0.549736 | 1.000945 |
| MWI | baseline | 200 | 2,539,644,902 | N/A | N/A | 1.000000 |
| MWI | null | 200 | 2,539,540,286 | 4,411,875,451 | 0.575615 | 0.999959 |
| MWI | cr2 | 200 | 2,539,984,973 | 4,412,762,103 | 0.575600 | 1.000134 |
| MWI | cr4 | 200 | 2,541,187,920 | 4,416,372,317 | 0.575402 | 1.000608 |
| MYS | baseline | 200 | 2,151,521,761 | N/A | N/A | 1.000000 |
| MYS | null | 200 | 2,151,335,991 | 2,987,674,497 | 0.720070 | 0.999914 |
| MYS | cr2 | 200 | 2,152,125,636 | 2,988,872,804 | 0.720046 | 1.000281 |
| MYS | cr4 | 200 | 2,154,261,746 | 2,993,085,869 | 0.719746 | 1.001274 |
| MLI | baseline | 200 | 3,591,524,921 | N/A | N/A | 1.000000 |
| MLI | null | 200 | 3,591,331,006 | 5,708,764,760 | 0.629091 | 0.999946 |
| MLI | cr2 | 200 | 3,592,155,274 | 5,710,324,642 | 0.629063 | 1.000176 |
| MLI | cr4 | 200 | 3,594,385,044 | 5,716,679,648 | 0.628754 | 1.000796 |
| MEX | baseline | 200 | 7,647,943,459 | N/A | N/A | 1.000000 |
| MEX | null | 200 | 7,647,334,598 | 12,015,658,250 | 0.636447 | 0.999920 |
| MEX | cr2 | 200 | 7,649,922,655 | 12,020,330,063 | 0.636415 | 1.000259 |
| MEX | cr4 | 200 | 7,656,923,745 | 12,034,386,737 | 0.636254 | 1.001174 |
| MAR | baseline | 200 | 2,436,658,270 | N/A | N/A | 1.000000 |
| MAR | null | 200 | 2,436,496,905 | 3,708,673,490 | 0.656973 | 0.999934 |
| MAR | cr2 | 200 | 2,437,182,813 | 3,710,087,692 | 0.656907 | 1.000215 |
| MAR | cr4 | 200 | 2,439,038,298 | 3,714,971,930 | 0.656543 | 1.000977 |
| MOZ | baseline | 200 | 4,430,737,188 | N/A | N/A | 1.000000 |
| MOZ | null | 200 | 4,430,558,330 | 8,336,131,518 | 0.531489 | 0.999960 |
| MOZ | cr2 | 200 | 4,431,318,595 | 8,337,790,435 | 0.531474 | 1.000131 |
| MOZ | cr4 | 200 | 4,433,375,229 | 8,344,544,138 | 0.531290 | 1.000595 |
| MMR | baseline | 200 | 3,147,549,136 | N/A | N/A | 1.000000 |
| MMR | null | 200 | 3,147,129,639 | 4,857,991,110 | 0.647825 | 0.999867 |
| MMR | cr2 | 200 | 3,148,912,776 | 4,861,431,828 | 0.647734 | 1.000433 |
| MMR | cr4 | 200 | 3,153,736,433 | 4,873,303,494 | 0.647146 | 1.001966 |
| NPL | baseline | 200 | 3,395,020,484 | N/A | N/A | 1.000000 |
| NPL | null | 200 | 3,394,509,629 | 2,307,240,350 | 1.471242 | 0.999850 |
| NPL | cr2 | 200 | 3,396,681,098 | 2,308,964,889 | 1.471084 | 1.000489 |
| NPL | cr4 | 200 | 3,402,555,254 | 2,315,539,324 | 1.469444 | 1.002219 |
| NER | baseline | 200 | 6,017,858,349 | N/A | N/A | 1.000000 |
| NER | null | 200 | 6,017,635,354 | 11,420,972,478 | 0.526893 | 0.999963 |
| NER | cr2 | 200 | 6,018,583,231 | 11,422,800,583 | 0.526892 | 1.000120 |
| NER | cr4 | 200 | 6,021,147,383 | 11,430,248,161 | 0.526773 | 1.000547 |
| NGA | baseline | 200 | 25,745,381,192 | N/A | N/A | 1.000000 |
| NGA | null | 200 | 25,744,591,424 | 49,018,091,215 | 0.525206 | 0.999969 |
| NGA | cr2 | 200 | 25,747,948,457 | 49,024,907,305 | 0.525201 | 1.000100 |
| NGA | cr4 | 200 | 25,757,029,746 | 49,053,629,767 | 0.525079 | 1.000452 |
| PAK | baseline | 200 | 21,593,703,421 | N/A | N/A | 1.000000 |
| PAK | null | 200 | 21,592,257,312 | 31,344,848,291 | 0.688861 | 0.999933 |
| PAK | cr2 | 200 | 21,598,404,227 | 31,357,357,000 | 0.688783 | 1.000218 |
| PAK | cr4 | 200 | 21,615,032,574 | 31,404,978,096 | 0.688268 | 1.000988 |
| PER | baseline | 200 | 3,025,056,261 | N/A | N/A | 1.000000 |
| PER | null | 200 | 3,025,018,958 | 3,160,672,467 | 0.957081 | 0.999988 |
| PER | cr2 | 200 | 3,025,177,518 | 3,161,363,007 | 0.956922 | 1.000040 |
| PER | cr4 | 200 | 3,025,606,447 | 3,163,440,360 | 0.956429 | 1.000182 |
| PHL | baseline | 200 | 9,209,239,113 | N/A | N/A | 1.000000 |
| PHL | null | 200 | 9,208,560,235 | 12,249,784,546 | 0.751732 | 0.999926 |
| PHL | cr2 | 200 | 9,211,445,914 | 12,254,697,345 | 0.751667 | 1.000240 |
| PHL | cr4 | 200 | 9,219,252,121 | 12,271,668,376 | 0.751263 | 1.001087 |
| RUS | baseline | 200 | 7,222,947,130 | N/A | N/A | 1.000000 |
| RUS | null | 200 | 7,222,397,142 | 10,089,985,601 | 0.715799 | 0.999924 |
| RUS | cr2 | 200 | 7,224,734,952 | 10,093,670,855 | 0.715769 | 1.000248 |
| RUS | cr4 | 200 | 7,231,059,086 | 10,105,031,661 | 0.715590 | 1.001123 |
| RWA | baseline | 200 | 1,509,396,334 | N/A | N/A | 1.000000 |
| RWA | null | 200 | 1,509,315,832 | 2,549,210,912 | 0.592072 | 0.999947 |
| RWA | cr2 | 200 | 1,509,658,018 | 2,549,940,274 | 0.592037 | 1.000173 |
| RWA | cr4 | 200 | 1,510,583,685 | 2,552,910,746 | 0.591710 | 1.000787 |
| SLE | baseline | 200 | 862,747,365 | N/A | N/A | 1.000000 |
| SLE | null | 200 | 862,702,413 | 1,183,548,504 | 0.728912 | 0.999948 |
| SLE | cr2 | 200 | 862,893,489 | 1,183,855,232 | 0.728884 | 1.000169 |
| SLE | cr4 | 200 | 863,410,376 | 1,185,105,261 | 0.728552 | 1.000768 |
| ZAF | baseline | 200 | 3,894,855,452 | N/A | N/A | 1.000000 |
| ZAF | null | 200 | 3,894,532,273 | 6,039,370,839 | 0.644857 | 0.999917 |
| ZAF | cr2 | 200 | 3,895,905,997 | 6,041,784,000 | 0.644827 | 1.000270 |
| ZAF | cr4 | 200 | 3,899,622,132 | 6,052,304,781 | 0.644320 | 1.001224 |
| LKA | baseline | 200 | 1,091,119,379 | N/A | N/A | 1.000000 |
| LKA | null | 200 | 1,091,015,350 | 1,742,441,334 | 0.626142 | 0.999905 |
| LKA | cr2 | 200 | 1,091,457,539 | 1,743,383,030 | 0.626057 | 1.000310 |
| LKA | cr4 | 200 | 1,092,653,726 | 1,746,635,650 | 0.625576 | 1.001406 |
| SDN | baseline | 200 | 6,021,264,310 | N/A | N/A | 1.000000 |
| SDN | null | 200 | 6,020,989,730 | 9,373,569,794 | 0.642337 | 0.999954 |
| SDN | cr2 | 200 | 6,022,156,879 | 9,375,867,521 | 0.642304 | 1.000148 |
| SDN | cr4 | 200 | 6,025,314,196 | 9,385,224,679 | 0.642000 | 1.000673 |
| TJK | baseline | 200 | 1,039,910,054 | N/A | N/A | 1.000000 |
| TJK | null | 200 | 1,039,863,779 | 1,990,453,667 | 0.522426 | 0.999956 |
| TJK | cr2 | 200 | 1,040,060,476 | 1,990,882,857 | 0.522412 | 1.000145 |
| TJK | cr4 | 200 | 1,040,592,573 | 1,992,477,057 | 0.522261 | 1.000656 |
| TZA | baseline | 200 | 9,900,440,041 | N/A | N/A | 1.000000 |
| TZA | null | 200 | 9,900,097,713 | 18,348,581,297 | 0.539557 | 0.999965 |
| TZA | cr2 | 200 | 9,901,552,831 | 18,351,291,503 | 0.539556 | 1.000112 |
| TZA | cr4 | 200 | 9,905,489,147 | 18,362,708,409 | 0.539435 | 1.000510 |
| THA | baseline | 200 | 3,058,821,760 | N/A | N/A | 1.000000 |
| THA | null | 200 | 3,058,480,126 | 4,246,282,646 | 0.720272 | 0.999888 |
| THA | cr2 | 200 | 3,059,932,295 | 4,248,481,189 | 0.720241 | 1.000363 |
| THA | cr4 | 200 | 3,063,860,635 | 4,256,213,279 | 0.719856 | 1.001647 |
| TGO | baseline | 200 | 1,140,885,739 | N/A | N/A | 1.000000 |
| TGO | null | 200 | 1,140,829,485 | 1,776,257,921 | 0.642266 | 0.999951 |
| TGO | cr2 | 200 | 1,141,068,603 | 1,776,715,320 | 0.642235 | 1.000160 |
| TGO | cr4 | 200 | 1,141,715,455 | 1,778,578,064 | 0.641926 | 1.000727 |
| TUR | baseline | 200 | 4,909,246,270 | N/A | N/A | 1.000000 |
| TUR | null | 200 | 4,908,443,486 | 7,288,670,337 | 0.673435 | 0.999836 |
| TUR | cr2 | 200 | 4,911,855,847 | 7,294,409,969 | 0.673373 | 1.000532 |
| TUR | cr4 | 200 | 4,921,086,807 | 7,314,589,936 | 0.672777 | 1.002412 |
| UGA | baseline | 200 | 6,323,859,701 | N/A | N/A | 1.000000 |
| UGA | null | 200 | 6,323,606,167 | 9,639,984,192 | 0.655977 | 0.999960 |
| UGA | cr2 | 200 | 6,324,683,854 | 9,642,066,311 | 0.655947 | 1.000130 |
| UGA | cr4 | 200 | 6,327,599,162 | 9,650,545,721 | 0.655673 | 1.000591 |
| UKR | baseline | 200 | 1,676,223,501 | N/A | N/A | 1.000000 |
| UKR | null | 200 | 1,676,082,174 | 2,437,457,411 | 0.687635 | 0.999916 |
| UKR | cr2 | 200 | 1,676,682,909 | 2,438,485,888 | 0.687592 | 1.000274 |
| UKR | cr4 | 200 | 1,678,307,988 | 2,441,631,760 | 0.687371 | 1.001244 |
| UZB | baseline | 200 | 2,588,935,389 | N/A | N/A | 1.000000 |
| UZB | null | 200 | 2,588,816,963 | 3,635,700,566 | 0.712055 | 0.999954 |
| UZB | cr2 | 200 | 2,589,320,351 | 3,636,654,500 | 0.712006 | 1.000149 |
| UZB | cr4 | 200 | 2,590,682,092 | 3,640,285,635 | 0.711670 | 1.000675 |
| VNM | baseline | 200 | 5,702,144,567 | N/A | N/A | 1.000000 |
| VNM | null | 200 | 5,701,415,584 | 8,385,266,087 | 0.679933 | 0.999872 |
| VNM | cr2 | 200 | 5,704,514,241 | 8,390,585,041 | 0.679871 | 1.000416 |
| VNM | cr4 | 200 | 5,712,896,581 | 8,408,958,655 | 0.679382 | 1.001886 |
