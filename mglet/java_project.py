from __future__ import annotations

import os
import shutil
from pathlib import Path

from .command import CommandError, run_command
from .config import as_list


def ensure_maven_project(project_dir: Path) -> None:
    if not (project_dir / "pom.xml").exists():
        raise FileNotFoundError(f"No pom.xml found in Maven project: {project_dir}")


def class_to_source_path(project_dir: Path, class_name: str) -> Path:
    return project_dir / "src" / "main" / "java" / Path(*class_name.split(".")).with_suffix(".java")


def class_to_test_path(project_dir: Path, class_name: str, suffix: str = "LLMEnhancedTest") -> Path:
    parts = class_name.split(".")
    simple = parts[-1]
    package_parts = parts[:-1]
    return (
        project_dir
        / "src"
        / "test"
        / "java"
        / Path(*package_parts)
        / f"{simple}{suffix}.java"
    )


def read_target_source(project_dir: Path, class_name: str) -> str:
    source_path = class_to_source_path(project_dir, class_name)
    if not source_path.exists():
        raise FileNotFoundError(f"Target source not found: {source_path}")
    return source_path.read_text(encoding="utf-8", errors="replace")


def find_test_files(project_dir: Path) -> list[Path]:
    test_root = project_dir / "src" / "test" / "java"
    if not test_root.exists():
        return []
    return sorted(
        p
        for p in test_root.rglob("*.java")
        if p.name.endswith(("Test.java", "Tests.java", "ESTest.java"))
    )


def find_evosuite_tests(project_dir: Path, evosuite_dir: str) -> list[Path]:
    root = project_dir / evosuite_dir
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.java") if p.name.endswith(".java"))


def export_evosuite_tests(project_dir: Path, evosuite_dir: str) -> list[Path]:
    copied: list[Path] = []
    for source in find_evosuite_tests(project_dir, evosuite_dir):
        rel = source.relative_to(project_dir / evosuite_dir)
        destination = project_dir / "src" / "test" / "java" / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(destination)
    return copied


def build_maven_classpath(
    project_dir: Path,
    maven_executable: str,
    timeout_seconds: int,
    output_file: Path,
) -> str:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result = run_command(
        [
            maven_executable,
            "-q",
            "dependency:build-classpath",
            f"-Dmdep.outputFile={output_file}",
        ],
        cwd=project_dir,
        timeout_seconds=timeout_seconds,
    )
    if not result.ok:
        raise CommandError("Failed to build Maven dependency classpath", result)

    entries = [
        project_dir / "target" / "classes",
        project_dir / "target" / "test-classes",
    ]
    if output_file.exists():
        dependency_cp = output_file.read_text(encoding="utf-8", errors="replace").strip()
        if dependency_cp:
            entries.extend(Path(item) for item in dependency_cp.split(os.pathsep) if item)
    return os.pathsep.join(str(entry) for entry in entries)


def run_maven_goal(
    project_dir: Path,
    maven_config: dict,
    goal_key: str,
):
    args = [maven_config.get("executable", "mvn"), *as_list(maven_config.get(goal_key))]
    return run_command(
        args,
        cwd=project_dir,
        timeout_seconds=int(maven_config.get("timeout_seconds", 900)),
    )
