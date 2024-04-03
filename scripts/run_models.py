"""
run_models.py

Runs a list of models for a list of scenarios.
"""
import requests
import json
from io import StringIO
from country_metadata import get_countries_by_tags
from datetime import datetime
import pandas as pd

RUN_ENDPOINT = "https://api.forecasthealth.org/run/appendix_3"
QUERY_ENDPOINT = "https://api.forecasthealth.org/query"
MODEL_FILEPATH = "copd_baseline.json"
SCENARIOS = ["baseline", "null", "cr2", "cr4"]
RESULTS_FILEPATH = "results.json"
QUERY = """
SELECT strftime("%Y", timestamp) AS year,
  element_label,
  AVG(value) AS "AVG(value)"
FROM results
WHERE event_type IN ("BALANCE_SET")
AND element_label IN ("Healthy Years Lived")
GROUP BY year, element_label
ORDER BY "AVG(value)" DESC
"""


def change_country(botech: dict, iso3: str):
    for node in botech["nodes"]:
        generate_array = node.get("generate_array")
        if generate_array:
            parameters = generate_array.get("parameters", {})
            if "country" in parameters.keys():
                parameters["country"] = iso3

    for edge in botech["links"]:
        generate_array = edge.get("generate_array")
        if generate_array:
            parameters = generate_array.get("parameters", {})
            if "country" in parameters.keys():
                parameters["country"] = iso3


def convert_scenario(botech: dict, scenario: str):
    if scenario == "baseline":
        for node in botech["nodes"]:
            if node["label"] == "InhaledSalbutamol_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.05
            if node["label"] == "IpratropiumInhaler_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.05
            if node["label"] == "OralPrednisolone_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.05

    elif scenario == "null":
        for node in botech["nodes"]:
            if node["label"] == "InhaledSalbutamol_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.00
            if node["label"] == "IpratropiumInhaler_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.00
            if node["label"] == "OralPrednisolone_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.00

    elif scenario == "cr2":
        for node in botech["nodes"]:
            if node["label"] == "InhaledSalbutamol_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.05
            if node["label"] == "IpratropiumInhaler_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.05
            if node["label"] == "OralPrednisolone_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.95

    elif scenario == "cr4":
        for node in botech["nodes"]:
            if node["label"] == "InhaledSalbutamol_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.95
            if node["label"] == "IpratropiumInhaler_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.95
            if node["label"] == "OralPrednisolone_Coverage":
                node["generate_array"]["parameters"]["value"] = 0.05

    else:
        raise KeyError(f"{scenario} is not recognised")


def change_time_horizon(botech: dict, start_year: int, end_year: int):
    botech["runtime"]["startYear"] = start_year
    botech["runtime"]["endYear"] = end_year


def run_request(session, botech: dict, scenario: str, iso3: str):
    request = {
        "data": botech,
        "store": False,
        "file_id": f"test_{scenario}_{iso3}"
    }
    response = session.post(url=RUN_ENDPOINT, json=request)
    return response


def make_query_request(session, results: str):
    request = {
        "results": results,
        "query": QUERY
    }
    response = session.post(url=QUERY_ENDPOINT, json=request)
    return response


def calculate_hyl(results: str):
    df = pd.read_csv(StringIO(results))
    return df["AVG(value)"].sum()


def main():
    results = []
    countries = get_countries_by_tags("appendix_3")["1"]
    with open(MODEL_FILEPATH, "r") as f:
        botech = json.load(f)

    with requests.Session() as session:
        for country in countries:
            change_country(botech, country.alpha3)
            change_time_horizon(botech, 2020, 2120)
            country_results = {
                "country": country.alpha3,
                "timestamp": datetime.now().strftime("%Y%m%dT%H%M%S"),
                "scenarios": {}
            }
            for scenario in SCENARIOS:
                print(f"Working on {country.alpha3} - {scenario}")
                country_results["scenarios"][scenario] = {}
                convert_scenario(botech, scenario)
                run_response = run_request(session, botech, scenario, country.alpha3)
                country_results["scenarios"][scenario]["STATUS_CODE"] = run_response.status_code
                if run_response.status_code == 200:
                    query_response = make_query_request(session, run_response.text)
                    country_results["scenarios"][scenario]["STATUS_CODE"] = query_response.status_code
                    if query_response.status_code == 200:
                        country_results["scenarios"][scenario]["HYL"] = calculate_hyl(query_response.text)
            results.append(country_results)
            with open(RESULTS_FILEPATH, "w") as file:
                json.dump(results, file, indent=4)


if __name__ == "__main__":
    main()
