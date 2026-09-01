#!/usr/bin/env python3
"""Convert a simple Lando requirements file into Clafer requirement instances."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADER_RE = re.compile(r"^\s*requirements\s+.+$", re.IGNORECASE)
NON_ALNUM_RE = re.compile(r"[^A-Za-z0-9]+")


def slugify(name: str) -> str:
    compact = NON_ALNUM_RE.sub("", name).lower()
    if not compact:
        raise ValueError(f"cannot derive requirement identifier from: {name!r}")
    if compact[0].isdigit():
        compact = f"r{compact}"
    return compact


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def parse_lando_requirements(path: Path) -> list[tuple[str, str]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    non_empty = [line for line in lines if line]
    if not non_empty:
        raise ValueError("requirements file is empty")

    start = 0
    if HEADER_RE.match(non_empty[0]):
        start = 1

    entries = non_empty[start:]
    if len(entries) % 2 != 0:
        raise ValueError("expected alternating requirement title/description lines")

    pairs: list[tuple[str, str]] = []
    for idx in range(0, len(entries), 2):
        title = entries[idx]
        description = entries[idx + 1]
        pairs.append((title, description))
    return pairs


def render_cfr(requirements: list[tuple[str, str]], source_hint: str) -> str:
    out = [f"// Generated from {source_hint}", ""]
    seen: set[str] = set()
    for title, description in requirements:
        req_id = slugify(title)
        if req_id in seen:
            raise ValueError(f"duplicate requirement identifier generated: {req_id}")
        seen.add(req_id)
        out.append(f"{req_id}: Requirement")
        out.append(f"    [ label = \"{esc(title)}\" ]")
        out.append(f"    [ description = \"{esc(description)}\" ]")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate requirements.generated.cfr from a .lando requirements file")
    parser.add_argument("--input", required=True, type=Path, help="Path to a requirements .lando file")
    parser.add_argument("--output", required=True, type=Path, help="Output .cfr path")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"error: requirements input not found: {args.input}", file=sys.stderr)
        return 1

    try:
        requirements = parse_lando_requirements(args.input)
        rendered = render_cfr(requirements, args.input.as_posix())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
