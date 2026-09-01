#!/usr/bin/env python3
"""Fail when any generated requirement is not referenced by events/scenarios."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQ_DECL_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*Requirement\s*$")
# Matches lines like: [ preserves = foo, bar ] or [ validates = foo ]
LINK_RE = re.compile(r"\[\s*(preserves|validates)\s*=\s*([^\]]+)\]")
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_requirements(requirements_file: Path) -> set[str]:
    reqs: set[str] = set()
    for line in requirements_file.read_text(encoding="utf-8").splitlines():
        m = REQ_DECL_RE.match(line)
        if m:
            reqs.add(m.group(1))
    return reqs


def parse_links(architecture_file: Path) -> set[str]:
    linked: set[str] = set()
    for line in architecture_file.read_text(encoding="utf-8").splitlines():
        m = LINK_RE.search(line)
        if not m:
            continue
        values = m.group(2)
        for token in TOKEN_RE.findall(values):
            linked.add(token)
    return linked


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check that every generated requirement is referenced by at least one "
            "event preserves-link or scenario validates-link in architecture.cfr"
        )
    )
    parser.add_argument("--requirements", required=True, help="Path to requirements.generated.cfr")
    parser.add_argument("--architecture", required=True, help="Path to architecture.cfr")
    args = parser.parse_args()

    req_file = Path(args.requirements)
    arch_file = Path(args.architecture)

    if not req_file.is_file():
        print(f"[error] requirements file not found: {req_file}", file=sys.stderr)
        return 2
    if not arch_file.is_file():
        print(f"[error] architecture file not found: {arch_file}", file=sys.stderr)
        return 2

    requirements = parse_requirements(req_file)
    linked = parse_links(arch_file)

    if not requirements:
        print("[error] no requirements found in generated file", file=sys.stderr)
        return 2

    missing = sorted(requirements - linked)

    if missing:
        print("[error] uncovered requirement(s):", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 1

    print(f"[ok] coverage check passed: {len(requirements)}/{len(requirements)} requirements linked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
