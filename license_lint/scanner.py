"""Scan a repository directory for license files and declared licenses."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .detect import COPYLEFT_IDS, detect_license_text, normalize_declared

LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
MAX_FILE_BYTES = 512 * 1024


@dataclass
class Finding:
    level: str  # "error" | "warning" | "info"
    code: str
    message: str


@dataclass
class Report:
    root: str
    license_file: str | None = None
    detected_license: str | None = None
    declared: dict[str, str] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    def add(self, level: str, code: str, message: str) -> None:
        self.findings.append(Finding(level, code, message))

    @property
    def has_errors(self) -> bool:
        return any(f.level == "error" for f in self.findings)


def _read_small(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _declared_from_pyproject(text: str) -> str | None:
    match = re.search(r'^\s*license\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def _declared_from_cargo(text: str) -> str | None:
    match = re.search(r'^\s*license\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def _declared_from_package_json(text: str) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    value = data.get("license") if isinstance(data, dict) else None
    return value if isinstance(value, str) else None


MANIFESTS = {
    "pyproject.toml": _declared_from_pyproject,
    "Cargo.toml": _declared_from_cargo,
    "package.json": _declared_from_package_json,
}


def scan(root: str | Path, deny: set[str] | None = None) -> Report:
    base = Path(root)
    report = Report(root=str(base))
    if not base.is_dir():
        report.add("error", "NOT_A_DIRECTORY", f"{base} is not a directory")
        return report

    for name in LICENSE_NAMES:
        candidate = base / name
        if candidate.is_file():
            report.license_file = name
            text = _read_small(candidate)
            if text is None:
                report.add("warning", "LICENSE_UNREADABLE", f"{name} is too large or unreadable")
            else:
                report.detected_license = detect_license_text(text)
                if report.detected_license is None:
                    report.add("warning", "LICENSE_UNRECOGNIZED", f"{name} does not match a known license")
            break
    if report.license_file is None:
        report.add("error", "LICENSE_MISSING", "no LICENSE file found")

    for manifest, reader in MANIFESTS.items():
        path = base / manifest
        if not path.is_file():
            continue
        text = _read_small(path)
        if text is None:
            continue
        raw = reader(text)
        if raw is None:
            report.add("warning", "MANIFEST_NO_LICENSE", f"{manifest} declares no license field")
            continue
        spdx = normalize_declared(raw) or raw
        report.declared[manifest] = spdx

    if report.detected_license and report.declared:
        for manifest, spdx in report.declared.items():
            if spdx != report.detected_license:
                report.add(
                    "error",
                    "LICENSE_MISMATCH",
                    f"{manifest} declares {spdx}, but {report.license_file} looks like {report.detected_license}",
                )

    if deny:
        denied = {d.strip() for d in deny}
        for label, spdx in [(report.license_file or "LICENSE", report.detected_license)] + list(report.declared.items()):
            if spdx and spdx in denied:
                report.add("error", "DENIED_LICENSE", f"{label} uses denied license {spdx}")

    if report.detected_license in COPYLEFT_IDS:
        report.add("info", "COPYLEFT", f"project is licensed under copyleft {report.detected_license}")
    return report
