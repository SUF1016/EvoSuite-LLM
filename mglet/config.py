from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "project_dir": "examples/java-target",
    "output_dir": "runs/default",
    "targets": [],
    "iterations": 1,
    "repair_attempts": 2,
    "flaky_runs": 1,
    "maven": {
        "executable": "mvn",
        "compile_goal": ["-q", "-DskipTests", "test-compile"],
        "test_goal": ["-q", "test"],
        "jacoco_goal": ["-q", "jacoco:prepare-agent", "test", "jacoco:report"],
        "pit_goal": ["-q", "org.pitest:pitest-maven:mutationCoverage"],
        "timeout_seconds": 900,
    },
    "java": {
        "executable": "java",
    },
    "evosuite": {
        "jar": "tools/evosuite-1.2.0.jar",
        "test_dir": "evosuite-tests",
        "report_dir": "evosuite-report",
        "search_budget_seconds": 60,
        "extra_args": [],
        "export_to_test_tree": True,
    },
    "llm": {
        "provider": "openai-compatible",
        "model": "${OPENAI_MODEL:gpt-4.1-mini}",
        "base_url": "${OPENAI_BASE_URL:https://api.openai.com/v1}",
        "api_key": "${OPENAI_API_KEY:}",
        "temperature": 0.2,
        "timeout_seconds": 120,
        "dry_run": False,
        "response_file": "",
    },
    "prompt": {
        "max_source_chars": 12000,
        "max_test_chars": 14000,
        "max_mutants": 20,
    },
}


def deep_update(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_update(merged[key], value)
        else:
            merged[key] = value
    return merged


def expand_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env(v) for v in value]
    if not isinstance(value, str):
        return value

    result = value
    start = result.find("${")
    while start != -1:
        end = result.find("}", start)
        if end == -1:
            break
        token = result[start + 2 : end]
        if ":" in token:
            name, default = token.split(":", 1)
        else:
            name, default = token, ""
        replacement = os.environ.get(name, default)
        result = result[:start] + replacement + result[end + 1 :]
        start = result.find("${", start + len(replacement))
    return result


def load_config(path: str | Path | None) -> dict[str, Any]:
    cfg = DEFAULT_CONFIG
    if path:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        user_config = json.loads(config_path.read_text(encoding="utf-8"))
        cfg = deep_update(cfg, user_config)
    return expand_env(cfg)


def resolve_config_path(value: str | Path, config_path: str | Path | None = None) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        return raw
    if config_path:
        base = Path(config_path).absolute().parent
        candidates = [(Path.cwd() / raw).absolute(), (base / raw).absolute(), (base.parent / raw).absolute()]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        if base.name.lower() == "configs":
            return (base.parent / raw).absolute()
    return raw.absolute()


def resolve_project_dir(config: dict[str, Any], config_path: str | Path | None = None) -> Path:
    return resolve_config_path(config["project_dir"], config_path)


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
