#!/usr/bin/env python3
"""
Terminal User Interface (TUI) for Model Validation
"""
import json
import os
import sys
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any

from .runner import EnhancedValidationRunner

# Configure logging for the TUI to show INFO level messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def load_env_file(file_path: str = ".env.local") -> Dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env_vars

def get_default_environment() -> str:
    """Get the default environment from .env.local or fallback to 'standard'."""
    env_vars = load_env_file()
    return env_vars.get('ENVIRONMENT', 'standard')

def load_json_file(file_path: str) -> Any:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_model_files() -> List[str]:
    return sorted([p for p in glob.glob("*.json") + glob.glob("models/*.json") if "scenario" not in p and "list" not in p]) or ["model.json"]

def get_scenario_files() -> List[str]:
    return sorted(glob.glob("scenarios/*.json")) or ["scenarios/default_scenario.json"]

def get_country_files() -> List[str]:
    return sorted(glob.glob("countries/*.json")) or []

def get_environments() -> List[str]:
    return ["default", "standard", "appendix_3"]

def print_header():
    print("=" * 60 + "\n" + "🔍 Model Validation TUI".center(60) + "\n" + "=" * 60 + "\n")

def print_menu(title: str, options: List[str], current_selection: str = None) -> int:
    print(f"\n📋 {title}\n" + "-" * 40)
    for i, option in enumerate(options, 1):
        marker = "→" if option == current_selection else " "
        print(f"{marker} {i}. {option}")
    print(f"  {len(options) + 1}. Back/Skip\n")
    
    while True:
        try:
            choice = input("Select option (number): ").strip()
            if not choice: continue
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return choice_num - 1
            elif choice_num == len(options) + 1:
                return -1
            else:
                print(f"Please enter a number between 1 and {len(options) + 1}")
        except (ValueError, KeyboardInterrupt, EOFError):
            print("\n\n⏹️  Cancelled by user")
            sys.exit(0)

def run_validation(selections: Dict[str, str]) -> None:
    """Run the validation using the integrated runner."""
    print("\n" + "=" * 60 + "\n🚀 Running Validation\n" + "=" * 60)
    try:
        runner = EnhancedValidationRunner()
        
        # The TUI runs a specific set of scenarios/countries, so we force it.
        # The runner is designed to work with groups, so we adapt.
        scenario_name = Path(selections["Scenario"]).stem
        country_iso_codes = None
        if selections["Countries"] != "all":
            country_data = load_json_file(selections["Countries"])
            if country_data:
                country_iso_codes = [c['iso3'] for c in country_data.get('countries', [])]
        
        result = runner.run(
            model_path=selections["Model"],
            countries_file="countries/list_of_countries.json",
            scenario_templates_dir=str(Path(selections["Scenario"]).parent),
            environment=selections["Environment"],
            max_instances=100,
            force_rerun=True, # TUI runs are explicit actions, so always run.
            specific_scenarios=[scenario_name],
            specific_countries=country_iso_codes
        )

        print("\n" + "=" * 60)
        if result.get("success"):
            print(f"✅ Validation completed successfully! Run ID: {result.get('run_id')}")
        else:
            print(f"❌ Validation failed: {result.get('error', 'Unknown error')}")
        print("=" * 60)

    except (KeyboardInterrupt, EOFError):
        print("\n\n⏹️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running validation: {e}", exc_info=True)

def main():
    print_header()
    selections = {
        "Model": "model.json",
        "Scenario": get_scenario_files()[0] if get_scenario_files() else "",
        "Environment": get_default_environment(),
        "Countries": "all"
    }
    
    while True:
        print("\n🎯 Current Selections:")
        for key, value in selections.items(): print(f"   {key:15}: {value}")
        
        print("\n📋 Main Menu\n" + "-" * 40)
        print("  1. Select Model\n  2. Select Scenario\n  3. Select Environment\n  4. Select Countries\n  5. Run Validation\n  6. Exit\n")
        
        try:
            choice = input("Select option (number): ").strip()
            if choice == "1":
                files = get_model_files()
                idx = print_menu("Select Model File", files, selections["Model"])
                if idx >= 0: selections["Model"] = files[idx]
            elif choice == "2":
                files = get_scenario_files()
                idx = print_menu("Select Scenario File", files, selections["Scenario"])
                if idx >= 0: selections["Scenario"] = files[idx]
            elif choice == "3":
                envs = get_environments()
                idx = print_menu("Select Environment", envs, selections["Environment"])
                if idx >= 0: selections["Environment"] = envs[idx]
            elif choice == "4":
                files = ["all"] + get_country_files()
                idx = print_menu("Select Countries File ('all' for everything)", files, selections["Countries"])
                if idx >= 0: selections["Countries"] = files[idx]
            elif choice == "5":
                run_validation(selections)
            elif choice == "6":
                print("\n👋 Goodbye!")
                sys.exit(0)
            else:
                print("Please enter a number between 1 and 6")
        except (KeyboardInterrupt, EOFError):
            print("\n\n⏹️  Cancelled by user")
            sys.exit(0)

if __name__ == "__main__":
    main()