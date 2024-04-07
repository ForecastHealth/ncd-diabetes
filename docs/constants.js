export const DISEASE_NAME = "diabetes"

export const INTERVENTIONS = [
    "RetinopathyScrn",
    "NeuropathyScr",
    "NephropathyScr",
    "IntsvGlycControl",
    "StdGlycControl"
];

export const TARGET_COVERAGES = {
    "RetinopathyScrn": "RetinopathyScrn_Coverage",
    "NeuropathyScr": "NeuropathyScr_Coverage",
    "NephropathyScr": "NephropathyScr_Coverage",
    "IntsvGlycControl": "IntsvGlycControl_Coverage",
    "StdGlycControl": "StdGlycControl_Coverage"
};

export const STARTING_COVERAGES = {
    "RetinopathyScrn": "RetinopathyScrn_StartingCoverage",
    "NeuropathyScr": "NeuropathyScr_StartingCoverage",
    "NephropathyScr": "NephropathyScr_StartingCoverage",
    "IntsvGlycControl": "IntsvGlycControl_StartingCoverage",
    "StdGlycControl": "StdGlycControl_StartingCoverage"
};

export const DEFAULT_COVERAGE = 0.05;

export const NULL_COVERAGE_CHANGES = {
    "RetinopathyScrn": 0.0,
    "NeuropathyScr": 0.0,
    "NephropathyScr": 0.0,
    "IntsvGlycControl": 0.0,
    "StdGlycControl": 0.0
}

export const D1_COVERAGE_CHANGES = {
    "NeuropathyScr_Coverage": 0.95
};

export const D2_COVERAGE_CHANGES = {
    "RetinopathyScrn_Coverage": 0.95
};

export const D3_COVERAGE_CHANGES = {
    "StdGlycControl_Coverage": 0.95,
    "IntsvGlycControl_Coverage": 0.95
};

export const D5_COVERAGE_CHANGES = {
    "NephropathyScr_Coverage": 0.95
};

export const RESULTS_QUERY = `
SELECT strftime("%Y", timestamp) AS year,
  element_label,
  AVG(value) AS "AVG(value)"
FROM results
WHERE event_type IN ("BALANCE_SET")
AND element_label IN (
    "DsFreeSus", 
    "DsFreeSus -> DiabetesEpsd", 
    "DiabetesEpsd",
    "DiabetesEpsd -> DiabetesEpsd Mortality", 
    "Deceased",
    "DsFreeSus -> DsFreeSus HYL", 
    "DiabetesEpsd -> DiabetesEpsd HYL"
)
GROUP BY year, element_label
ORDER BY "AVG(value)" DESC
`;
