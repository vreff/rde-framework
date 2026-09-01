#!/usr/bin/env python3
"""Convert Chocosolver instance output into JSON artifacts."""

import argparse
import glob
import json
import os
from pathlib import Path
import re
import sys

from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput
from lark.indenter import Indenter


INSTANCE_GRAMMAR = r"""
  start: _NL* (instance _NL*)+

  instance: instance_begin _NL* (node)+ _NL* instance_end

  ?instance_begin: "=== Instance " INT " Begin ===" | "=== Instance " INT "Begin ==="
  ?instance_end:   "--- Instance " INT " End ---" | "--- Instance " INT "End ---"

  node: clafer _NL [_INDENT (node)+ _DEDENT]

  %declare _INDENT _DEDENT

  clafer: NAME[index] [_EXTENDS NAME] [_REF TYPE _EQUALS VALUE]

  ?index: _DOLLAR INT

  VALUE: NAME | SIGNED_INT | STRING

  TYPE: "int" | "real" | "double" | "string" | NAME

  %import common.CNAME -> NAME
  %import common.INT -> INT
  %import common.SIGNED_INT -> SIGNED_INT
  %import common.ESCAPED_STRING -> STRING
  %import common.WS_INLINE
  %ignore WS_INLINE

  _NL: /\r?\n[\t ]*/
  _DOLLAR: /\$/
  _EXTENDS: ":"
  _REF: "->"
  _EQUALS: "="
"""


class NodeIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


class DictTransformer(Transformer):
    def start(self, args):
        return args

    def instance(self, args):
        begin = int(args[0])
        end = int(args[-1])
        if begin != end:
            raise ValueError(f"mismatched instance bounds: {begin} != {end}")
        return {"instance": begin, "clafers": args[1:-1]}

    def node(self, args):
        node = args[0]
        node["children"] = args[1:]
        return node

    def clafer(self, args):
        value = args[4].value if args[4] else None
        value_type = args[3].value if args[3] else None
        if value_type == "int" and value is not None:
            value = int(value)
        return {
            "name": args[0].value,
            "index": int(args[1]) if args[1] else None,
            "super": args[2].value if args[2] else None,
            "type": value_type,
            "value": value,
        }


INSTANCE_PARSER = Lark(
    INSTANCE_GRAMMAR,
    parser="lalr",
    postlex=NodeIndenter(),
    transformer=DictTransformer(),
)


def parse_instances(text: str) -> list[dict]:
    return INSTANCE_PARSER.parse(text)


def extract_complete_instances(text: str) -> str:
    """Return concatenated complete instance blocks from raw solver output."""
    pattern = re.compile(
        r"=== Instance\s+(\d+)\s*Begin ===.*?--- Instance\s+\1\s*End ---",
        re.DOTALL,
    )
    matches = [m.group(0) for m in pattern.finditer(text)]
    return "\n\n".join(matches)


def write_json_outputs(input_file: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    content = input_file.read_text(encoding="utf-8")
    try:
        instances = parse_instances(content)
    except UnexpectedInput as exc:
        recovered = extract_complete_instances(content)
        if not recovered:
            raise ValueError(f"error parsing {input_file}: {exc}") from exc
        try:
            instances = parse_instances(recovered)
        except UnexpectedInput as nested_exc:
            raise ValueError(f"error parsing {input_file}: {nested_exc}") from nested_exc

    stem = input_file.stem
    (output_dir / f"{stem}.json").write_text(json.dumps(instances, indent=2), encoding="utf-8")

    for old in glob.glob(str(output_dir / f"{stem}.*.json")):
        os.remove(old)

    for instance in instances:
        instance_path = output_dir / f"{stem}.{instance['instance']}.json"
        instance_path.write_text(json.dumps(instance, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Chocosolver output into JSON files.")
    parser.add_argument("--file", required=True, type=Path, help="Input instances.txt file")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for JSON outputs")
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"error: input file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        write_json_outputs(args.file, args.output_dir)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())