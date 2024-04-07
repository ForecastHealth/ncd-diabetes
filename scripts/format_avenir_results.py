import pandas as pd

DISEASE = "diabetes"
INPUT_FILEPATH = f"./data/{DISEASE}_avenir_results.csv"
OUTPUT_FILEPATH = f"./data/{DISEASE}_avenir_results_formatted.json"
SCENARIO_NAME_MAP = {
    "DNull": "null",
    "D1": "d1",
    "D2": "d2",
    "D3": "d3",
    "D5": "d5",
}


def main():
    df = pd.read_csv(INPUT_FILEPATH, skiprows=[0])
    required_columns = [2, 27, 28, 29, 30, 31]

    records = []
    scenarios = ['DNull', 'D1', 'D2', 'D3', 'D5']

    for _, row in df.iterrows():
        if not isinstance(row[2], float):
            for index, scenario in enumerate(scenarios, start=1):
                hyl = row[required_columns[index]]
                if isinstance(hyl, str):
                    hyl = hyl.replace(',', '')
                if pd.isna(hyl):
                    hyl = 0
                records.append({
                    'ISO3': row[2],
                    'scenario': SCENARIO_NAME_MAP[scenario],
                    'HYL': int(hyl),
                } 
            )

    clean_data = pd.DataFrame(records)
    clean_data.to_json(OUTPUT_FILEPATH, orient='records', indent=4)


if __name__ == "__main__":
    main()
