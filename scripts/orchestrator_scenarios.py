#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / "model.json"
PARAMETER_REGISTRY_PATH = REPO_ROOT / "parameters" / "registry.v1.json"
TEMPLATES_ROOT = REPO_ROOT / "parameters" / "templates"
MODULE_CONTRACT_PATH = REPO_ROOT / "interface" / "diabetes-epidemiology-core.module.contract.v1.json"
DEFAULT_TEMPLATE_ID = "diabetes_baseline"
TEMPLATE_ALIASES = {
    "baseline": "diabetes_baseline",
    "default": "diabetes_baseline",
    "d1": "diabetes_d1",
    "d2": "diabetes_d2",
    "d3": "diabetes_d3",
    "d5": "diabetes_d5",
}
JSON_PATH_RE = re.compile(r"^\$\.(nodes|links)\[\?\(@\.id=='([^']+)'\)\]\.(.+)$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_registry() -> dict[str, Any]:
    if not PARAMETER_REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Missing parameter registry: {PARAMETER_REGISTRY_PATH}")
    return load_json(PARAMETER_REGISTRY_PATH)


def iter_template_files() -> list[Path]:
    if not TEMPLATES_ROOT.exists():
        return []
    return sorted(TEMPLATES_ROOT.glob("*.template.v1.json"))


def load_templates() -> dict[str, dict[str, Any]]:
    templates: dict[str, dict[str, Any]] = {}
    for path in iter_template_files():
        template = load_json(path)
        template_id = template.get("template_id")
        if not template_id:
            raise ValueError(f"Template is missing template_id: {path}")
        if template_id in templates:
            raise ValueError(f"Duplicate template_id: {template_id}")
        template["_template_ref"] = str(path.relative_to(REPO_ROOT))
        templates[template_id] = template
    return templates


def resolve_template_id(template_id: str) -> str:
    resolved = TEMPLATE_ALIASES.get(template_id, template_id)
    templates = load_templates()
    if resolved not in templates:
        available = ", ".join(sorted(templates)) or "none"
        raise KeyError(f"Unknown template_id `{template_id}`. Available templates: {available}")
    return resolved


def template_kind(template: dict[str, Any]) -> str:
    role = template.get("template_role")
    if role == "baseline":
        return "baseline"
    if role == "comparison":
        return "preset"
    return role or "custom"


def parameter_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["parameter_id"]: item for item in registry.get("parameters", [])}


def template_value_index(template: dict[str, Any]) -> dict[str, Any]:
    return {item["parameter_id"]: item.get("value") for item in template.get("parameter_values", [])}


def build_catalog_payload() -> dict[str, Any]:
    return load_registry()


def build_templates_payload() -> dict[str, Any]:
    registry = load_registry()
    templates = load_templates()
    baseline_values = template_value_index(templates[DEFAULT_TEMPLATE_ID]) if DEFAULT_TEMPLATE_ID in templates else {}
    payload_templates = []
    for template_id in sorted(templates):
        template = templates[template_id]
        values = template_value_index(template)
        changed = [name for name, value in values.items() if baseline_values.get(name) != value]
        payload_templates.append(
            {
                "template_id": template_id,
                "kind": template_kind(template),
                "template_role": template.get("template_role"),
                "label": template.get("label", template_id),
                "description": template.get("description", ""),
                "parameter_registry_ref": template.get("parameter_registry_ref", "parameters/registry.v1.json"),
                "parameter_count": len(template.get("parameter_values", [])),
                "changed_from_baseline_parameter_names": sorted(changed),
                "template_ref": template.get("_template_ref"),
            }
        )
    return {
        "schema": "botech.module-template-registry.v1",
        "schema_version": "v1",
        "model_id": "ncd-diabetes",
        "module_id": registry.get("module_id"),
        "owner": registry.get("owner"),
        "parameter_registry_ref": "parameters/registry.v1.json",
        "template_count": len(payload_templates),
        "templates": payload_templates,
    }


def parse_override(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise ValueError(f"Override must use NAME=VALUE form: {raw}")
    name, raw_value = raw.split("=", 1)
    name = name.strip()
    raw_value = raw_value.strip()
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        value = raw_value
    return name, value


def resolve_parameter_name(raw_name: str, registry_by_id: dict[str, dict[str, Any]]) -> str:
    if raw_name in registry_by_id:
        return raw_name
    matches = [parameter_id for parameter_id, item in registry_by_id.items() if item.get("label") == raw_name]
    if len(matches) == 1:
        return matches[0]
    raise KeyError(f"Unknown parameter `{raw_name}`")


def apply_value_at_json_path(model: dict[str, Any], ref: str, value: Any) -> None:
    match = JSON_PATH_RE.match(ref)
    if not match:
        raise ValueError(f"Unsupported placement ref: {ref}")
    section, entry_id, tail = match.groups()
    entries = model.get(section, [])
    target_entry = next((entry for entry in entries if entry.get("id") == entry_id), None)
    if target_entry is None:
        raise KeyError(f"Placement ref points to missing {section[:-1]} `{entry_id}`")
    target: Any = target_entry
    for part in tail.split(".")[:-1]:
        if not isinstance(target, dict) or part not in target:
            raise KeyError(f"Placement ref cannot resolve `{part}` in {ref}")
        target = target[part]
    leaf = tail.split(".")[-1]
    if not isinstance(target, dict) or leaf not in target:
        raise KeyError(f"Placement ref cannot resolve `{leaf}` in {ref}")
    target[leaf] = copy.deepcopy(value)


def apply_parameter_values(model: dict[str, Any], registry: dict[str, Any], values: dict[str, Any]) -> list[dict[str, Any]]:
    registry_by_id = parameter_index(registry)
    applied: list[dict[str, Any]] = []
    for parameter_id, value in values.items():
        if parameter_id not in registry_by_id:
            raise KeyError(f"Template references unknown parameter `{parameter_id}`")
        placements = registry_by_id[parameter_id].get("placement_refs", [])
        if not placements:
            raise ValueError(f"Parameter `{parameter_id}` has no placement_refs")
        for placement in placements:
            if placement.get("kind") != "json_path":
                raise ValueError(f"Parameter `{parameter_id}` has unsupported placement kind `{placement.get('kind')}`")
            apply_value_at_json_path(model, placement.get("ref", ""), value)
        applied.append({"parameter_id": parameter_id, "label": registry_by_id[parameter_id].get("label"), "value": value, "placement_count": len(placements)})
    return applied


def apply_runtime_context(model: dict[str, Any], *, country: str, start_year: int, end_year: int) -> None:
    runtime = model.setdefault("runtime", {})
    runtime["startYear"] = start_year
    runtime["endYear"] = end_year
    for section in ("nodes", "links"):
        for item in model.get(section, []):
            params = (item.get("generate_array") or {}).get("parameters")
            if isinstance(params, dict) and "country" in params:
                params["country"] = country


def materialize_template(*, template_id: str, scenario_id: str | None, country: str, start_year: int, end_year: int, output_dir: Path, overrides: list[str]) -> dict[str, Any]:
    registry = load_registry()
    registry_by_id = parameter_index(registry)
    templates = load_templates()
    resolved_template_id = resolve_template_id(template_id)
    template = copy.deepcopy(templates[resolved_template_id])
    template.pop("_template_ref", None)
    values = template_value_index(template)
    applied_overrides: dict[str, Any] = {}
    for raw_override in overrides:
        name, value = parse_override(raw_override)
        parameter_id = resolve_parameter_name(name, registry_by_id)
        values[parameter_id] = value
        applied_overrides[parameter_id] = value
    materialized_model = copy.deepcopy(load_json(MODEL_PATH))
    apply_runtime_context(materialized_model, country=country, start_year=start_year, end_year=end_year)
    applied_parameters = apply_parameter_values(materialized_model, registry, values)
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_path = output_dir / "scenario.json"
    model_path = output_dir / "model.json"
    bundle_path = output_dir / "data_bundle.json"
    run_input_path = output_dir / "materialized.model-input.v1.json"
    module_contract = load_json(MODULE_CONTRACT_PATH) if MODULE_CONTRACT_PATH.exists() else {}
    scenario = {
        "schema": "botech.materialized-scenario.v1",
        "model_id": "ncd-diabetes",
        "module_id": registry.get("module_id"),
        "scenario_id": scenario_id or resolved_template_id,
        "template_id": resolved_template_id,
        "requested_template_id": template_id,
        "parameter_registry_ref": "parameters/registry.v1.json",
        "template_ref": f"parameters/templates/{resolved_template_id}.template.v1.json",
        "parameter_values": [{"parameter_id": parameter_id, "value": value} for parameter_id, value in sorted(values.items())],
        "run_context": {"country": country, "start_year": start_year, "end_year": end_year},
    }
    write_json(scenario_path, scenario)
    write_json(model_path, materialized_model)
    materialized = {
        "metadata": {
            "artifact_version": "v1",
            "artifact_type": "template_applied_module_model",
            "name": f"ncd-diabetes materialized run input: {scenario_id or resolved_template_id}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "model_id": "ncd-diabetes",
        "module_id": registry.get("module_id"),
        "scenario_id": scenario_id or resolved_template_id,
        "template_id": resolved_template_id,
        "requested_template_id": template_id,
        "template_kind": template_kind(template),
        "materializer": {"repo_root": str(REPO_ROOT), "script": str(Path(__file__).resolve()), "source": "parameters/registry.v1.json plus parameters/templates"},
        "materialized_input": {
            "kind": "template_applied_module_model_requires_compiler_lowering",
            "model_ref": str(model_path),
            "scenario_ref": str(scenario_path),
            "data_bundle_ref": str(bundle_path),
            "data_bundle_status": "declared_path_pending_fetch",
        },
        "data_requirements": {"mode": "unified_api_bundle_required_before_runtime", "source_ref": str(MODULE_CONTRACT_PATH), "requirements": module_contract.get("runtime_data_requirements", [])},
        "runtime_status": {
            "standalone_runtime_proof": False,
            "requires_compiler_lowering": ["demographic_substrate"],
            "reason": "Diabetes declares demographic substrate inputs and opening-balance seeding. This materialized model has the diabetes template applied, but it is not a complete proof run until the compiler lowers demographic inputs and diabetes opening balances.",
        },
        "resolved_values": {"country": country, "start_year": start_year, "end_year": end_year, "overrides": applied_overrides, "applied_parameters": applied_parameters},
        "provenance": {"source_model_ref": str(MODEL_PATH), "parameter_registry_ref": str(PARAMETER_REGISTRY_PATH), "template_ref": str(TEMPLATES_ROOT / f"{resolved_template_id}.template.v1.json")},
    }
    write_json(run_input_path, materialized)
    return {
        "status": "ok",
        "template_id": resolved_template_id,
        "requested_template_id": template_id,
        "scenario_id": scenario_id or resolved_template_id,
        "run_input": str(run_input_path),
        "model": str(model_path),
        "scenario": str(scenario_path),
        "data_bundle": str(bundle_path),
        "data_bundle_status": "declared_path_pending_fetch",
        "runtime_status": "requires_demographic_substrate_compiler_lowering",
        "output_dir": str(output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Expose ncd-diabetes parameter registry, templates, and template materialisation helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    catalog_parser = subparsers.add_parser("catalog", help="Emit the parameter registry.")
    catalog_parser.add_argument("--output", help="Optional output JSON path.")
    templates_parser = subparsers.add_parser("templates", help="Emit the template list.")
    templates_parser.add_argument("--output", help="Optional output JSON path.")
    materialize_parser = subparsers.add_parser("materialize", help="Materialize one named template into a template-applied diabetes module model.")
    materialize_parser.add_argument("--template-id", required=True, help="Template id from parameters/templates, for example diabetes_baseline, diabetes_d1, diabetes_d2, diabetes_d3, or diabetes_d5.")
    materialize_parser.add_argument("--scenario-id", default=None, help="Scenario id to record in the materialized artifact.")
    materialize_parser.add_argument("--country", default="AFG")
    materialize_parser.add_argument("--start-year", type=int, default=2025)
    materialize_parser.add_argument("--end-year", type=int, default=2050)
    materialize_parser.add_argument("--output-dir", required=True, help="Directory where scenario/model/materialized input should be written.")
    materialize_parser.add_argument("--set", dest="overrides", action="append", default=[], help="Optional parameter override in parameter_id=JSON_VALUE or label=JSON_VALUE form. Can be repeated.")
    args = parser.parse_args()
    if args.command == "catalog":
        payload = build_catalog_payload()
        if args.output:
            write_json(Path(args.output).resolve(), payload)
        print(json.dumps(payload, indent=2))
        return
    if args.command == "templates":
        payload = build_templates_payload()
        if args.output:
            write_json(Path(args.output).resolve(), payload)
        print(json.dumps(payload, indent=2))
        return
    if args.command == "materialize":
        print(json.dumps(materialize_template(template_id=args.template_id, scenario_id=args.scenario_id, country=args.country, start_year=args.start_year, end_year=args.end_year, output_dir=Path(args.output_dir).resolve(), overrides=args.overrides), indent=2))
        return
    raise ValueError(f"Unhandled command `{args.command}`")


if __name__ == "__main__":
    main()
