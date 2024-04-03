"""
avenir_projection_to_timeseries.py

Convert the copy-pasted output from a projection in Avenir to a timeseries in a CSV file.
The output has been modified, because we only need a few of these, and 
its quicker to modify them in visidata.
"""
import csv
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]

def clean_value(value):
    """Remove commas from numbers and convert to integer."""
    return int(value.replace(',', ''))

with open(input_file, mode='r', newline='', encoding='utf-8') as infile, \
     open(output_file, mode='w', newline='', encoding='utf-8') as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    writer.writerow(['timestamp', 'author', 'element_label', 'value'])
    headers = next(reader)
    for row in reader:
        element_label = row[0]

        for year, value in zip(headers[1:], row[1:]):
            timestamp = f'{year}-01-01'
            cleaned_value = clean_value(value)
            writer.writerow([timestamp, 'avenir', element_label, cleaned_value])
