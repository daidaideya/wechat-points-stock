"""Fail when installed application dependencies have an unknown or disallowed license."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement


ALLOWED_LICENSES = {
    "0BSD",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "CC0-1.0",
    "ISC",
    "MIT",
    "MPL-2.0",
    "PSF-2.0",
    "Python-2.0",
    "Unlicense",
    "Zlib",
}
LICENSE_CLASSIFIER_MAP = {
    "Apache Software License": "Apache-2.0",
    "BSD License": "BSD-3-Clause",
    "ISC License (ISCL)": "ISC",
    "MIT License": "MIT",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "Python Software Foundation License": "PSF-2.0",
}
LICENSE_SPLIT_RE = re.compile(r"\s+(?:AND|OR)\s+|\s*[,/]\s*|[()]", re.IGNORECASE)


def canonical_license(value: str) -> str:
    value = " ".join(value.strip().split())
    replacements = {
        "Apache 2.0": "Apache-2.0",
        "Apache License 2.0": "Apache-2.0",
        "BSD 2-Clause": "BSD-2-Clause",
        "BSD 3-Clause": "BSD-3-Clause",
        "MIT License": "MIT",
        "Python Software Foundation License": "PSF-2.0",
    }
    return replacements.get(value, value)


def allowed_license(value: str) -> bool:
    parts = [canonical_license(part) for part in LICENSE_SPLIT_RE.split(value) if part.strip()]
    return bool(parts) and all(part in ALLOWED_LICENSES for part in parts)


def read_requirement_names(path: Path, seen: set[Path] | None = None) -> set[str]:
    seen = set() if seen is None else seen
    path = path.resolve()
    if path in seen:
        return set()
    seen.add(path)

    names: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-r ") or line.startswith("--requirement "):
            included = line.split(maxsplit=1)[1]
            names.update(read_requirement_names(path.parent / included, seen))
            continue
        if line.startswith("-"):
            continue
        requirement = Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate():
            names.add(requirement.name)
    return names


def python_license(dist: metadata.Distribution) -> list[str]:
    values = list(dist.metadata.get_all("License-Expression") or [])
    values.extend(dist.metadata.get_all("License") or [])
    values = [value for value in values if value and value.upper() not in {"UNKNOWN", "NONE"}]
    if values:
        return [canonical_license(value) for value in values]

    classifiers = dist.metadata.get_all("Classifier") or []
    for classifier in classifiers:
        prefix = "License :: OSI Approved :: "
        if classifier.startswith(prefix):
            label = classifier[len(prefix) :]
            mapped = LICENSE_CLASSIFIER_MAP.get(label)
            if mapped:
                return [mapped]
    return []


def collect_python_distributions(requirements: list[Path]) -> list[metadata.Distribution]:
    pending = sorted(
        {name for path in requirements for name in read_requirement_names(path)},
        key=str.casefold,
    )
    collected: dict[str, metadata.Distribution] = {}
    while pending:
        name = pending.pop(0)
        key = name.casefold().replace("_", "-")
        if key in collected:
            continue
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError as exc:
            raise RuntimeError(f"Python dependency is not installed: {name}") from exc
        collected[key] = dist
        for raw_requirement in dist.requires or []:
            requirement = Requirement(raw_requirement)
            if requirement.marker is None or requirement.marker.evaluate():
                pending.append(requirement.name)
    return sorted(collected.values(), key=lambda dist: dist.metadata["Name"].casefold())


def npm_license_values(raw_value: object) -> list[str]:
    if isinstance(raw_value, str):
        return [raw_value]
    if isinstance(raw_value, dict):
        value = raw_value.get("type") or raw_value.get("name")
        return [value] if isinstance(value, str) else []
    if isinstance(raw_value, list):
        values: list[str] = []
        for item in raw_value:
            values.extend(npm_license_values(item))
        return values
    return []


def collect_npm_packages(frontend_root: Path) -> list[tuple[str, str, list[str]]]:
    node_modules = frontend_root / "node_modules"
    if not node_modules.is_dir():
        raise RuntimeError(f"Node dependencies are not installed: {node_modules}")

    packages: list[tuple[str, str, list[str]]] = []
    for directory, _, files in os.walk(node_modules):
        if "package.json" not in files:
            continue
        package_file = Path(directory) / "package.json"
        try:
            package = json.loads(package_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Cannot read {package_file}: {exc}") from exc
        name = package.get("name")
        if not isinstance(name, str):
            continue
        version = package.get("version", "unknown")
        values = npm_license_values(package.get("license"))
        if not values:
            values = npm_license_values(package.get("licenses"))
        packages.append((name, str(version), values))
    return sorted(packages, key=lambda item: (item[0].casefold(), item[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend-root", type=Path, default=Path("frontend"))
    parser.add_argument(
        "--python-requirement",
        action="append",
        dest="python_requirements",
        type=Path,
        default=[Path("requirements-dev.txt")],
    )
    args = parser.parse_args()

    try:
        python_distributions = collect_python_distributions(args.python_requirements)
        npm_packages = collect_npm_packages(args.frontend_root)
    except RuntimeError as exc:
        print(f"[license-check] error: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for dist in python_distributions:
        name = dist.metadata["Name"]
        versions = python_license(dist)
        if not versions or not all(allowed_license(value) for value in versions):
            display = ", ".join(versions) if versions else "unknown"
            failures.append(f"python {name}=={dist.version}: {display}")

    for name, version, values in npm_packages:
        if not values or not all(allowed_license(value) for value in values):
            display = ", ".join(values) if values else "unknown"
            failures.append(f"npm {name}@{version}: {display}")

    print(
        f"[license-check] inspected {len(python_distributions)} Python and "
        f"{len(npm_packages)} npm package(s)"
    )
    if failures:
        print("[license-check] unknown or disallowed licenses:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print("[license-check] passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
