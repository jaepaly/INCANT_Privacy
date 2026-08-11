#!/usr/bin/env python3
"""rules/*.yaml -> rules/CATALOG.md 생성기.

카탈로그를 손으로 쓰면 원본 YAML과 조용히 어긋난다. 룰은 YAML에만 두고
사람이 읽는 문서는 항상 여기서 생성한다.

    python tools/render_rules.py          생성
    python tools/render_rules.py --check  검증만 (CI용, 위반 시 exit 1)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
OUT = RULES_DIR / "CATALOG.md"

SOURCES = ["kr.yaml", "eu.yaml"]

# rules/README.md 의 영역 표와 같은 순서로 묶는다.
DOMAIN_ORDER = ["투명성", "국외이전", "보유·파기", "정보주체 권리", "특별범주", "아동"]

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
VERIFICATIONS = ["확인필요", "확인완료"]

REQUIRED = [
    "id", "domain", "title", "summary", "legal_basis", "condition_human",
    "check_expr", "severity_base", "severity_rationale", "applies_to",
    "remediation", "evidence", "related",
]
REQUIRED_BASIS = ["law", "article", "note", "verification"]


def load() -> tuple[dict, list[dict]]:
    metas, rules = {}, []
    for name in SOURCES:
        path = RULES_DIR / name
        if not path.exists():
            fail(f"원본 없음: {path}")
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        jur = doc["meta"]["jurisdiction"]
        metas[jur] = doc["meta"]
        for rule in doc["rules"]:
            rule["_jurisdiction"] = jur
            rule["_source"] = name
            rules.append(rule)
    return metas, rules


def validate(rules: list[dict]) -> list[str]:
    errors: list[str] = []
    ids = {r.get("id") for r in rules}

    for rule in rules:
        rid = rule.get("id", "<id 없음>")
        where = f"{rule['_source']} :: {rid}"

        for field in REQUIRED:
            if not rule.get(field):
                errors.append(f"{where}: 필수 필드 누락 — {field}")

        parts = str(rid).split("-")
        if len(parts) != 3 or parts[0] not in ("KR", "EU") \
                or len(parts[1]) != 3 or not parts[1].isupper() \
                or len(parts[2]) != 3 or not parts[2].isdigit():
            errors.append(f"{where}: ID 형식 위반 — {{KR|EU}}-{{3자 대문자}}-{{3자리 숫자}}")
        elif parts[0] != rule["_jurisdiction"]:
            errors.append(f"{where}: ID 관할과 파일 관할 불일치")

        if rule.get("severity_base") not in SEVERITIES:
            errors.append(f"{where}: severity_base 값 오류 — {SEVERITIES}")

        for basis in rule.get("legal_basis") or []:
            for field in REQUIRED_BASIS:
                if not basis.get(field):
                    errors.append(f"{where}: legal_basis 필드 누락 — {field}")
            verification = basis.get("verification")
            if verification not in VERIFICATIONS:
                errors.append(f"{where}: verification 값 오류 — {VERIFICATIONS}")
            elif verification == "확인완료" and not (basis.get("checked_at") and basis.get("source")):
                errors.append(f"{where}: '확인완료'는 checked_at·source 필수 — {basis.get('article')}")

        for ref in rule.get("related") or []:
            if ref not in ids:
                errors.append(f"{where}: related 참조 대상 없음 — {ref}")

    return errors


def basis_line(rule: dict) -> str:
    return " · ".join(f"{b['law']} {b['article']}" for b in rule["legal_basis"])


def verify_mark(rule: dict) -> str:
    pending = sum(1 for b in rule["legal_basis"] if b["verification"] == "확인필요")
    total = len(rule["legal_basis"])
    return "확인완료" if pending == 0 else f"확인필요 {pending}/{total}"


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def rule_key(rule: dict) -> tuple[int, str]:
    """같은 영역 안에서는 국내 룰을 먼저 놓는다 — 이 프로젝트의 주 관할."""
    return (0 if rule["_jurisdiction"] == "KR" else 1, rule["id"])


def render(metas: dict, rules: list[dict]) -> str:
    by_domain: dict[str, list[dict]] = {}
    for rule in rules:
        by_domain.setdefault(rule["domain"], []).append(rule)

    domains = [d for d in DOMAIN_ORDER if d in by_domain]
    domains += sorted(d for d in by_domain if d not in DOMAIN_ORDER)

    pending = [
        (r, b) for r in rules for b in r["legal_basis"] if b["verification"] == "확인필요"
    ]
    sev_count = {s: sum(1 for r in rules if r["severity_base"] == s) for s in SEVERITIES}

    L: list[str] = []
    add = L.append

    add("# 컴플라이언스 룰 카탈로그")
    add("")
    add("> **생성물입니다. 이 파일을 직접 수정하지 마세요.**")
    add("> 원본은 `rules/kr.yaml`·`rules/eu.yaml`이며,")
    add("> 이 문서는 `python tools/render_rules.py`로 생성됩니다.")
    add("")

    add("## 현황")
    add("")
    add(f"- 총 **{len(rules)}개** 룰 / {len(domains)}개 영역")
    for jur, meta in metas.items():
        count = sum(1 for r in rules if r["_jurisdiction"] == jur)
        add(f"- `{jur}` {meta['jurisdiction_name']} — {count}개 (v{meta['version']}, {meta['updated']})")
    add("- 기본 심각도: " + " / ".join(f"{s} {sev_count[s]}" for s in SEVERITIES if sev_count[s]))
    add(f"- **미검증 조문 {len(pending)}건** — 아래 마지막 절 참조")
    add("")

    for jur, meta in metas.items():
        if meta.get("applicability"):
            add(f"## `{jur}` 적용 범위")
            add("")
            add(meta["applicability"].rstrip())
            add("")

    add("## 요약")
    add("")
    add("| ID | 영역 | 제목 | 기본 심각도 | 근거 조문 | 검증 | 대상 |")
    add("|---|---|---|---|---|---|---|")
    for domain in domains:
        for rule in sorted(by_domain[domain], key=rule_key):
            targets = ", ".join(rule["applies_to"])
            if len(targets) > 40:
                targets = f"{len(rule['applies_to'])}개 항목"
            add(
                f"| `{rule['id']}` | {rule['domain']} | {rule['title']} "
                f"| {rule['severity_base']} | {basis_line(rule)} | {verify_mark(rule)} | {targets} |"
            )
    add("")

    add("## 영역별 상세")
    add("")
    for domain in domains:
        add(f"### {domain}")
        add("")
        for rule in sorted(by_domain[domain], key=rule_key):
            add(f"#### `{rule['id']}` {rule['title']}")
            add("")
            add(rule["summary"].rstrip())
            add("")
            add("| 항목 | 내용 |")
            add("|---|---|")
            add(f"| 관할 | {rule['_jurisdiction']} |")
            add(f"| 기본 심각도 | **{rule['severity_base']}** |")
            add(f"| 대상 항목 | {', '.join(rule['applies_to'])} |")
            add(f"| 연관 룰 | {', '.join(f'`{x}`' for x in rule['related']) or '—'} |")
            add("")
            add("**근거 조문**")
            add("")
            add("| 법령 | 조문 | 내용 | 검증 |")
            add("|---|---|---|---|")
            for b in rule["legal_basis"]:
                mark = "확인완료" if b["verification"] == "확인완료" else "**확인필요**"
                if b["verification"] == "확인완료":
                    mark += f" ({b['checked_at']})"
                add(f"| {b['law']} | {b['article']} | {b['note']} | {mark} |")
            add("")
            add("**판정 조건**")
            add("")
            add(rule["condition_human"].rstrip())
            add("")
            add("```python")
            add(rule["check_expr"].rstrip())
            add("```")
            add("")
            add("**심각도 근거**")
            add("")
            add(rule["severity_rationale"].rstrip())
            add("")
            add("**개선 조치**")
            add("")
            add(bullets(rule["remediation"]))
            add("")
            add("**요구 증적**")
            add("")
            add(bullets(rule["evidence"]))
            add("")
            if rule.get("notes"):
                add("**비고**")
                add("")
                add(rule["notes"].rstrip())
                add("")

    add("## 미검증 조문")
    add("")
    if not pending:
        add("없음 — 모든 근거 조문이 원문 대조를 마쳤습니다.")
    else:
        add(f"아래 **{len(pending)}건**은 원문 대조 전 초안입니다. 조문 번호·항 구분에 오류가 있을 수 있습니다.")
        add("")
        add("| 룰 | 법령 | 조문 | 내용 |")
        add("|---|---|---|---|")
        for rule, b in pending:
            add(f"| `{rule['id']}` | {b['law']} | {b['article']} | {b['note']} |")
        add("")
        add("검증 출처: [국가법령정보센터](https://www.law.go.kr/) · "
            "[EUR-Lex](https://eur-lex.europa.eu/) · [EDPB](https://www.edpb.europa.eu/)")
        add("")
        add("검증 완료 시 해당 `legal_basis`의 `verification`을 `확인완료`로 바꾸고 "
            "`checked_at`·`source`를 채운 뒤 이 문서를 다시 생성하세요.")
    add("")

    return "\n".join(L)


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    check_only = "--check" in sys.argv

    metas, rules = load()
    errors = validate(rules)
    if errors:
        print(f"[FAIL] 스키마 검증 실패 ({len(errors)}건)")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    content = render(metas, rules)

    if check_only:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != content:
            print("[FAIL] CATALOG.md가 원본 YAML과 다릅니다. "
                  "`python tools/render_rules.py`로 다시 생성하세요.")
            sys.exit(1)
        print(f"[OK] 룰 {len(rules)}개 검증 통과, CATALOG.md 최신 상태")
        return

    OUT.write_text(content, encoding="utf-8", newline="\n")
    pending = sum(
        1 for r in rules for b in r["legal_basis"] if b["verification"] == "확인필요"
    )
    print(f"[OK] 룰 {len(rules)}개 -> {OUT.relative_to(ROOT).as_posix()}")
    print(f"[WARN] 미검증 조문 {pending}건 — 원문 대조 필요")


if __name__ == "__main__":
    main()
