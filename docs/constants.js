export const DISEASE_NAME = "asthma"

export const INTERVENTIONS = [
    'InhaledSalbutamol',
    'IpratropiumInhaler',
    'OralPrednisolone'
];

export const TARGET_COVERAGES = {
    'InhaledSalbutamol': 'InhaledSalbutamol_Coverage',
    'IpratropiumInhaler': 'IpratropiumInhaler_Coverage',
    'OralPrednisolone': 'OralPrednisolone_Coverage',
};

export const STARTING_COVERAGES = {
    'InhaledSalbutamol': 'InhaledSalbutamol_StartingCoverage',
    'IpratropiumInhaler': 'IpratropiumInhaler_StartingCoverage',
    'OralPrednisolone': 'OralPrednisolone_StartingCoverage',
};

export const DEFAULT_COVERAGE = 0.05;

export const NULL_COVERAGE_CHANGES = {
    'OralPrednisolone': 0.00,
    'InhaledSalbutamol': 0.00,
    'IpratropiumInhaler': 0.00,
}

export const CR2_COVERAGE_CHANGES = {
    'OralPrednisolone': 0.95,
};

export const CR4_COVERAGE_CHANGES = {
    'InhaledSalbutamol': 0.95,
    'IpratropiumInhaler': 0.95,
};

export const RESULTS_QUERY = `
SELECT strftime("%Y", timestamp) AS year,
  element_label,
  AVG(value) AS "AVG(value)"
FROM results
WHERE event_type IN ("BALANCE_SET")
AND element_label IN ("DsFreeSus", "DsFreeSus -> COPDEpsd", "COPDEpsd",
                    "COPDEpsd -> COPDEpsd Mortality", "Deceased",
                    "DsFreeSus -> DsFreeSus HYL", "COPDEpsd -> COPDEpsd HYL")
GROUP BY year, element_label
ORDER BY "AVG(value)" DESC
`;
