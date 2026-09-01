#!/usr/bin/env python3
"""Generate a Markdown traceability report from a Clafer instance JSON."""

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


def refs(node: dict, field: str) -> list[str]:
    children = group_children(node["children"])
    return [strip_prefix(child["value"]) for child in children.get(field, []) if child.get("value")]


def desc(node: dict) -> str:
    children = group_children(node["children"])
    for key in ["description", "c1_description", "c2_description", "c3_description", "c4_description", "c5_description", "c6_description"]:
        if key in children:
            return decode_string(children[key][0]["value"])
    return ""


def label(node: dict) -> str:
    children = group_children(node["children"])
    if "label" in children:
        return decode_string(children["label"][0]["value"])
    for key in ["c1_label", "c2_label"]:
        if key in children:
            return decode_string(children[key][0]["value"])
    return strip_prefix(node["name"])


def load(path: Path):
    doc = json.loads(path.read_text(encoding="utf-8"))

    def walk(node: dict):
        yield node
        for child in node.get("children", []):
            yield from walk(child)

    all_nodes = [nested for node in doc["clafers"] for nested in walk(node)]
    typed: dict[str, list[dict]] = {key: [] for key in ["Requirement", "System", "Subsystem", "Actor", "Asset", "Component", "Event", "Scenario"]}
    for node in all_nodes:
        kind = classify(node)
        if kind in typed:
            typed[kind].append(node)
    return typed


def render(path: Path) -> str:
    typed = load(path)
    title = "System Traceability Report"
    if typed["System"]:
        title = f"{strip_prefix(typed['System'][0]['name'])} Traceability Report"
    lines = [f"# {title}", ""]

    if typed["System"]:
        system = typed["System"][0]
        lines.extend(["## System", "", f"- Name: `{strip_prefix(system['name'])}`"])
        lines.append(f"- Subsystems: {', '.join(f'`{name}`' for name in refs(system, 'subSystems'))}")
        lines.append(f"- Events: {', '.join(f'`{name}`' for name in refs(system, 'events'))}")
        lines.append(f"- Scenarios: {', '.join(f'`{name}`' for name in refs(system, 'scenarios'))}")
        lines.append("")

    lines.extend(["## Requirements", ""])
    for req in typed["Requirement"]:
        lines.append(f"- `{strip_prefix(req['name'])}`: {label(req)}")
    lines.append("")

    lines.extend(["## Subsystems", ""])
    for subsystem in typed["Subsystem"]:
        name = strip_prefix(subsystem["name"])
        lines.append(f"### `{name}`")
        lines.append(desc(subsystem))
        lines.append("")
        lines.append(f"- Depends on: {', '.join(f'`{value}`' for value in refs(subsystem, 'dependsOn')) or 'none'}")
        lines.append(f"- Satisfies: {', '.join(f'`{value}`' for value in refs(subsystem, 'satisfies')) or 'none'}")
        lines.append(f"- Actors: {', '.join(f'`{value}`' for value in refs(subsystem, 'actors')) or 'none'}")
        lines.append(f"- Assets: {', '.join(f'`{value}`' for value in refs(subsystem, 'assets')) or 'none'}")
        lines.append(f"- Components: {', '.join(f'`{value}`' for value in refs(subsystem, 'components')) or 'none'}")
        lines.append("")

    lines.extend(["## Events", ""])
    for event in typed["Event"]:
        name = strip_prefix(event["name"])
        lines.append(f"### `{name}`")
        lines.append(desc(event))
        lines.append("")
        lines.append(f"- Touches: {', '.join(f'`{value}`' for value in refs(event, 'touches')) or 'none'}")
        lines.append(f"- Preserves: {', '.join(f'`{value}`' for value in refs(event, 'preserves')) or 'none'}")
        lines.append("")

    lines.extend(["## Scenarios", ""])
    for scenario in typed["Scenario"]:
        name = strip_prefix(scenario["name"])
        lines.append(f"### `{name}`")
        lines.append(desc(scenario))
        lines.append("")
        lines.append(f"- Steps: {', '.join(f'`{value}`' for value in refs(scenario, 'steps')) or 'none'}")
        lines.append(f"- Validates: {', '.join(f'`{value}`' for value in refs(scenario, 'validates')) or 'none'}")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown traceability report from an instance JSON.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(args.input), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())