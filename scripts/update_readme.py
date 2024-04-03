"""
update_readme.py

Take the results in JSON format,
render them as a markdown table,
append that table to the bottom of the README.md
"""
import json
DISEASE = "copd"

def load_avenir_results(filename):
    with open(filename, 'r') as file:
        avenir_data = json.load(file)
    # Create a dictionary to easily access Avenir results based on country and scenario.
    avenir_results = {(d['ISO3'], d['scenario']): d['HYL'] for d in avenir_data}
    return avenir_results

def format_hyl(value):
    if isinstance(value, str):
        value = value.replace(',', '')
    return "{:,}".format(int(value))

def calculate_ratios(data, baseline_scenario='baseline'):
    # Calculate baseline HYLs for comparison.
    baseline_hyls = {}
    for result in data:
        country = result["country"]
        if baseline_scenario in result["scenarios"]:
            baseline_hyls[country] = result["scenarios"][baseline_scenario]['HYL']
    return baseline_hyls

def main():
    avenir_results = load_avenir_results(f'data/{DISEASE}_avenir_results_formatted.json')
    with open('results.json', 'r') as file:
        data = json.load(file)

    baseline_hyls = calculate_ratios(data)

    markdown_table = "# Test Results\n\n| Country | Scenario  | STATUS_CODE | HYL          | Avenir HYL    | Ratio         | vs Baseline   |\n|---------|-----------|-------------|--------------|---------------|---------------|---------------|\n"
    for result in data:
        country = result["country"]
        for scenario, details in result["scenarios"].items():
            hyl_formatted = format_hyl(details['HYL'])
            key = (country, scenario)
            avenir_hyl_formatted = format_hyl(avenir_results[key]) if key in avenir_results else "N/A"
            ratio = "{:.6f}".format(details['HYL'] / avenir_results[key]) if key in avenir_results else "N/A"
            vs_baseline = "{:.6f}".format(details['HYL'] / baseline_hyls[country]) if country in baseline_hyls and scenario != 'CRNullCOPD' else "1.00"
            markdown_table += f"| {country} | {scenario} | {details['STATUS_CODE']} | {hyl_formatted} | {avenir_hyl_formatted} | {ratio} | {vs_baseline} |\n"

    with open('README.md', 'r') as file:
        readme_content = file.read()

    header_index = readme_content.find("# Test Results")
    if header_index != -1:
        readme_content = readme_content[:header_index]
    readme_content += markdown_table

    with open('README.md', 'w') as file:
        file.write(readme_content)

if __name__ == "__main__":
    main()
