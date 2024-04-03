"""
replace_link_labels.py

Iterate through links.
Add "label" property as source["label"] and target["label"]
"""
import sys
import json


def main():
    botech_filepath = sys.argv[1]
    with open(botech_filepath, "r") as f:
        botech = json.load(f)

    for link in botech["links"]:
        source_id = link["source"]
        target_id = link["target"]

        for node in botech["nodes"]:
            if node["id"] == source_id:
                source_label = node["label"]
            if node["id"] == target_id:
                target_label = node["label"]

        link["label"] = f"{source_label} -> {target_label}"

    with open(botech_filepath, "w") as f:
        json.dump(botech, f, indent=4)

if __name__ == "__main__":
    main()
