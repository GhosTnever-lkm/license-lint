# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Update the CI examples and workflows to current, commit-pinned GitHub Actions.

## [0.1.3] - 2026-10-25

### Added

- Read legacy PEP 621 `license = { file = "..." }` declarations from repository-local files and compare their detected license with `LICENSE`.
- Report missing, unsafe, oversized, unreadable, or unrecognized legacy license files explicitly.
- Add regression tests for matching, mismatching, missing, and repository-escaping license file paths.

## [0.1.2] - 2026-10-13

### Added

- Read TOML license declarations only from the relevant `[project]` or `[package]` table.
- Support single-quoted TOML strings, inline text values, and legacy npm `{type: ...}` license objects.
- Normalize `--deny` aliases such as `mit` to SPDX identifiers.
- Add CLI version regression coverage, release badges, install guidance, and tagged wheel/sdist releases with SHA-256 checksums.

### Fixed

- Avoid false license mismatches caused by unrelated TOML tables or case variants in `--deny`.

## [0.1.1] - 2026-10-11

### Added

- CI now also runs the test suite on Windows (windows-latest), not only Ubuntu.


## [0.1.0] - 2026-10-11

### Added

- LICENSE detection for MIT, Apache-2.0, BSD-2/3-Clause, ISC, MPL-2.0, Unlicense, GPL/LGPL/AGPL.
- Manifest checks for `pyproject.toml`, `Cargo.toml` and `package.json`.
- `--deny` list, `--json` output and `--strict` mode.

[Unreleased]: https://github.com/GhosTnever-lkm/license-lint/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/GhosTnever-lkm/license-lint/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/GhosTnever-lkm/license-lint/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/GhosTnever-lkm/license-lint/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/GhosTnever-lkm/license-lint/releases/tag/v0.1.0
