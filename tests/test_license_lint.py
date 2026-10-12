import io
import json
import contextlib
import tempfile
import unittest
from pathlib import Path

from license_lint.cli import main
from license_lint.detect import detect_license_text, normalize_declared
from license_lint.scanner import scan

MIT_TEXT = "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy"
GPL3_TEXT = "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007"
APACHE_TEXT = "Apache License\nVersion 2.0, January 2004"


def make_repo(files: dict[str, str]) -> Path:
    tmp = Path(tempfile.mkdtemp())
    for name, content in files.items():
        (tmp / name).write_text(content, encoding="utf-8")
    return tmp


class DetectTests(unittest.TestCase):
    def test_detects_known_licenses(self):
        self.assertEqual(detect_license_text(MIT_TEXT), "MIT")
        self.assertEqual(detect_license_text(GPL3_TEXT), "GPL-3.0-only")
        self.assertEqual(detect_license_text(APACHE_TEXT), "Apache-2.0")

    def test_unknown_text_returns_none(self):
        self.assertIsNone(detect_license_text("All rights reserved."))

    def test_normalize_declared_aliases(self):
        self.assertEqual(normalize_declared("Apache 2.0"), "Apache-2.0")
        self.assertEqual(normalize_declared(" 'mit' "), "MIT")
        self.assertEqual(normalize_declared(""), None)


class ScanTests(unittest.TestCase):
    def test_missing_license_is_error(self):
        report = scan(make_repo({}))
        self.assertTrue(report.has_errors)
        self.assertEqual(report.findings[0].code, "LICENSE_MISSING")

    def test_matching_manifest_has_no_errors(self):
        repo = make_repo({"LICENSE": MIT_TEXT, "pyproject.toml": '[project]\nlicense = "MIT"\n'})
        report = scan(repo)
        self.assertFalse(report.has_errors)
        self.assertEqual(report.declared, {"pyproject.toml": "MIT"})

    def test_pyproject_license_is_read_from_project_section_and_single_quotes(self):
        text = "[tool.example]\nlicense = 'Apache-2.0'\n[project]\nlicense = 'MIT'\n"
        report = scan(make_repo({"LICENSE": MIT_TEXT, "pyproject.toml": text}))
        self.assertEqual(report.declared, {"pyproject.toml": "MIT"})
        self.assertFalse(report.has_errors)

    def test_pyproject_inline_license_text(self):
        text = '[project]\nlicense = { text = "MIT" }\n'
        report = scan(make_repo({"LICENSE": MIT_TEXT, "pyproject.toml": text}))
        self.assertEqual(report.declared, {"pyproject.toml": "MIT"})
        self.assertFalse(report.has_errors)

    def test_cargo_license_is_read_from_package_section(self):
        text = "[workspace]\nlicense = 'Apache-2.0'\n[package]\nlicense = 'MIT'\n"
        report = scan(make_repo({"LICENSE": MIT_TEXT, "Cargo.toml": text}))
        self.assertEqual(report.declared, {"Cargo.toml": "MIT"})
        self.assertFalse(report.has_errors)

    def test_npm_legacy_license_object(self):
        package = json.dumps({"license": {"type": "MIT", "url": "https://example.test/license"}})
        report = scan(make_repo({"LICENSE": MIT_TEXT, "package.json": package}))
        self.assertEqual(report.declared, {"package.json": "MIT"})
        self.assertFalse(report.has_errors)

    def test_mismatch_is_error(self):
        repo = make_repo({"LICENSE": MIT_TEXT, "package.json": json.dumps({"license": "Apache 2.0"})})
        report = scan(repo)
        self.assertIn("LICENSE_MISMATCH", [f.code for f in report.findings])

    def test_manifest_without_license_warns(self):
        repo = make_repo({"LICENSE": MIT_TEXT, "Cargo.toml": "[package]\nname = 'x'\n"})
        report = scan(repo)
        self.assertNotIn("Cargo.toml", report.declared)
        self.assertIn("MANIFEST_NO_LICENSE", [f.code for f in report.findings])

    def test_denied_license_is_error(self):
        report = scan(make_repo({"LICENSE": GPL3_TEXT}), deny={"GPL-3.0-only"})
        self.assertIn("DENIED_LICENSE", [f.code for f in report.findings])

    def test_deny_alias_is_normalized(self):
        report = scan(make_repo({"LICENSE": MIT_TEXT}), deny={"mit"})
        self.assertIn("DENIED_LICENSE", [f.code for f in report.findings])

    def test_copyleft_is_info_only(self):
        report = scan(make_repo({"LICENSE": GPL3_TEXT}))
        self.assertFalse(report.has_errors)
        self.assertIn("COPYLEFT", [f.code for f in report.findings])

    def test_not_a_directory(self):
        report = scan("/definitely/not/here")
        self.assertEqual(report.findings[0].code, "NOT_A_DIRECTORY")


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_clean_repo_exit_zero(self):
        code, out = self.run_cli([str(make_repo({"LICENSE": MIT_TEXT}))])
        self.assertEqual(code, 0)
        self.assertIn("OK: no findings", out)

    def test_missing_license_exit_one(self):
        code, _ = self.run_cli([str(make_repo({}))])
        self.assertEqual(code, 1)

    def test_json_output_is_valid(self):
        code, out = self.run_cli(["--json", str(make_repo({"LICENSE": MIT_TEXT}))])
        data = json.loads(out)
        self.assertEqual(data["detected_license"], "MIT")
        self.assertEqual(code, 0)

    def test_strict_fails_on_warning(self):
        repo = make_repo({"LICENSE": MIT_TEXT, "Cargo.toml": "[package]\n"})
        code, _ = self.run_cli(["--strict", str(repo)])
        self.assertEqual(code, 1)
        code, _ = self.run_cli([str(repo)])
        self.assertEqual(code, 0)

    def test_version_matches_package_metadata(self):
        from license_lint import __version__

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as raised:
            main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(buf.getvalue().strip(), __version__)


if __name__ == "__main__":
    unittest.main()
