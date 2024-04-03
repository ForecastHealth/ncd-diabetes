import pandas as pd

DISEASE = "copd"
INPUT_FILEPATH = f"./data/{DISEASE}_avenir_results.csv"
OUTPUT_FILEPATH = f"./data/{DISEASE}_avenir_results_formatted.json"
SCENARIO_NAME_MAP = {
    "Null": "null",
    "CR2": "cr2",
    "CR4": "cr4"
}


def main():
    df = pd.read_csv(INPUT_FILEPATH, skiprows=[0])
    required_columns = [2, 13, 14, 15]

    records = []
    scenarios = ['Null', 'CR2', 'CR4']

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
