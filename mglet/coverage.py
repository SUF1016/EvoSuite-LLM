from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import CoverageCounter, CoverageReport


def jacoco_xml_path(project_dir: Path) -> Path | None:
    candidates = [
        project_dir / "target" / "site" / "jacoco" / "jacoco.xml",
        project_dir / "target" / "site" / "jacoco-it" / "jacoco.xml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    found = sorted(
        (project_dir / "target").rglob("jacoco.xml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ) if (project_dir / "target").exists() else []
    return found[0] if found else None


def parse_jacoco_xml(path: Path | None) -> CoverageReport:
    if path is None or not path.exists():
        return CoverageReport(path=None)
    root = ET.parse(path).getroot()
    counters: dict[str, CoverageCounter] = {}
    for counter in root.findall("counter"):
        kind = counter.attrib.get("type", "").upper()
        if not kind:
            continue
        counters[kind] = CoverageCounter(
            missed=int(counter.attrib.get("missed", "0")),
            covered=int(counter.attrib.get("covered", "0")),
        )
    return CoverageReport(path=path, counters=counters)
