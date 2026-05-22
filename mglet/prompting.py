from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .java_project import class_to_source_path, find_test_files, read_target_source
from .models import CoverageReport, PitReport
from .pitest import mutation_type_guidance, summarize_survived_mutants


def trim_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n\n/* ... trimmed for prompt budget ... */\n\n" + tail


def collect_test_context(project_dir: Path, max_chars: int) -> str:
    chunks: list[str] = []
    for path in find_test_files(project_dir):
        rel = path.relative_to(project_dir)
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks.append(f"// file: {rel.as_posix()}\n{text}")
    return trim_text("\n\n".join(chunks), max_chars)


def collect_related_source_context(project_dir: Path, target_class: str, max_chars: int) -> str:
    target_path = class_to_source_path(project_dir, target_class)
    source_root = project_dir / "src" / "main" / "java"
    package_dir = target_path.parent
    chunks: list[str] = []
    if package_dir.exists() and source_root.exists():
        for path in sorted(package_dir.glob("*.java")):
            rel = path.relative_to(project_dir)
            text = path.read_text(encoding="utf-8", errors="replace")
            chunks.append(f"// file: {rel.as_posix()}\n{text}")
    if not chunks:
        chunks.append(read_target_source(project_dir, target_class))
    return trim_text("\n\n".join(chunks), max_chars)


def heuristic_business_rules(source_context: str) -> str:
    rules: list[str] = []
    rule_patterns = [
        ("VIP customers can receive special tier discounts or shipping treatment.", ["VIP", "isVip"]),
        ("Expired coupons must be rejected and must not reduce the order total.", ["EXPIRED", "expiresOn", "today.isAfter"]),
        ("First-order-only coupons apply only when the customer is placing the first order.", ["FIRST_ORDER_ONLY", "firstOrderOnly"]),
        ("High percentage coupons require VIP status.", ["HIGH_PERCENT_REQUIRES_VIP"]),
        ("Digital-only orders should not pay shipping.", ["allItemsDigital", "isDigital"]),
        ("Discounts are capped and should never exceed the configured subtotal limit.", ["capDiscount", "0.70"]),
        ("US and EU regions use different tax rates.", ["0.07", "0.20"]),
        ("Non-stackable coupons should replace tier discount only when they are better.", ["TIER_DISCOUNT_REPLACED", "COUPON_NOT_BETTER_THAN_TIER"]),
        ("Fixed coupons cannot discount more than the subtotal.", ["min(subtotal)", "FIXED"]),
        ("Free-shipping coupons should remove shipping without changing item subtotal.", ["FREE_SHIPPING"]),
    ]
    for rule, needles in rule_patterns:
        if any(needle in source_context for needle in needles):
            rules.append(f"- {rule}")
    return "\n".join(rules) if rules else "- No obvious domain rules were extracted heuristically."


def build_rule_extraction_messages(
    project_dir: Path,
    target_class: str,
    prompt_config: dict[str, Any],
) -> list[dict[str, str]]:
    source_context = collect_related_source_context(
        project_dir,
        target_class,
        int(prompt_config.get("max_rule_source_chars", 18000)),
    )
    system = (
        "You extract business rules from Java source for test-oracle generation. "
        "Do not write tests. Return concise markdown bullets only."
    )
    user = f"""Target class: {target_class}

Related production source:
```java
{source_context}
```

Extract 8-15 business rules that should become semantic test assertions.
Focus on monetary values, thresholds, eligibility rules, exception rules, and branch decisions.
Use this format only:
- Rule: ...
  Oracle: ...
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_enhancement_messages(
    project_dir: Path,
    target_class: str,
    pit_report: PitReport,
    coverage_report: CoverageReport,
    prompt_config: dict[str, Any],
    business_rules: str = "",
) -> list[dict[str, str]]:
    source = collect_related_source_context(
        project_dir,
        target_class,
        int(prompt_config.get("max_related_source_chars", prompt_config.get("max_source_chars", 12000))),
    )
    tests = collect_test_context(project_dir, int(prompt_config.get("max_test_chars", 14000)))
    mutants = summarize_survived_mutants(
        pit_report,
        limit=int(prompt_config.get("max_mutants", 20)),
    )
    mutant_guidance = mutation_type_guidance(
        pit_report,
        target_class=target_class,
        limit=int(prompt_config.get("max_mutants", 20)),
    )
    coverage = json.dumps(coverage_report.to_dict(), ensure_ascii=False, indent=2)
    fallback_name = target_class.split(".")[-1] + "LLMEnhancedTest.java"
    related_source = collect_related_source_context(
        project_dir,
        target_class,
        int(prompt_config.get("max_related_source_chars", 18000)),
    )
    heuristic_rules = heuristic_business_rules(related_source)
    rule_context = business_rules.strip() if business_rules.strip() else heuristic_rules

    system = (
        "You are a senior Java testing engineer. Improve JUnit tests without "
        "changing production code. Prefer strong semantic assertions, exact "
        "monetary oracles, boundary cases, and mutation-killing inputs. "
        "Use only constructors, methods, and enum constants that are present in the supplied source. "
        "Return only Java code blocks."
    )
    user = f"""Target class: {target_class}

Production source:
```java
{source}
```

Existing generated tests:
```java
{tests}
```

JaCoCo coverage summary:
```json
{coverage}
```

Business rules to turn into semantic oracles:
{rule_context}

Survived or uncovered PIT mutants:
{mutants}

{mutant_guidance}

Task:
1. Add or improve tests that kill the highest-value survived mutants and strengthen assertions.
2. Use the business rules above as oracle guidance; assert exact CheckoutResult fields, rejection reasons, and BigDecimal values where possible.
3. Use mutation-type guidance: boundary mutants need threshold tests, math mutants need exact amount assertions, return mutants need direct boolean/string/result assertions.
4. Prefer descriptive test method names over generated names like test00.
5. Keep tests deterministic and readable.
6. Use the same test framework already visible in the existing tests when possible.
7. Do not depend on network, time, locale, file-system state, or random values.
8. Do not modify production source.
9. Keep the output concise: one test class, at most 6 focused test methods, under 220 lines total.
10. Do not duplicate existing EvoSuite tests unless the new assertion is semantically stronger.

Output format:
Return one or more fenced Java code blocks. Each block must start with:
// path: src/test/java/.../{fallback_name}
Always close every fenced code block with ```

If no improvement is possible, return exactly: NO_CHANGE
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_repair_messages(
    project_dir: Path,
    target_class: str,
    failing_output: str,
    generated_files: list[Path],
    prompt_config: dict[str, Any],
) -> list[dict[str, str]]:
    source = collect_related_source_context(
        project_dir,
        target_class,
        int(prompt_config.get("max_related_source_chars", prompt_config.get("max_source_chars", 12000))),
    )
    tests = []
    for path in generated_files:
        if path.exists():
            rel = path.relative_to(project_dir)
            tests.append(f"// file: {rel.as_posix()}\n{path.read_text(encoding='utf-8', errors='replace')}")
    test_context = trim_text("\n\n".join(tests), int(prompt_config.get("max_test_chars", 14000)))
    output = trim_text(failing_output, 12000)
    system = (
        "You repair Java unit tests. Fix only test code, preserve the intended "
        "assertions, use only APIs and enum constants present in the supplied source, "
        "and return complete Java files in fenced code blocks."
    )
    user = f"""Target class: {target_class}

Production source:
```java
{source}
```

Generated test files to repair:
```java
{test_context}
```

Maven compiler/test output:
```text
{output}
```

Return complete fixed Java files. Each block must start with // path: <relative path>.
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
