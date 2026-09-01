#!/usr/bin/env python3
"""Generate a traceability-focused PlantUML view from a Clafer instance JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PREFIX_RE = re.compile(r"^c\d+_")


def strip_prefix(name: str) -> str:
    return PREFIX_RE.sub("", name)


def decode_string(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def group_children(children: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for child in children:
        grouped.setdefault(strip_prefix(child["name"]), []).append(child)
    return grouped


def classify(node: dict) -> str | None:
    sup = node.get("super")
    return strip_prefix(sup) if sup else None


def load_model(path: Path):
    doc = json.loads(path.read_text(encoding="utf-8"))

    def walk(node: dict):
        yield node
        for child in node.get("children", []):
            yield from walk(child)

    all_nodes = [nested for node in doc["clafers"] for nested in walk(node)]
    nodes = {strip_prefix(node["name"]): node for node in all_nodes}
    typed: dict[str, list[dict]] = {key: [] for key in ["Requirement", "System", "Subsystem", "Actor", "Asset", "Component", "Event", "Scenario"]}
    for node in all_nodes:
        kind = classify(node)
        if kind in typed:
            typed[kind].append(node)
    return doc, nodes, typed


def labels_for_requirements(typed: dict[str, list[dict]]) -> dict[str, str]:
    labels = {}
    for req in typed["Requirement"]:
        children = group_children(req["children"])
        label_node = children.get("label", [])
        labels[strip_prefix(req["name"])] = decode_string(label_node[0]["value"]) if label_node else strip_prefix(req["name"])
    return labels


def desc_for(node: dict) -> str:
    children = group_children(node["children"])
    for key in ["description", "c1_description", "c2_description", "c3_description", "c4_description", "c5_description", "c6_description"]:
        if key in children:
            return decode_string(children[key][0]["value"])
    return ""


def refs(node: dict, field: str) -> list[str]:
    children = group_children(node["children"])
    return [strip_prefix(child["value"]) for child in children.get(field, []) if child.get("value")]


def render(path_in: Path) -> str:
    _doc, _nodes, typed = load_model(path_in)
    req_labels = labels_for_requirements(typed)

    lines = ["@startuml", "left to right direction", "hide empty members", "skinparam linetype ortho", ""]

    lines.append('rectangle "Requirements" {')
    for req in typed["Requirement"]:
        name = strip_prefix(req["name"])
        lines.append(f'  rectangle "{req_labels[name]}" as req_{name}')
    lines.append("}")
    lines.append("")

    lines.append('rectangle "Subsystems" {')
    for subsystem in typed["Subsystem"]:
        name = strip_prefix(subsystem["name"])
        lines.append(f'  rectangle "{name}" as sub_{name}')
    lines.append("}")
    lines.append("")

    lines.append('rectangle "Actors" {')
    for actor in typed["Actor"]:
        name = strip_prefix(actor["name"])
        lines.append(f'  actor "{name}" as actor_{name}')
    lines.append("}")
    lines.append("")

    lines.append('rectangle "Assets" {')
    for asset in typed["Asset"]:
        name = strip_prefix(asset["name"])
        lines.append(f'  artifact "{name}" as asset_{name}')
    lines.append("}")
    lines.append("")

    lines.append('rectangle "Events" {')
    for event in typed["Event"]:
        name = strip_prefix(event["name"])
        lines.append(f'  usecase "{name}" as event_{name}')
    lines.append("}")
    lines.append("")

    lines.append('rectangle "Scenarios" {')
    for scenario in typed["Scenario"]:
        name = strip_prefix(scenario["name"])
        lines.append(f'  card "{name}" as scenario_{name}')
    lines.append("}")
    lines.append("")

    for subsystem in typed["Subsystem"]:
        sub_name = strip_prefix(subsystem["name"])
        for dep in refs(subsystem, "dependsOn"):
            lines.append(f'sub_{sub_name} --> sub_{dep} : dependsOn')
        for req in refs(subsystem, "satisfies"):
            lines.append(f'sub_{sub_name} --> req_{req} : satisfies')
        for asset in refs(subsystem, "assets"):
            lines.append(f'sub_{sub_name} --> asset_{asset} : holds')

    for actor in typed["Actor"]:
        actor_name = strip_prefix(actor["name"])
        for sub in refs(actor, "uses"):
            lines.append(f'actor_{actor_name} --> sub_{sub} : uses')

    for asset in typed["Asset"]:
        asset_name = strip_prefix(asset["name"])
        for actor in refs(asset, "heldByActor"):
            lines.append(f'actor_{actor} --> asset_{asset_name} : holds')
        for sub in refs(asset, "heldBySystem"):
            lines.append(f'sub_{sub} --> asset_{asset_name} : stores')

    for event in typed["Event"]:
        event_name = strip_prefix(event["name"])
        for sub in refs(event, "touches"):
            lines.append(f'event_{event_name} --> sub_{sub} : touches')
        for req in refs(event, "preserves"):
            lines.append(f'event_{event_name} --> req_{req} : preserves')

    for scenario in typed["Scenario"]:
        scenario_name = strip_prefix(scenario["name"])
        for event in refs(scenario, "steps"):
            lines.append(f'scenario_{scenario_name} --> event_{event} : step')
        for req in refs(scenario, "validates"):
            lines.append(f'scenario_{scenario_name} --> req_{req} : validates')

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a traceability PlantUML diagram from an instance JSON.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(args.input), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())