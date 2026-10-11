"""Text and JSON output for license-lint reports."""

from __future__ import annotations

import json
from dataclasses import asdict

from .scanner import Report


def to_json(report: Report) -> str:
    data = asdict(report)
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_text(report: Report) -> str:
    lines = [f"license-lint: {report.root}"]
    lines.append(f"LICENSE file: {report.license_file or 'missing'}")
    lines.append(f"Detected license: {report.detected_license or 'unknown'}")
    for manifest, spdx in sorted(report.declared.items()):
        lines.append(f"Declared in {manifest}: {spdx}")
    if not report.findings:
        lines.append("OK: no findings")
    for f in report.findings:
        lines.append(f"[{f.level.upper()}] {f.code}: {f.message}")
    return "\n".join(lines) + "\n"
