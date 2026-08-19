#!/usr/bin/env python3
"""Collect deterministic NGC root-project evidence without modifying the repository.

The helper intentionally limits itself to facts that can be checked reliably. Its findings are
review inputs, not automatic authorization to rewrite project configuration. Docker checks assume
the NGC CI build context is the repository root and do not emulate `.dockerignore` matching;
workspace members are not expanded.
"""

import argparse
import json
import re
import shlex
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

IGNORED_SCAN_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "htmlcov",
    "node_modules",
}
RUNTIME_ASSET_DIRS = ("consts", "migrations", "static", "templates")
DOC_POLICY_FILES = ("AGENTS.md", "CLAUDE.md", "CONSTITUTION.md", "README.md")


@dataclass(frozen=True)
class Finding:
    """A deterministic repository-audit finding."""

    severity: str
    code: str
    message: str
    paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        result = asdict(self)
        result["paths"] = list(self.paths)
        return result


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_scannable(path: Path) -> bool:
    return not any(part in IGNORED_SCAN_PARTS for part in path.parts)


def _load_pyproject(root: Path, findings: list[Finding]) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.exists():
        findings.append(
            Finding("warning", "missing-pyproject", "pyproject.toml was not found."),
        )
        return {}
    try:
        with path.open("rb") as file_handle:
            loaded = tomllib.load(file_handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        findings.append(
            Finding(
                "error",
                "invalid-pyproject",
                f"Unable to parse pyproject.toml: {exc}",
                ("pyproject.toml",),
            ),
        )
        return {}
    return loaded


def _dependency_names(pyproject: dict[str, Any]) -> set[str]:
    raw: list[str] = []
    project = pyproject.get("project", {})
    if isinstance(project, dict):
        dependencies = project.get("dependencies", [])
        if isinstance(dependencies, list):
            raw.extend(str(item) for item in dependencies)
    groups = pyproject.get("dependency-groups", {})
    if isinstance(groups, dict):
        for values in groups.values():
            if isinstance(values, list):
                raw.extend(str(item) for item in values)

    names: set[str] = set()
    for specification in raw:
        match = re.match(r"\s*([A-Za-z0-9_.-]+)", specification)
        if match:
            names.add(match.group(1).lower().replace("_", "-"))
    return names


def _find_dockerfiles(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or not _is_scannable(path.relative_to(root)):
            continue
        if path.name == "Dockerfile" or path.name.endswith(".Dockerfile"):
            paths.append(path)
    return sorted(paths)


def _find_compose_files(root: Path) -> list[Path]:
    names = (
        "compose*.yml",
        "compose*.yaml",
        "docker-compose*.yml",
        "docker-compose*.yaml",
    )
    found: set[Path] = set()
    for pattern in names:
        for path in root.rglob(pattern):
            if path.is_file() and _is_scannable(path.relative_to(root)):
                found.add(path)
    return sorted(found)


def _audit_compose(
    root: Path,
    compose_files: list[Path],
    findings: list[Finding],
) -> dict[str, list[str]]:
    image_map: dict[str, list[str]] = {}
    for path in compose_files:
        relative_path = _relative(path, root)
        text = _read_text(path)
        images = [
            match.group(1).strip().strip("\"'")
            for match in re.finditer(r"(?m)^\s+image:\s*([^#\r\n]+)", text)
        ]
        image_map[relative_path] = images

        if re.search(r"(?m)^\s+build:\s*(?:\S.*)?$", text):
            findings.append(
                Finding(
                    "warning",
                    "compose-build-present",
                    f"{relative_path} contains 'build'; verify that it is development-only.",
                    (relative_path,),
                ),
            )
        if re.search(r"(?m)^\s+pull_policy:\s*[\"']?always[\"']?\s*(?:#.*)?$", text):
            findings.append(
                Finding(
                    "warning",
                    "compose-pull-always",
                    f"{relative_path} forces pull_policy: always; review image selection policy.",
                    (relative_path,),
                ),
            )
        latest_images = tuple(image for image in images if re.search(r":latest(?:[}\s]|$)", image))
        if latest_images:
            findings.append(
                Finding(
                    "warning",
                    "mutable-compose-image",
                    f"{relative_path} contains a mutable ':latest' image or fallback.",
                    (relative_path,),
                ),
            )
    return image_map


def _docker_instructions(text: str) -> list[str]:
    instructions: list[str] = []
    current = ""
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or (not current and stripped.startswith("#")):
            continue
        current = f"{current} {stripped}".strip()
        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue
        instructions.append(current)
        current = ""
    if current:
        instructions.append(current)
    return instructions


def _copy_add_sources(instruction: str) -> set[str]:
    match = re.match(r"^(COPY|ADD)\s+(.+)$", instruction, flags=re.IGNORECASE)
    if not match:
        return set()

    remainder = match.group(2).strip()
    if re.search(r"(?:^|\s)--from(?:=|\s)", remainder):
        return set()

    while remainder.startswith("--"):
        flag_match = re.match(r"--[^\s]+\s+", remainder)
        if not flag_match:
            break
        remainder = remainder[flag_match.end() :]

    try:
        if remainder.startswith("["):
            tokens = [str(value) for value in json.loads(remainder)]
        else:
            tokens = shlex.split(remainder, posix=True)
    except ValueError:
        return set()

    return {
        token.replace("\\", "/")
        for token in tokens[:-1]
        if not re.match(r"^[a-z]+://", token, flags=re.IGNORECASE)
    }


def _docker_sources(text: str) -> set[str]:
    sources: set[str] = set()
    for instruction in _docker_instructions(text):
        sources.update(_copy_add_sources(instruction))

        bind_sources = re.findall(
            r"--mount=type=bind,[^\s]*?source=([^,\s]+)",
            instruction,
            flags=re.IGNORECASE,
        )
        sources.update(source.strip("\"'").replace("\\", "/") for source in bind_sources)
    return sources


def _audit_docker(
    root: Path,
    dockerfiles: list[Path],
    findings: list[Finding],
) -> dict[str, list[str]]:
    source_map: dict[str, list[str]] = {}
    for dockerfile in dockerfiles:
        relative_dockerfile = _relative(dockerfile, root)
        sources = _docker_sources(_read_text(dockerfile))
        source_map[relative_dockerfile] = sorted(sources)

        copies_everything = any(source in {".", "./"} for source in sources)
        for directory in RUNTIME_ASSET_DIRS:
            if not (root / directory).is_dir() or copies_everything:
                continue
            copied = any(
                source.strip("./").strip("/") == directory
                or source.strip("./").strip("/").startswith(f"{directory}/")
                for source in sources
            )
            if not copied:
                findings.append(
                    Finding(
                        "warning",
                        "uncopied-runtime-assets",
                        f"Top-level '{directory}/' exists but is not an explicit source in {relative_dockerfile}.",
                        (relative_dockerfile, directory),
                    ),
                )
    return source_map


def _audit_backend(pyproject: dict[str, Any], findings: list[Finding]) -> str | None:
    build_system = pyproject.get("build-system", {})
    backend = build_system.get("build-backend") if isinstance(build_system, dict) else None
    tool = pyproject.get("tool", {})
    if not isinstance(tool, dict) or not isinstance(backend, str):
        return backend if isinstance(backend, str) else None

    backend_lower = backend.lower()
    possible_mismatches = {
        "setuptools": "setuptools",
        "hatch": "hatchling",
        "poetry": "poetry",
        "pdm": "pdm",
    }
    for table, owner in possible_mismatches.items():
        if table in tool and owner not in backend_lower:
            findings.append(
                Finding(
                    "warning",
                    "inactive-backend-config",
                    f"[tool.{table}] is present while the active build backend is '{backend}'. Review whether the table is stale.",
                    ("pyproject.toml",),
                ),
            )
    return backend


def _pyproject_coverage_thresholds(
    pyproject: dict[str, Any],
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    tool = pyproject.get("tool", {})
    if not isinstance(tool, dict):
        return values

    coverage = tool.get("coverage", {})
    report = coverage.get("report", {}) if isinstance(coverage, dict) else {}
    fail_under = report.get("fail_under") if isinstance(report, dict) else None
    if isinstance(fail_under, (int, float)):
        values.append(
            {
                "source": "pyproject.toml:[tool.coverage.report]",
                "value": float(fail_under),
            },
        )

    pytest = tool.get("pytest", {})
    ini_options = pytest.get("ini_options", {}) if isinstance(pytest, dict) else {}
    addopts = ini_options.get("addopts", "") if isinstance(ini_options, dict) else ""
    matches = re.finditer(
        r"--cov-fail-under(?:=|\s+)(\d+(?:\.\d+)?)",
        str(addopts),
    )
    values.extend(
        {
            "source": "pyproject.toml:[tool.pytest.ini_options]",
            "value": float(match.group(1)),
        }
        for match in matches
    )
    return values


def _workflow_coverage_thresholds(root: Path) -> list[dict[str, Any]]:
    workflow_root = root / ".github" / "workflows"
    if not workflow_root.is_dir():
        return []

    return [
        {"source": _relative(path, root), "value": float(match.group(1))}
        for path in sorted(workflow_root.glob("*.y*ml"))
        for match in re.finditer(
            r"--cov-fail-under(?:=|\s+)(\d+(?:\.\d+)?)",
            _read_text(path),
        )
    ]


def _documented_coverage_thresholds(root: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    patterns = (
        re.compile(r"(?i)(\d{1,3}(?:\.\d+)?)\s*%\s*(?:line\s+)?coverage"),
        re.compile(r"(?i)coverage.{0,40}?(\d{1,3}(?:\.\d+)?)\s*%"),
    )
    for filename in DOC_POLICY_FILES:
        path = root / filename
        if not path.exists():
            continue
        text = _read_text(path)
        matches = {
            float(match.group(1)) for pattern in patterns for match in pattern.finditer(text)
        }
        values.extend({"source": filename, "value": value} for value in sorted(matches))
    return values


def _coverage_thresholds(root: Path, pyproject: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *_pyproject_coverage_thresholds(pyproject),
        *_workflow_coverage_thresholds(root),
        *_documented_coverage_thresholds(root),
    ]


def _runtime_entrypoints(root: Path, pyproject: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"project_scripts": [], "python_modules": []}
    project = pyproject.get("project", {})
    scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
    if isinstance(scripts, dict):
        result["project_scripts"] = sorted(str(key) for key in scripts)

    source_root = root / "src"
    if source_root.is_dir():
        for path in source_root.rglob("*.py"):
            if not _is_scannable(path.relative_to(root)):
                continue
            text = _read_text(path)
            if 'if __name__ == "__main__"' in text or "if __name__ == '__main__'" in text:
                result["python_modules"].append(_relative(path, root))
    result["python_modules"].sort()
    return result


def _structured_logging_evidence(root: Path, dependencies: set[str]) -> list[str]:
    evidence: set[str] = set()
    if dependencies & {"python-json-logger", "structlog"}:
        evidence.add("pyproject.toml")

    source_root = root / "src"
    if not source_root.is_dir():
        return sorted(evidence)
    patterns = (
        re.compile(r"class\s+\w*Json\w*Formatter\s*\([^)]*logging\.Formatter"),
        re.compile(r"\bstructlog\.configure\s*\("),
        re.compile(r"\b(?:from|import)\s+pythonjsonlogger\b"),
    )
    for path in source_root.rglob("*.py"):
        if not _is_scannable(path.relative_to(root)):
            continue
        text = _read_text(path)
        if any(pattern.search(text) for pattern in patterns):
            evidence.add(_relative(path, root))
    return sorted(evidence)


def _profile(
    root: Path,
    pyproject: dict[str, Any],
    dockerfiles: list[Path],
    compose_files: list[Path],
) -> dict[str, Any]:
    tool = pyproject.get("tool", {})
    uv = tool.get("uv", {}) if isinstance(tool, dict) else {}
    workspace = isinstance(uv, dict) and isinstance(uv.get("workspace"), dict)
    package_setting = uv.get("package") if isinstance(uv, dict) else None
    build_system = pyproject.get("build-system")
    if package_setting is False:
        packaging = "non-package"
    elif isinstance(build_system, dict):
        packaging = "installable"
    else:
        packaging = "undetermined"

    dependencies = _dependency_names(pyproject)
    examples = sorted(
        _relative(path, root)
        for path in root.rglob("*")
        if path.is_file()
        and _is_scannable(path.relative_to(root))
        and (path.name == ".env.example" or path.name.endswith(".example.toml"))
    )
    logging_evidence = _structured_logging_evidence(root, dependencies)
    checks = {
        "configuration": bool(examples) or "pydantic-settings" in dependencies,
        "tests": (root / "tests").is_dir() or "pytest" in dependencies,
        "formatting": (root / "package.json").exists() or any(root.glob(".prettierrc*")),
        "fastapi": "fastapi" in dependencies,
        "httpx2": "httpx2" in dependencies,
        "containers": bool(dockerfiles),
        "compose": bool(compose_files),
        "structured_logging": bool(logging_evidence),
        "stateful": any((root / name).exists() for name in ("data", "migrations"))
        or bool({"alembic", "sqlalchemy"} & dependencies),
        "private_ci": (root / ".github" / "workflows").is_dir(),
    }
    capabilities = [name for name, selected in checks.items() if selected]
    role_candidates = (
        ["service"] if checks["containers"] or checks["fastapi"] else ["service", "library"]
    )
    return {
        "repository": str(root),
        "repository_shape": "workspace" if workspace else "single-project",
        "profile_scope": "workspace-root" if workspace else "project",
        "project_role_candidates": role_candidates,
        "packaging": packaging,
        "capabilities": capabilities,
        "docker_build_context": ".",
        "dockerfiles": [_relative(path, root) for path in dockerfiles],
        "compose_files": [_relative(path, root) for path in compose_files],
        "configuration_examples": examples,
        "structured_logging_evidence": logging_evidence,
        "runtime_entrypoints": _runtime_entrypoints(root, pyproject),
    }


def audit(root: Path) -> dict[str, Any]:
    """Collect root-level repository evidence and findings."""
    findings: list[Finding] = []
    pyproject = _load_pyproject(root, findings)
    dockerfiles = _find_dockerfiles(root)
    compose_files = _find_compose_files(root)
    profile = _profile(root, pyproject, dockerfiles, compose_files)
    if profile["repository_shape"] == "workspace":
        findings.append(
            Finding(
                "info",
                "workspace-root-only",
                "Profile evidence covers the workspace root only; inspect affected members separately.",
                ("pyproject.toml",),
            ),
        )
    profile["build_backend"] = _audit_backend(pyproject, findings)
    profile["docker_sources"] = _audit_docker(root, dockerfiles, findings)
    profile["compose_images"] = _audit_compose(root, compose_files, findings)
    thresholds = _coverage_thresholds(root, pyproject)
    profile["coverage_thresholds"] = thresholds

    if len({item["value"] for item in thresholds}) > 1:
        sources = tuple(str(item["source"]) for item in thresholds)
        rendered = ", ".join(f"{item['source']}={item['value']:g}" for item in thresholds)
        findings.append(
            Finding(
                "warning",
                "coverage-policy-drift",
                f"Coverage thresholds disagree: {rendered}",
                sources,
            ),
        )

    severity_order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(
        key=lambda item: (severity_order.get(item.severity, 99), item.code, item.paths),
    )
    return {"profile": profile, "findings": [finding.to_dict() for finding in findings]}


def _print_text(result: dict[str, Any]) -> None:
    profile = result["profile"]
    print("NGC PROFILE EVIDENCE")
    print(f"repository: {profile['repository']}")
    print(f"repository shape: {profile['repository_shape']}")
    print(f"profile scope: {profile['profile_scope']}")
    print(f"project role candidates: {', '.join(profile['project_role_candidates'])}")
    print(f"packaging: {profile['packaging']}")
    print(f"build backend: {profile['build_backend'] or 'none'}")
    print(f"capabilities: {', '.join(profile['capabilities']) or 'none detected'}")
    print(
        f"runtime entry points: {json.dumps(profile['runtime_entrypoints'], ensure_ascii=False)}",
    )
    print(
        f"configuration examples: {', '.join(profile['configuration_examples']) or 'none'}",
    )
    print(
        "structured logging evidence: "
        f"{', '.join(profile['structured_logging_evidence']) or 'none'}",
    )
    print(
        f"compose images: {json.dumps(profile['compose_images'], ensure_ascii=False)}",
    )
    print(f"assumed Docker build context: {profile['docker_build_context']}")
    print()
    print("DETERMINISTIC FINDINGS")
    findings = result["findings"]
    if not findings:
        print("none")
        return
    for finding in findings:
        paths = f" ({', '.join(finding['paths'])})" if finding["paths"] else ""
        print(
            f"[{finding['severity'].upper()}] {finding['code']}: {finding['message']}{paths}",
        )


def main() -> int:
    """Run the command-line audit and return its exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".", type=Path)
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit JSON output.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return nonzero for warnings as well as errors.",
    )
    args = parser.parse_args()
    root = args.repository.resolve()
    if not root.is_dir():
        parser.error(f"repository is not a directory: {root}")

    result = audit(root)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text(result)

    severities = {finding["severity"] for finding in result["findings"]}
    if "error" in severities or (args.strict and "warning" in severities):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
