"""Command-line entry point: license-lint [PATH] [--deny ID] [--json] [--strict]."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .render import to_json, to_text
from .scanner import scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="license-lint", description="Offline license checks for a repository.")
    parser.add_argument("path", nargs="?", default=".", help="repository directory (default: current)")
    parser.add_argument("--deny", action="append", default=[], metavar="SPDX", help="fail if this SPDX id is used (repeatable)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = scan(args.path, deny=set(args.deny))
    output = to_json(report) if args.json else to_text(report)
    sys.stdout.write(output)
    failed = report.has_errors or (args.strict and any(f.level == "warning" for f in report.findings))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
