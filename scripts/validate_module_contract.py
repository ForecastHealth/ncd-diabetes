#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = Path("/Users/rory/Documents/botech-modular-structure/contracts")
STALE_PATHS = (
    "build",
    "countries",
    "scenarios",
    "scenario-templates",
    "modular-composition",
    "validation_suite",
    "resources",
    "assurance",
    "results",
)
STALE_ROOT_FILES = {
    "Appendix 3 Costs Reverse Engineering - TABLE.csv",
    "DISCLAIMER.md",
    "DOCUMENTATION.md",
    "clear_db.sh",
    "project.csv",
    "run_investment_case.sh",
    "upload_results.sh",
}
STALE_DATA_FILES = {"data/all_countries.json", "data/diabetes.csv"}
STALE_SCRIPT_NAMES = {
    "apply_scenario.py",
    "create_country_scenarios.py",
    "create_economic_analyses.py",
    "run_economic_analyses.py",
    "upload_project.py",
    "validate_scenario.py",
    "fetch_analytics.py",
    "process_analytics.py",
    "compare_latest_results.py",
    "transform_results_to_xlsx.py",
    "get_latest_results.py",
    "get_appendix_3_comparison.py",
    "diagnose_scenario_warnings.py",
    "verify_components.py",
    "check_results_status.py",
}
STALE_MODEL_NODE_IDS = {"AsthmaEpsd", "Births", "BXOLckIN", "oGP2Nze1", "PjHF9FHh", "DXhAVyOP", "HaYRxeQQ", "mrGezI4c"}
STALE_MODEL_LINK_IDS = {"8g0Xnawu", "pfDEgvPv", "B48YPJzw", "DbLhgNYh"}
BACKGROUND_MORTALITY_LINK_IDS = {"9lHjCUmt", "tJOW1hhc", "STz4wrnX", "BJGaPBZg"}
STALE_POP_REACHED_NODE_IDS = {"5p5rIiTd", "979lBOrq", "q6foBZs3", "Jj9sztq7", "B4SjgqET"}
INTERVENTION_NODE_IDS = {
    "lrst79uc", "lrst0woc", "lrsnjkmt", "lrsnalk2", "lrso22do", "lrsnavq2",
    "ls9tdixs", "ls9tdxgx", "ls9tftfr", "ls9tgf2u", "ls9tli5c", "ls9tllxv",
    "ls9tloqj", "ls9tlsbv", "ls9tlxvf", "ls9tm2qi", "ls9tm6nt", "ls9tmepe",
    "ls9tmgwr", "ls9tmkpe", "ls9tsmp3", "ls9tsrav", "ls9tsvuf", "ls9ttf2m",
    "ls9ttil2", "ls9ttm0m", "ls9tx5l9", "ls9txa8s", "ls9txmx1", "ls9txte5",
    "ls9txz8o", "ls9ty2u5", "ls9u3agu", "ls9u3pq6", "ls9u41gm", "ls9u4cw6",
    "ls9u4iq6", "ls9u9aty", "ResourcePopulationReached_NeuropathyScr",
    "ResourcePopulationReached_RetinopathyScrn", "ResourcePopulationReached_StdGlycControl",
    "ResourcePopulationReached_IntsvGlycControl", "ResourcePopulationReached_NephropathyScr",
}
INTERVENTION_PARAMETER_PREFIXES = (
    "foot_care_",
    "retinopathy_screening_",
    "standard_glycaemic_control_",
    "intensive_glycaemic_control_",
    "nephropathy_screening_",
)
INTERVENTION_TEMPLATE_IDS = {"diabetes_d1", "diabetes_d2", "diabetes_d3", "diabetes_d5"}
PASSIVE_REPORTING_LINK_IDS = {"S2Dkmt7a", "k9NpYYol", "13L1Jqrn", "Vew01LGX", "nNwW4CQS"}
JSON_PATH_RE = re.compile(r"^\$\.(nodes|links)\[\?\(@\.id=='([^']+)'\)\]\.(.+)$")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def strings_in(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(strings_in(item))
        return result
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(strings_in(item))
        return result
    return []


def resolve_json_path(model: dict[str, Any], ref: str) -> bool:
    match = JSON_PATH_RE.match(ref)
    if not match:
        return False
    section, entry_id, tail = match.groups()
    entries = model.get(section, [])
    target = next((entry for entry in entries if entry.get("id") == entry_id), None)
    if target is None:
        return False
    for part in tail.split("."):
        if not isinstance(target, dict) or part not in target:
            return False
        target = target[part]
    return True


def git_tracked_files() -> set[str]:
    result = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, check=True, text=True, capture_output=True)
    return set(result.stdout.splitlines())


def data_requirement_tuple(item: dict[str, Any]) -> tuple[str, str | None, str | None, str | None]:
    generate_array = item.get("generate_array") or {}
    method = generate_array.get("method")
    parameters = generate_array.get("parameters") or {}
    fetcher = generate_array.get("data_fetcher_label")
    if method == "epidemiology":
        return ("epidemiology", parameters.get("disease"), parameters.get("measure"), None)
    if method == "get_observation":
        return (f"{fetcher}.get_observation" if fetcher else "get_observation", None, None, parameters.get("observation"))
    return (method or "", None, None, None)


def validate() -> list[str]:
    errors: list[str] = []
    tracked = git_tracked_files()
    for stale_path in STALE_PATHS:
        stale_tracked = [path for path in tracked if path == stale_path or path.startswith(stale_path + "/")]
        if stale_tracked:
            fail(errors, f"Tracked stale path remains under {stale_path}/")
    for stale_file in STALE_ROOT_FILES | STALE_DATA_FILES:
        if stale_file in tracked:
            fail(errors, f"Tracked stale file remains: {stale_file}")
    for script_name in STALE_SCRIPT_NAMES:
        if (REPO_ROOT / "scripts" / script_name).exists():
            fail(errors, f"scripts/{script_name} still exists; this is not part of the current command surface")
    if (REPO_ROOT / "templates").exists():
        fail(errors, "top-level templates/ still exists; templates should live in parameters/templates")

    model_path = REPO_ROOT / "model.json"
    if not model_path.exists():
        fail(errors, "Missing model.json")
        return errors
    model = load(model_path)
    node_ids = [node.get("id") for node in model.get("nodes", [])]
    link_ids = [link.get("id") for link in model.get("links", [])]
    if len(node_ids) != len(set(node_ids)):
        fail(errors, "model.json has duplicate node ids")
    if len(link_ids) != len(set(link_ids)):
        fail(errors, "model.json has duplicate link ids")
    node_set = set(node_ids)
    link_set = set(link_ids)
    node_by_id = {node.get("id"): node for node in model.get("nodes", [])}
    link_by_id = {link.get("id"): link for link in model.get("links", [])}
    stale_nodes = (STALE_MODEL_NODE_IDS | STALE_POP_REACHED_NODE_IDS | INTERVENTION_NODE_IDS) & node_set
    if stale_nodes:
        fail(errors, f"model.json still contains stale risk-factor/economic/asthma/intervention nodes: {sorted(stale_nodes)}")
    stale_links = STALE_MODEL_LINK_IDS & link_set
    if stale_links:
        fail(errors, f"model.json still contains stale risk-factor/economic links: {sorted(stale_links)}")
    for link in model.get("links", []):
        if link.get("source") not in node_set:
            fail(errors, f"Link {link.get('id')} points to missing source {link.get('source')}")
        if link.get("target") not in node_set:
            fail(errors, f"Link {link.get('id')} points to missing target {link.get('target')}")
    subroutine_edge_refs = set()
    subroutine_node_refs = set()
    for subroutine in model.get("subroutines", []):
        subroutine_edge_refs.update(subroutine.get("included_edges", []))
        subroutine_node_refs.update(subroutine.get("included_source_nodes", []))
    for edge_id in sorted(subroutine_edge_refs - link_set):
        fail(errors, f"Subroutine references missing link {edge_id}")
    for node_id in sorted(subroutine_node_refs - node_set):
        fail(errors, f"Subroutine references missing node {node_id}")
    required_extension_slots = {
        "Calculate Coverage",
        "Calculate Incidence Effects",
        "Remove Incidence Effects from 1.0",
        "Push disease populations to absolute resource population reached",
        "Modify absolute resource population reached by PIN and coverage",
    }
    existing_extension_slots = {
        item.get("narration")
        for item in model.get("subroutines", [])
        if item.get("compiler_extension_slot") == "diabetes_intervention_components"
    }
    missing_extension_slots = required_extension_slots - existing_extension_slots
    if missing_extension_slots:
        fail(errors, f"Missing diabetes intervention compiler extension slots: {sorted(missing_extension_slots)}")
    surrogate_fanout_edges = set()
    for edge_id in subroutine_edge_refs & link_set:
        edge = link_by_id[edge_id]
        target = node_by_id.get(edge.get("target"), {})
        if not edge.get("set_by_surrogate") or target.get("node_type") != "SURROGATE":
            continue
        for out_edge in model.get("links", []):
            if out_edge.get("source") != edge.get("target"):
                continue
            if out_edge.get("value_to_target_operator") != "add":
                continue
            if out_edge.get("remove_value_from_source"):
                continue
            if not out_edge.get("requires_source_balance"):
                continue
            surrogate_fanout_edges.add(out_edge.get("id"))
    unaccounted_links = link_set - subroutine_edge_refs - surrogate_fanout_edges - PASSIVE_REPORTING_LINK_IDS
    if unaccounted_links:
        fail(errors, f"Executable-looking links are not reachable by subroutine or surrogate fanout: {sorted(unaccounted_links)}")
    for text_value in strings_in(model):
        if "Asthma" in text_value or "asthma" in text_value:
            fail(errors, f"Diabetes model still contains stale asthma text: {text_value}")
            break
    for link_id in BACKGROUND_MORTALITY_LINK_IDS:
        link = next((item for item in model.get("links", []) if item.get("id") == link_id), None)
        if not link:
            fail(errors, f"Missing diabetes background mortality link {link_id}")
        elif link.get("generate_array"):
            fail(errors, f"Diabetes background mortality link {link_id} still fetches demographic mortality directly instead of relying on compiler lowering")
        elif link.get("compiler_binding", {}).get("kind") != "declared_input":
            fail(errors, f"Diabetes background mortality link {link_id} is not marked as a declared compiler input")
        elif link.get("compiler_binding", {}).get("channel_id") != "background_mortality_rate":
            fail(errors, f"Diabetes background mortality link {link_id} does not name background_mortality_rate")
    incidence_link = next((item for item in model.get("links", []) if item.get("id") == "eYyocGwO"), None)
    if not incidence_link or incidence_link.get("compiler_binding", {}).get("channel_id") != "incidence_modifier":
        fail(errors, "Diabetes incidence-rate link does not expose the optional incidence_modifier compiler binding")

    module_files = sorted((REPO_ROOT / "interface").glob("*.module.contract.v1.json"))
    if len(module_files) != 1:
        fail(errors, f"Expected exactly one module contract, found {len(module_files)}")
        return errors
    module = load(module_files[0])
    module_id = module.get("module_id")
    repo_id = module.get("owner", {}).get("repo_id")
    if module.get("schema") != "botech.module-contract.v1":
        fail(errors, f"{module_files[0]} has wrong module contract schema")
    if module_id != "diabetes_epidemiology_core":
        fail(errors, "Module contract module_id is not diabetes_epidemiology_core")
    if module.get("runtime_role") != "compiled_together":
        fail(errors, "Diabetes should be marked compiled_together because it declares demographic substrate inputs")
    declared_inputs = {item.get("channel_id") for item in module.get("declared_inputs", [])}
    for required_input in {"population_at_risk_opening", "background_mortality_rate", "incidence_modifier"}:
        if required_input not in declared_inputs:
            fail(errors, f"Module contract is missing declared input {required_input}")
    published_bindings = []
    for output in module.get("published_outputs", []):
        binding = output.get("binding", {})
        if "node_id" in binding:
            published_bindings.append(binding["node_id"])
        if "node_ids" in binding:
            published_bindings.extend(binding["node_ids"])
    for node_id in published_bindings:
        if node_id not in node_set:
            fail(errors, f"Published output binds to missing node {node_id}")

    declared_data_requirements = set()
    for requirement in module.get("runtime_data_requirements", []):
        data_type = requirement.get("data_type")
        parameters = requirement.get("parameters") or {}
        declared_data_requirements.add((data_type, parameters.get("disease"), parameters.get("measure"), parameters.get("observation")))
    model_data_requirements = set()
    for section in ("nodes", "links"):
        for item in model.get(section, []):
            generate_array = item.get("generate_array") or {}
            method = generate_array.get("method")
            if not method or method in {"single_value", "linear_with_arbitrary_length", "subset"}:
                continue
            if not generate_array.get("data_fetcher_label") and method not in {"epidemiology", "get_observation", "healthy_disability", "yll_weights", "mortality"}:
                continue
            model_data_requirements.add(data_requirement_tuple(item))
    for requirement in sorted(model_data_requirements):
        if requirement not in declared_data_requirements:
            fail(errors, f"Model data dependency is not declared in runtime_data_requirements: {requirement}")

    tests = module.get("validation", {}).get("internal_validity_tests", [])
    if "python scripts/validate_module_contract.py" not in tests:
        fail(errors, "Module contract validation command does not point at scripts/validate_module_contract.py")
    recipe_ref = module.get("state_initialization", {}).get("recipe_ref")
    if not recipe_ref or not (REPO_ROOT / recipe_ref).exists():
        fail(errors, "Module contract state initialization recipe is missing")
    else:
        recipe = load(REPO_ROOT / recipe_ref)
        if recipe.get("module_id") != module_id:
            fail(errors, "State initialization recipe module_id does not match module contract")
        recipe_inputs = {item.get("input_id"): item for item in recipe.get("inputs", [])}
        if recipe_inputs.get("population_at_risk_opening", {}).get("owner_module_id") != "demographic_substrate":
            fail(errors, "State initialization recipe does not consume demographic population_at_risk_opening")
        if recipe_inputs.get("diabetes_prevalence", {}).get("owner_module_id") != module_id:
            fail(errors, "State initialization recipe does not declare diabetes-owned prevalence input")
        recipe_targets = {item.get("target") for item in recipe.get("outputs", [])}
        for target in recipe_targets:
            if target not in node_set:
                fail(errors, f"State initialization recipe targets missing model node {target}")
        epidemiology_requirements = {
            ((item.get("parameters", {}) or {}).get("disease"), (item.get("parameters", {}) or {}).get("measure"))
            for item in module.get("runtime_data_requirements", [])
            if item.get("data_type") == "epidemiology"
        }
        if ("Diabetes", "prevalence") not in epidemiology_requirements:
            fail(errors, "Module runtime data requirements do not declare Diabetes prevalence for state initialization")

    registry_path = REPO_ROOT / "parameters" / "registry.v1.json"
    if not registry_path.exists():
        fail(errors, "Missing parameters/registry.v1.json")
        return errors
    registry = load(registry_path)
    if registry.get("schema") != "botech.parameter-registry.v1":
        fail(errors, "parameters/registry.v1.json has wrong schema")
    if registry.get("module_id") != module_id:
        fail(errors, "Parameter registry module_id does not match module contract")
    if registry.get("owner", {}).get("repo_id") != repo_id:
        fail(errors, "Parameter registry owner repo_id does not match module contract")
    registry_ids = [item.get("parameter_id") for item in registry.get("parameters", [])]
    if len(registry_ids) != len(set(registry_ids)):
        fail(errors, "Parameter registry has duplicate parameter_id values")
    registry_set = set(registry_ids)
    forbidden_tokens = ("tobacco", "physical_inactivity", "sodium", "diet", "alcohol", "bmi", "obesity")
    if any(any(token in str(parameter_id).lower() for token in forbidden_tokens) for parameter_id in registry_set):
        fail(errors, "Diabetes registry contains cross-module risk-factor parameter ids")
    if any(parameter_id in {"country", "start_year", "end_year"} for parameter_id in registry_set):
        fail(errors, "Runtime context appears as scenario-editable registry parameters")
    stale_intervention_parameters = [
        parameter_id for parameter_id in registry_set
        if any(str(parameter_id).startswith(prefix) for prefix in INTERVENTION_PARAMETER_PREFIXES)
    ]
    if stale_intervention_parameters:
        fail(errors, f"Diabetes registry still owns intervention parameters: {sorted(stale_intervention_parameters)}")
    stale_intervention_parameters = [
        parameter_id for parameter_id in registry_set
        if any(str(parameter_id).startswith(prefix) for prefix in INTERVENTION_PARAMETER_PREFIXES)
    ]
    if stale_intervention_parameters:
        fail(errors, f"Diabetes registry still owns intervention parameters: {sorted(stale_intervention_parameters)}")
    stale_intervention_parameters = [
        parameter_id for parameter_id in registry_set
        if any(str(parameter_id).startswith(prefix) for prefix in INTERVENTION_PARAMETER_PREFIXES)
    ]
    if stale_intervention_parameters:
        fail(errors, f"Diabetes registry still owns intervention parameters: {sorted(stale_intervention_parameters)}")
    stale_intervention_parameters = [
        parameter_id for parameter_id in registry_set
        if any(str(parameter_id).startswith(prefix) for prefix in INTERVENTION_PARAMETER_PREFIXES)
    ]
    if stale_intervention_parameters:
        fail(errors, f"Diabetes registry still owns intervention parameters: {sorted(stale_intervention_parameters)}")
    stale_intervention_parameters = [
        parameter_id for parameter_id in registry_set
        if any(str(parameter_id).startswith(prefix) for prefix in INTERVENTION_PARAMETER_PREFIXES)
    ]
    if stale_intervention_parameters:
        fail(errors, f"Diabetes registry still owns intervention parameters: {sorted(stale_intervention_parameters)}")
    stale_intervention_parameters = [
        parameter_id for parameter_id in registry_set
        if any(str(parameter_id).startswith(prefix) for prefix in INTERVENTION_PARAMETER_PREFIXES)
    ]
    if stale_intervention_parameters:
        fail(errors, f"Diabetes registry still owns intervention parameters: {sorted(stale_intervention_parameters)}")
    for text in strings_in(registry):
        if any(token in text for token in ("build/", "scenarios/", "scenario-templates", "modular-composition")):
            fail(errors, f"Parameter registry still references removed source: {text}")
            break
    for item in registry.get("parameters", []):
        for placement in item.get("placement_refs", []):
            if placement.get("kind") != "json_path":
                fail(errors, f"Parameter {item.get('parameter_id')} has unsupported placement kind {placement.get('kind')}")
            elif not resolve_json_path(model, placement.get("ref", "")):
                fail(errors, f"Parameter {item.get('parameter_id')} placement does not resolve: {placement.get('ref')}")

    template_root = REPO_ROOT / "parameters" / "templates"
    template_files = sorted(template_root.glob("*.template.v1.json"))
    required_templates = {"diabetes_baseline"}
    template_ids = set()
    if not template_files:
        fail(errors, "Missing parameters/templates/*.template.v1.json")
    for template_file in template_files:
        template = load(template_file)
        template_id = template.get("template_id")
        template_ids.add(template_id)
        if template.get("schema") != "botech.scenario-template.v1":
            fail(errors, f"{template_file} has wrong template schema")
        if template.get("module_id") != module_id:
            fail(errors, f"{template_file} module_id does not match registry")
        if template.get("owner", {}).get("repo_id") != repo_id:
            fail(errors, f"{template_file} owner repo_id does not match registry")
        if template.get("parameter_registry_ref") != "parameters/registry.v1.json":
            fail(errors, f"{template_file} does not point to parameters/registry.v1.json")
        if template_id in INTERVENTION_TEMPLATE_IDS:
            fail(errors, f"{template_file} is an intervention template that should live in an intervention contract")
        if template_id in INTERVENTION_TEMPLATE_IDS:
            fail(errors, f"{template_file} is an intervention template that should live in an intervention contract")
        if template_id in INTERVENTION_TEMPLATE_IDS:
            fail(errors, f"{template_file} is an intervention template that should live in an intervention contract")
        if template_id in INTERVENTION_TEMPLATE_IDS:
            fail(errors, f"{template_file} is an intervention template that should live in an intervention contract")
        if template_id in INTERVENTION_TEMPLATE_IDS:
            fail(errors, f"{template_file} is an intervention template that should live in an intervention contract")
        if template_id in INTERVENTION_TEMPLATE_IDS:
            fail(errors, f"{template_file} is an intervention template that should live in an intervention contract")
        for text in strings_in(template):
            if any(token in text for token in ("build/", "scenarios/", "scenario-templates", "tobacco", "physical_inactivity", "sodium", "diet", "alcohol")):
                fail(errors, f"{template_file} contains stale or cross-module reference: {text}")
                break
        for value in template.get("parameter_values", []):
            parameter_id = value.get("parameter_id")
            if parameter_id not in registry_set:
                fail(errors, f"{template_file} references unknown parameter_id {parameter_id}")
    missing = required_templates - template_ids
    if missing:
        fail(errors, f"Missing required diabetes templates: {sorted(missing)}")

    link_files = sorted((REPO_ROOT / "contracts" / "links").glob("*.link.contract.v1.json"))
    for link_file in link_files:
        link = load(link_file)
        if link.get("schema") != "botech.link-contract.v1":
            fail(errors, f"{link_file} has wrong link schema")
        source_repo = link.get("source", {}).get("repo_id")
        if source_repo and source_repo != repo_id:
            fail(errors, f"{link_file} is not source-owned by this repository")

    command_script = REPO_ROOT / "scripts" / "orchestrator_scenarios.py"
    if not command_script.exists():
        fail(errors, "Missing scripts/orchestrator_scenarios.py command surface")
    else:
        for command, expected_schema in (("catalog", "botech.parameter-registry.v1"), ("templates", "botech.module-template-registry.v1")):
            result = subprocess.run([sys.executable, str(command_script), command], cwd=REPO_ROOT, text=True, capture_output=True)
            if result.returncode != 0:
                fail(errors, f"Command surface `{command}` failed: {result.stderr.strip() or result.stdout.strip()}")
                continue
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                fail(errors, f"Command surface `{command}` did not emit valid JSON: {exc}")
                continue
            if payload.get("schema") != expected_schema:
                fail(errors, f"Command surface `{command}` emitted schema {payload.get('schema')} not {expected_schema}")
        with tempfile.TemporaryDirectory(prefix="diabetes-module-validate-") as output_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(command_script),
                    "materialize",
                    "--template-id",
                    "diabetes_baseline",
                    "--country",
                    "ETH",
                    "--start-year",
                    "2025",
                    "--end-year",
                    "2050",
                    "--output-dir",
                    output_dir,
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            if result.returncode != 0:
                fail(errors, f"Command surface `materialize` failed: {result.stderr.strip() or result.stdout.strip()}")
            else:
                try:
                    payload = json.loads(result.stdout)
                    materialized = load(Path(payload["run_input"]))
                except (json.JSONDecodeError, KeyError, FileNotFoundError) as exc:
                    fail(errors, f"Command surface `materialize` did not emit a readable run input: {exc}")
                else:
                    runtime_status = materialized.get("runtime_status", {})
                    if runtime_status.get("standalone_runtime_proof") is not False:
                        fail(errors, "Materialized diabetes artifact must explicitly report that standalone runtime proof is false")
                    if "demographic_substrate" not in runtime_status.get("requires_compiler_lowering", []):
                        fail(errors, "Materialized diabetes artifact does not declare demographic_substrate compiler lowering")

    if not CONTRACT_ROOT.exists():
        fail(errors, "Cannot find botech-modular-structure contract root")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("Module contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
