#!/usr/bin/env python3
"""Contract-drift check: api-reference/service-catalog.mdx vs the generated backend contract.

The backend generates docs/api-contract/methods.txt from the facade and admin service XML
(./gradlew :runtime:component:darpan:generateApiContract in darpan-backend). This script
fails when the catalog documents a method the contract does not define, and reports
(without failing) contract methods the catalog has not documented yet.

Usage: python3 scripts/check_service_catalog.py <path-to-methods.txt>
Run from the darpan-docs repo root. Exits 1 on drift.
"""
import re
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "api-reference" / "service-catalog.mdx"


def parse_catalog(text: str) -> set[str]:
    methods: set[str] = set()
    prefix = None
    for line in text.splitlines():
        section = re.match(r"^#{2,3}\s+.*\(`((?:facade|admin)\.[A-Za-z]+)`\)", line)
        if section:
            prefix = section.group(1)
            continue
        if re.match(r"^#{2,3}\s+", line):
            prefix = None  # section without a facade/admin prefix in the heading (e.g. Integration components)
            continue
        if not line.strip().startswith("|"):
            continue
        # Integration-components table shape: | `component` | `facade.X` | `m1`, `m2` |
        row_facade = re.search(r"\|\s*`((?:facade|admin)\.[A-Za-z]+)`\s*\|", line)
        row_prefix = row_facade.group(1) if row_facade else prefix
        if row_prefix is None:
            continue
        for token in re.findall(r"`([a-zA-Z]+#[A-Za-z0-9]+)`", line):
            methods.add(f"{row_prefix}.{token}")
    return methods


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    contract = {
        line.strip()
        for line in Path(sys.argv[1]).read_text().splitlines()
        if line.strip()
    }
    documented = parse_catalog(CATALOG.read_text())
    if not documented:
        print("ERROR: parsed zero methods from the catalog — format changed? Fix the parser or the catalog.")
        return 1

    phantom = sorted(documented - contract)
    undocumented = sorted(contract - documented)

    if undocumented:
        print(f"note: {len(undocumented)} contract methods not yet documented in the catalog:")
        for m in undocumented:
            print(f"  - {m}")
    if phantom:
        print(f"DRIFT: service-catalog.mdx documents {len(phantom)} methods the backend contract does not define:")
        for m in phantom:
            print(f"  - {m}")
        return 1
    print(f"service catalog OK: {len(documented)} documented methods all exist in the contract "
          f"({len(contract)} total).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
