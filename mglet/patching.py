from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


JAVA_BLOCK_RE = re.compile(r"```(?:java)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
PATH_RE = re.compile(r"^\s*//\s*(?:path|file)\s*:\s*(\S+)\s*$", re.MULTILINE)


@dataclass
class GeneratedFile:
    relative_path: Path
    content: str


def extract_java_files(response: str, fallback_relative_path: Path | None = None) -> list[GeneratedFile]:
    if response.strip() == "NO_CHANGE":
        return []

    blocks = JAVA_BLOCK_RE.findall(response)
    if not blocks and response.lstrip().startswith("package ") and fallback_relative_path:
        blocks = [response]

    files: list[GeneratedFile] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        path_match = PATH_RE.search(block)
        if path_match:
            raw_path = path_match.group(1).replace("\\", "/")
            candidate = Path(raw_path)
            rel_path = candidate if candidate.is_absolute() else Path(*[p for p in raw_path.split("/") if p and p != "."])
            content = PATH_RE.sub("", block, count=1).lstrip()
        elif fallback_relative_path is not None:
            rel_path = fallback_relative_path
            content = block
        else:
            continue
        if rel_path.suffix != ".java":
            continue
        files.append(GeneratedFile(relative_path=rel_path, content=content.rstrip() + "\n"))
    return files


def write_generated_files(project_dir: Path, files: list[GeneratedFile]) -> list[Path]:
    written: list[Path] = []
    project_root = project_dir.absolute()
    for generated in files:
        destination = (project_root / generated.relative_path).absolute()
        if project_root not in destination.parents and destination != project_root:
            raise ValueError(f"Generated file escapes project directory: {generated.relative_path}")
        if destination.suffix != ".java":
            raise ValueError(f"Generated file is not a Java source file: {generated.relative_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(generated.content, encoding="utf-8", newline="\n")
        written.append(destination)
    return written
