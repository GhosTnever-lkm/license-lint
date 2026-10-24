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


def _toml_section(text: str, section: str) -> str:
    """Return the source lines belonging to one TOML table."""
    current = None
    selected: list[str] = []
    for line in text.splitlines():
        header = re.match(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$", line)
        if header:
            current = header.group(1).strip()
        elif current == section:
            selected.append(line)
    return "\n".join(selected)


def _toml_string_value(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*(?:#.*)?$", text, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    direct = re.fullmatch(r"(['\"])(.*?)\1", value)
    if direct:
        return direct.group(2)
    inline_text = re.search(r"\btext\s*=\s*(['\"])(.*?)\1", value)
    return inline_text.group(2) if inline_text else None


def _declared_from_pyproject(text: str) -> str | None:
    return _toml_string_value(_toml_section(text, "project"), "license")


def _pyproject_license_file(text: str) -> str | None:
    """Return the legacy PEP 621 license table's file path, if present."""
    section = _toml_section(text, "project")
    match = re.search(r"^\s*license\s*=\s*(\{.*?\})\s*(?:#.*)?$", section, re.MULTILINE)
    if not match:
        return None
    file_match = re.search(r"\bfile\s*=\s*(['\"])(.*?)\1", match.group(1))
    return file_match.group(2) if file_match else None


def _declared_from_cargo(text: str) -> str | None:
    return _toml_string_value(_toml_section(text, "package"), "license")


def _declared_from_package_json(text: str) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    value = data.get("license") if isinstance(data, dict) else None
    if isinstance(value, dict):
        value = value.get("type")
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
        if manifest == "pyproject.toml":
            license_file = _pyproject_license_file(text)
            if license_file is not None:
                candidate = (base / license_file).resolve()
                try:
                    candidate.relative_to(base.resolve())
                except ValueError:
                    report.add("warning", "MANIFEST_LICENSE_FILE_UNSAFE", "pyproject.toml license file points outside the repository")
                    continue
                if not candidate.is_file():
                    report.add("warning", "MANIFEST_LICENSE_FILE_MISSING", f"pyproject.toml license file {license_file!r} does not exist")
                    continue
                license_text = _read_small(candidate)
                declared_license = detect_license_text(license_text) if license_text is not None else None
                if declared_license is None:
                    report.add("warning", "MANIFEST_LICENSE_FILE_UNRECOGNIZED", f"pyproject.toml license file {license_file!r} is too large, unreadable, or unrecognized")
                    continue
                report.declared[manifest] = declared_license
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
        denied = {normalize_declared(d) or d.strip() for d in deny}
        for label, spdx in [(report.license_file or "LICENSE", report.detected_license)] + list(report.declared.items()):
            if spdx and spdx in denied:
                report.add("error", "DENIED_LICENSE", f"{label} uses denied license {spdx}")

    if report.detected_license in COPYLEFT_IDS:
        report.add("info", "COPYLEFT", f"project is licensed under copyleft {report.detected_license}")
    return report
