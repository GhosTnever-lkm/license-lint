"""Heuristic SPDX detection for LICENSE texts and manifest license fields."""

from __future__ import annotations

import re

# Ordered from most to least specific. Each entry: (SPDX id, required phrases).
_LICENSE_SIGNATURES: list[tuple[str, tuple[str, ...]]] = [
    ("AGPL-3.0-only", ("gnu affero general public license", "version 3")),
    ("GPL-3.0-only", ("gnu general public license", "version 3")),
    ("GPL-2.0-only", ("gnu general public license", "version 2")),
    ("LGPL-3.0-only", ("gnu lesser general public license", "version 3")),
    ("Apache-2.0", ("apache license", "version 2.0")),
    ("MPL-2.0", ("mozilla public license", "version 2.0")),
    ("Unlicense", ("this is free and unencumbered software",)),
    ("BSD-3-Clause", ("redistribution and use in source and binary forms", "neither the name")),
    ("BSD-2-Clause", ("redistribution and use in source and binary forms",)),
    ("ISC", ("permission to use, copy, modify, and/or distribute this software",)),
    ("MIT", ("permission is hereby granted, free of charge",)),
]

# Patterns accepted in manifest fields. Values are normalised to lowercase first.
_SPDX_ALIASES = {
    "mit": "MIT",
    "apache-2.0": "Apache-2.0",
    "apache 2.0": "Apache-2.0",
    "bsd-3-clause": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "isc": "ISC",
    "mpl-2.0": "MPL-2.0",
    "unlicense": "Unlicense",
    "gpl-2.0-only": "GPL-2.0-only",
    "gpl-3.0-only": "GPL-3.0-only",
    "gpl-3.0": "GPL-3.0-only",
    "lgpl-3.0-only": "LGPL-3.0-only",
    "agpl-3.0-only": "AGPL-3.0-only",
    "agpl-3.0": "AGPL-3.0-only",
}

COPYLEFT_IDS = frozenset(
    {"GPL-2.0-only", "GPL-3.0-only", "LGPL-3.0-only", "AGPL-3.0-only"}
)


def detect_license_text(text: str) -> str | None:
    """Return the SPDX id that best matches a LICENSE file, or None."""
    normalized = re.sub(r"\s+", " ", text.lower())
    for spdx, phrases in _LICENSE_SIGNATURES:
        if all(phrase in normalized for phrase in phrases):
            return spdx
    return None


def normalize_declared(value: str) -> str | None:
    """Map a manifest license string (e.g. 'MIT', 'Apache 2.0') to an SPDX id."""
    cleaned = value.strip().strip("\"'").lower()
    if not cleaned:
        return None
    return _SPDX_ALIASES.get(cleaned, value.strip())
