#!/usr/bin/env python3
"""저장소의 현재 컴플라이언스 상태를 요약한다.

CI가 매 실행마다 이 요약을 남긴다. 초록/빨강만 보이는 CI는 이 저장소에서 의미가
적다 — 무엇이 몇 건 열려 있고 근거 검증이 어디까지 됐는지가 실제 상태다.

    python tools/ci_summary.py            표준출력
    python tools/ci_summary.py --github   GitHub Actions 작업 요약에 추가
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def build() -> str:
    rules, unverified = [], 0
    for name in ("kr.yaml", "eu.yaml"):
        doc = yaml.safe_load((ROOT / "rules" / name).read_text(encoding="utf-8"))
        rules.extend(doc["rules"])
        unverified += sum(
            1 for r in doc["rules"] for b in r["legal_basis"]
            if b["verification"] == "확인필요"
        )

    L = ["## 컴플라이언스 상태", ""]

    L += [f"- 룰 **{len(rules)}개** (KR {sum(1 for r in rules if r['id'].startswith('KR'))}"
          f" / EU {sum(1 for r in rules if r['id'].startswith('EU'))})"]
    L += [f"- 근거 조문 미검증 **{unverified}건**"
          + ("" if unverified else " — 전건 원문 대조 완료")]

    inv_path = ROOT / "inventory" / "incant_tobe.yaml"
    if inv_path.exists():
        inv = yaml.safe_load(inv_path.read_text(encoding="utf-8"))
        items = inv["data_items"]
        no_basis = sum(1 for i in items if not (i.get("retention") or {}).get("verified"))
        L += [f"- To-Be 인벤토리 항목 **{len(items)}건** / 보유기간 근거 미확정 {no_basis}건"]

    L += ["", "### 룰 적용 결과", "", "| 데이터셋 | 발동 룰 | Finding 후보 |", "|---|---|---|"]
    for dataset, label in (("asis", "As-Is"), ("tobe", "To-Be")):
        path = ROOT / "reports" / f"findings_{dataset}.json"
        if not path.exists():
            continue
        findings = json.loads(path.read_text(encoding="utf-8"))["findings"]
        fired = len({f["rule_id"] for f in findings})
        L += [f"| {label} | {fired} / {len(rules)} | {len(findings)} |"]

    tobe = ROOT / "reports" / "findings_tobe.json"
    if tobe.exists():
        findings = json.loads(tobe.read_text(encoding="utf-8"))["findings"]
        by_sev: dict[str, int] = {}
        for f in findings:
            by_sev[f["severity_base"]] = by_sev.get(f["severity_base"], 0) + 1
        parts = [f"{s} {by_sev[s]}" for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW") if by_sev.get(s)]
        L += ["", f"To-Be 후보 기본 심각도: {' / '.join(parts)}"]

    L += ["", "> Finding **후보**입니다. 위험도 산정과 시나리오는 사람이 붙입니다.", ""]
    return "\n".join(L)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    text = build()
    print(text)
    if "--github" in sys.argv:
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as fp:
                fp.write(text + "\n")


if __name__ == "__main__":
    main()
