#!/usr/bin/env python3
"""컴플라이언스 룰 엔진 — 룰 카탈로그를 인벤토리에 적용해 Finding 후보를 도출한다.

    python tools/run_rules.py                  전 데이터셋 실행
    python tools/run_rules.py --dataset tobe   특정 데이터셋만
    python tools/run_rules.py --check          재생성 없이 동기화 검증 (CI용)

## 이 엔진이 하는 일과 하지 않는 일

**한다** — 룰의 `check` 술어를 인벤토리에 적용해 "어떤 룰이 어떤 대상에서 발동하는가"를
기계적으로 판정한다. 판정은 결정적이며 근거(어느 필드가 왜 걸렸는가)를 함께 낸다.

**하지 않는다** — 위험도 산정, 리스크 시나리오 작성, 개선 우선순위 결정.
Likelihood는 시스템 구조와 맥락에 대한 판단이고, 인벤토리에 그 정보가 없다.
엔진의 출력은 **Finding 후보**이며, 사람이 위험도와 시나리오를 붙여야 Finding이 된다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
INV_DIR = ROOT / "inventory"
OUT_DIR = ROOT / "reports"

DATASETS = {
    "asis": {"file": "incant_asis.yaml", "label": "As-Is (실제 배포 데모)"},
    "tobe": {"file": "incant_tobe.yaml", "label": "To-Be (상용화 가정)"},
}

COLLECTION_SCOPES = {"data_items", "flows", "channels", "vendors"}
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


# ── 술어 평가 ────────────────────────────────────────────────

MISSING = object()


def resolve(entity: dict, root: dict, field: str):
    """점 표기 경로를 푼다. 'service.' 접두는 인벤토리 루트의 service를 가리킨다."""
    if field.startswith("service."):
        cursor, parts = root.get("service", {}), field.split(".")[1:]
    else:
        cursor, parts = entity, field.split(".")
    for part in parts:
        if not isinstance(cursor, dict) or part not in cursor:
            return MISSING
        cursor = cursor[part]
    return cursor


OPS = {
    "is_null": lambda v, _: v is None or v is MISSING,
    "is_not_null": lambda v, _: v is not None and v is not MISSING,
    "is_true": lambda v, _: v is True,
    "is_false": lambda v, _: v is False,
    "eq": lambda v, x: v == x,
    "ne": lambda v, x: v != x,
    "in": lambda v, x: v in (x or []),
    "not_in": lambda v, x: v not in (x or []),
}


def evaluate(cond: dict, entity: dict, root: dict) -> tuple[bool, str]:
    field, op = cond["field"], cond["op"]
    if op not in OPS:
        raise ValueError(f"알 수 없는 연산자: {op}")
    value = resolve(entity, root, field)
    result = OPS[op](value, cond.get("value"))
    shown = "(필드 없음)" if value is MISSING else json.dumps(value, ensure_ascii=False)
    return result, f"`{field}` {op} → {shown}"


def check_entity(check: dict, entity: dict, root: dict) -> tuple[bool, list[str]]:
    """all_of는 AND, any_of는 OR. 둘 다 있으면 AND로 결합한다."""
    reasons: list[str] = []

    for cond in check.get("all_of") or []:
        ok, why = evaluate(cond, entity, root)
        if not ok:
            return False, []
        reasons.append(why)

    any_conds = check.get("any_of") or []
    if any_conds:
        hits = [why for ok, why in (evaluate(c, entity, root) for c in any_conds) if ok]
        if not hits:
            return False, []
        reasons.extend(hits)

    if not (check.get("all_of") or any_conds):
        return False, []
    return True, reasons


# ── 실행 ────────────────────────────────────────────────────

def load_rules() -> list[dict]:
    rules = []
    for name in ("kr.yaml", "eu.yaml"):
        doc = yaml.safe_load((RULES_DIR / name).read_text(encoding="utf-8"))
        for rule in doc["rules"]:
            rule["_jurisdiction"] = doc["meta"]["jurisdiction"]
            rules.append(rule)
    return rules


def run(rules: list[dict], inv: dict) -> list[dict]:
    service = inv.get("service", {})
    applicable = set(service.get("jurisdictions") or [])
    conditional = set(service.get("jurisdictions_conditional") or [])

    findings: list[dict] = []
    for rule in rules:
        jur = rule["_jurisdiction"]
        if jur not in applicable and jur not in conditional:
            continue
        check = rule.get("check")
        if not check:
            continue

        scope = check["scope"]
        entities = [("(서비스 전체)", service)] if scope == "service" else [
            (e.get("id", "?"), e) for e in inv.get(scope) or []
        ]
        if scope not in COLLECTION_SCOPES and scope != "service":
            raise ValueError(f"{rule['id']}: 알 수 없는 scope — {scope}")

        for entity_id, entity in entities:
            fired, reasons = check_entity(check, entity, inv)
            if not fired:
                continue
            findings.append({
                "rule_id": rule["id"],
                "jurisdiction": jur,
                "conditional": jur in conditional,
                "domain": rule["domain"],
                "title": rule["title"],
                "severity_base": rule["severity_base"],
                "scope": scope,
                "target_id": entity_id,
                "target_name": entity.get("name", entity_id),
                "reasons": reasons,
                "legal_basis": [f"{b['law']} {b['article']}" for b in rule["legal_basis"]],
                "remediation": rule.get("remediation") or [],
            })
    return findings


# ── 리포트 ───────────────────────────────────────────────────

def render(dataset: str, inv: dict, rules: list[dict], findings: list[dict]) -> str:
    label = DATASETS[dataset]["label"]
    service = inv.get("service", {})
    conditional_jur = service.get("jurisdictions_conditional") or []

    by_rule: dict[str, list[dict]] = {}
    for f in findings:
        by_rule.setdefault(f["rule_id"], []).append(f)

    evaluated = [r for r in rules
                 if r["_jurisdiction"] in set(service.get("jurisdictions") or [])
                 | set(conditional_jur)]
    silent = [r for r in evaluated if r["id"] not in by_rule]

    L: list[str] = []
    add = L.append

    add(f"# 룰 적용 결과 — {label}")
    add("")
    add("> **생성물입니다. 직접 수정하지 마세요.**")
    add("> `python tools/run_rules.py`로 생성됩니다.")
    add("")
    add("> **이것은 Finding 후보입니다.** 엔진은 룰의 술어가 인벤토리에서 참이 되는")
    add("> 지점만 기계적으로 찾습니다. 위험도 산정·리스크 시나리오·개선 우선순위는")
    add("> 인벤토리에 없는 맥락 판단이므로 사람이 붙여야 합니다.")
    add("")

    add("## 요약")
    add("")
    add(f"- 데이터셋: `{dataset}` — {inv['meta']['service_name']} (v{inv['meta']['version']})")
    add(f"- 적용 관할: {', '.join(service.get('jurisdictions') or []) or '—'}"
        + (f" / **조건부** {', '.join(conditional_jur)}" if conditional_jur else ""))
    add(f"- 평가한 룰 **{len(evaluated)}개** 중 **{len(by_rule)}개 발동**, {len(silent)}개 미발동")
    add(f"- Finding 후보 **{len(findings)}건**")
    add("")

    counts = {s: sum(1 for f in findings if f["severity_base"] == s) for s in SEVERITY_ORDER}
    add("| 기본 심각도 | 후보 수 | 발동 룰 |")
    add("|---|---|---|")
    for s in SEVERITY_ORDER:
        rule_ids = sorted({f["rule_id"] for f in findings if f["severity_base"] == s})
        if rule_ids:
            add(f"| {s} | {counts[s]} | {', '.join(f'`{r}`' for r in rule_ids)} |")
    add("")

    if conditional_jur:
        add(f"> ⚠️ `{', '.join(conditional_jur)}` 관할 룰의 판정은 **조건부**입니다.")
        add("> 해당 관할의 적용 여부 자체가 확정되지 않았습니다. 위반 사실로 기재하지 마세요.")
        add("")

    add("## 발동 룰별 상세")
    add("")
    for rule_id in sorted(by_rule, key=lambda r: (SEVERITY_ORDER.index(by_rule[r][0]["severity_base"]), r)):
        group = by_rule[rule_id]
        head = group[0]
        cond = " · **조건부**" if head["conditional"] else ""
        add(f"### `{rule_id}` {head['title']}")
        add("")
        add(f"{head['domain']} · {head['jurisdiction']} · 기본 심각도 **{head['severity_base']}**{cond} · 대상 {len(group)}건")
        add("")
        add(f"근거: {' · '.join(head['legal_basis'])}")
        add("")
        add("| 대상 | 발동 사유 |")
        add("|---|---|")
        for f in group:
            add(f"| `{f['target_id']}` {f['target_name']} | {' / '.join(f['reasons'])} |")
        add("")
        if head["remediation"]:
            add("개선 조치:")
            add("")
            for r in head["remediation"]:
                add(f"- {r}")
            add("")

    add("## 미발동 룰")
    add("")
    if not silent:
        add("없음 — 평가한 모든 룰이 발동했습니다.")
    else:
        add("아래 룰은 이 인벤토리에서 발동하지 않았습니다. "
            "해당 통제가 갖추어졌거나, 인벤토리에 평가 대상이 없는 경우입니다.")
        add("")
        add("| 룰 | 영역 | 평가 대상 |")
        add("|---|---|---|")
        for r in sorted(silent, key=lambda x: x["id"]):
            scope = (r.get("check") or {}).get("scope", "—")
            n = len(inv.get(scope) or []) if scope in COLLECTION_SCOPES else 1
            add(f"| `{r['id']}` | {r['domain']} | {scope} ({n}건) |")
    add("")

    add("---")
    add("")
    add(f"룰 카탈로그 `rules/` · 인벤토리 `inventory/{DATASETS[dataset]['file']}`")
    add("")
    return "\n".join(L)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    check_only = "--check" in argv
    only = None
    if "--dataset" in argv:
        only = argv[argv.index("--dataset") + 1]

    OUT_DIR.mkdir(exist_ok=True)
    rules = load_rules()
    failed = False

    for dataset, cfg in DATASETS.items():
        if only and dataset != only:
            continue
        src = INV_DIR / cfg["file"]
        if not src.exists():
            print(f"[SKIP] 인벤토리 없음 — {src.name}")
            continue
        inv = yaml.safe_load(src.read_text(encoding="utf-8"))
        findings = run(rules, inv)

        md = render(dataset, inv, rules, findings)
        md_path = OUT_DIR / f"findings_{dataset}.md"
        js_path = OUT_DIR / f"findings_{dataset}.json"
        js = json.dumps({"dataset": dataset, "findings": findings}, ensure_ascii=False, indent=1)

        if check_only:
            stale = (md_path.read_text(encoding="utf-8") if md_path.exists() else "") != md \
                or (js_path.read_text(encoding="utf-8") if js_path.exists() else "") != js
            if stale:
                print(f"[FAIL] {dataset}: 리포트가 최신이 아닙니다. `python tools/run_rules.py` 실행 필요")
                failed = True
            else:
                print(f"[OK] {dataset}: Finding 후보 {len(findings)}건, 리포트 최신")
            continue

        md_path.write_text(md, encoding="utf-8", newline="\n")
        js_path.write_text(js, encoding="utf-8", newline="\n")
        fired = len({f["rule_id"] for f in findings})
        print(f"[OK] {dataset}: 룰 {fired}개 발동, Finding 후보 {len(findings)}건 -> {md_path.name}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
