"""Export or verify the FastAPI-generated OpenAPI contract.

The committed JSON is a reviewable API baseline.  It is generated from the
same ``app`` object used by the service, so CI can detect undocumented route
or schema drift without starting a database or background scheduler.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT_DIR / "docs" / "openapi.json"


def render_openapi() -> str:
    sys.path.insert(0, str(ROOT_DIR))
    from app.main import app

    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed OpenAPI baseline differs from the app",
    )
    args = parser.parse_args()

    rendered = render_openapi()
    if args.check:
        if not OUTPUT_PATH.is_file():
            print(f"OpenAPI baseline is missing: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        if OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            print(
                "OpenAPI baseline is stale; run "
                "`python scripts/export_openapi.py` and review docs/openapi.json",
                file=sys.stderr,
            )
            return 1
        print(f"OpenAPI baseline is up to date: {OUTPUT_PATH}")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote OpenAPI baseline: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
