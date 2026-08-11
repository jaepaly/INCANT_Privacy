#!/usr/bin/env python3
"""inventory/*.yaml -> docs/to-be/03_data_inventory.md 생성기.

인벤토리를 문서로만 관리하면 룰 엔진이 읽을 수 없고, YAML로만 두면 사람이 읽지
않는다. 원본은 YAML 하나로 두고 문서는 여기서 생성한다.

    python tools/render_inventory.py          생성
    python tools/render_inventory.py --check  검증만 (CI용, 위반 시 exit 1)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "inventory" / "incant_tobe.yaml"
OUT = ROOT / "docs" / "to-be" / "03_data_inventory.md"

CATEGORIES = ["일반", "고유식별정보", "민감정보", "인증정보", "행태정보"]
RETENTION_TYPES = ["법정", "정책", "조건부"]

REQUIRED_ITEM = [
    "id", "name", "activity", "category", "purposes", "collected_at",
    "legal_ground", "retention", "stored_in",
]


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    system_ids = {s["id"] for s in doc["systems"]}
    vendor_ids = {v["id"] for v in doc["vendors"]}
    channel_ids = {c["id"] for c in doc.get("channels", [])}
    item_ids = {i.get("id") for i in doc["data_items"]}

    for item in doc["data_items"]:
        iid = item.get("id", "<id 없음>")
        for field in REQUIRED_ITEM:
            if item.get(field) in (None, [], ""):
                if field == "stored_in" and item.get("retention", {}).get("period") == "미보관":
                    continue          # 미보관 항목은 저장 위치가 비어 있는 것이 정상
                errors.append(f"{iid}: 필수 필드 누락 — {field}")

        if item.get("category") not in CATEGORIES:
            errors.append(f"{iid}: category 값 오류 — {CATEGORIES}")

        retention = item.get("retention") or {}
        if retention.get("type") not in RETENTION_TYPES:
            errors.append(f"{iid}: retention.type 값 오류 — {RETENTION_TYPES}")
        if retention.get("type") == "법정" and not retention.get("basis"):
            errors.append(f"{iid}: 법정 보존기간은 basis(근거 법령·조문) 필수")
        if retention.get("verified") is None:
            errors.append(f"{iid}: retention.verified 누락 — 근거 확인 여부를 명시할 것")

        for sid in item.get("stored_in") or []:
            if sid not in system_ids:
                errors.append(f"{iid}: 존재하지 않는 시스템 참조 — {sid}")
        for vid in item.get("vendors") or []:
            if vid not in vendor_ids:
                errors.append(f"{iid}: 존재하지 않는 수탁자 참조 — {vid}")
        if item.get("channel") and item["channel"] not in channel_ids:
            errors.append(f"{iid}: 존재하지 않는 채널 참조 — {item['channel']}")

    for flow in doc["flows"]:
        for ref in flow.get("items") or []:
            if ref not in item_ids:
                errors.append(f"{flow['id']}: 존재하지 않는 항목 참조 — {ref}")
        if flow.get("is_overseas") and not flow.get("transfer_ground"):
            # 오류가 아니라 룰이 잡아야 할 상태 — 검증에서는 통과시킨다
            pass

    return errors


def render(doc: dict) -> str:
    items = doc["data_items"]
    vendors = {v["id"]: v for v in doc["vendors"]}
    systems = {s["id"]: s for s in doc["systems"]}

    overseas_vendors = [v for v in doc["vendors"] if v.get("is_overseas")]
    unverified = [i for i in items if not (i.get("retention") or {}).get("verified")]
    statutory = [i for i in items if (i.get("retention") or {}).get("type") == "법정"]
    special_risk = [i for i in items if i.get("gdpr_special_category_risk")]

    L: list[str] = []
    add = L.append

    add("# INCANT 개인정보 인벤토리 (To-Be)")
    add("")
    add("> **생성물입니다. 이 파일을 직접 수정하지 마세요.**")
    add("> 원본은 `inventory/incant_tobe.yaml`이며,")
    add("> 이 문서는 `python tools/render_inventory.py`로 생성됩니다.")
    add("")
    add("> **To-Be 문서**입니다. 가정에 기반하며, 근거는")
    add("> [01_policy_benchmark.md](01_policy_benchmark.md)와 [02_service_model.md](02_service_model.md)입니다.")
    add("")

    add("## 현황")
    add("")
    add(f"- 개인정보 항목 **{len(items)}건** / 시스템 {len(systems)}개 / 수탁자 {len(doc['vendors'])}개")
    add(f"- 국외 이전 대상 수탁자 **{len(overseas_vendors)}개** — {', '.join(v['name'] for v in overseas_vendors)}")
    add(f"- 법정 보존기간 적용 항목 {len(statutory)}건")
    add(f"- **보유기간 근거 미확정 {len(unverified)}건** — 아래 §5 참조")
    add(f"- 특별범주 유입 위험 채널을 거치는 항목 {len(special_risk)}건")
    add("")

    by_category: dict[str, int] = {}
    for item in items:
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
    add("| 유형 | 건수 |")
    add("|---|---|")
    for cat in CATEGORIES:
        if by_category.get(cat):
            add(f"| {cat} | {by_category[cat]} |")
    add("")

    add("## 1. 개인정보 항목")
    add("")
    activities: list[str] = []
    for item in items:
        if item["activity"] not in activities:
            activities.append(item["activity"])

    for activity in activities:
        add(f"### {activity}")
        add("")
        add("| ID | 항목 | 유형 | 처리 목적 | 수집 경로 | 보유기간 | 근거 | 저장 위치 | 수탁자 |")
        add("|---|---|---|---|---|---|---|---|---|")
        for item in [i for i in items if i["activity"] == activity]:
            r = item.get("retention") or {}
            mark = "" if r.get("verified") else " ⚠️"
            basis = r.get("basis") or ("정책상 기간" if r.get("type") == "정책" else "—")
            vendor_names = ", ".join(vendors[v]["name"] for v in item.get("vendors") or []) or "—"
            stored = ", ".join(item.get("stored_in") or []) or "—"
            star = "★ " if item.get("gdpr_special_category_risk") else ""
            add(
                f"| `{item['id']}` | {star}{item['name']} | {item['category']} "
                f"| {', '.join(item['purposes'])} | {item['collected_at']} "
                f"| **{r.get('period')}**{mark} | {basis} | {stored} | {vendor_names} |"
            )
        add("")

    add("★ = 자유 텍스트·파일 채널을 거쳐 특별범주 정보가 비의도적으로 유입될 수 있는 항목")
    add("")
    add("⚠️ = 보유기간의 근거가 원문으로 확인되지 않은 항목")
    add("")

    add("## 2. 처리 근거")
    add("")
    add("| ID | 항목 | 국내 | EU (GDPR Art.6) |")
    add("|---|---|---|---|")
    for item in items:
        g = item.get("legal_ground") or {}
        add(f"| `{item['id']}` | {item['name']} | {g.get('kr', '—')} | {g.get('eu', '—')} |")
    add("")

    add("## 3. 수탁자·외부 사업자")
    add("")
    add("| ID | 사업자 | 관계 | 처리 업무 | 국가 | 국외이전 | 계약(DPA) |")
    add("|---|---|---|---|---|---|---|")
    for v in doc["vendors"]:
        overseas = "**해당**" if v.get("is_overseas") else "미해당"
        dpa = v.get("dpa") or "**미체결**"
        add(f"| `{v['id']}` | {v['name']} | {v['relation']} | {v['task']} | {v['country']} | {overseas} | {dpa} |")
    add("")
    for v in doc["vendors"]:
        if v.get("note"):
            add(f"**`{v['id']}` {v['name']}** — {v['note'].strip()}")
            add("")

    add("## 4. 데이터 흐름")
    add("")
    add("| ID | 흐름 | 출발 | 도착 | 항목 | 유형 | 국외 | 이전 근거 |")
    add("|---|---|---|---|---|---|---|---|")
    for f in doc["flows"]:
        overseas = "**해당**" if f.get("is_overseas") else "—"
        ground = f.get("transfer_ground") or "**미정의**"
        add(
            f"| `{f['id']}` | {f['name']} | {f.get('from') or '—'} | {f.get('to') or '(파기)'} "
            f"| {', '.join(f.get('items') or [])} | {f['type']} | {overseas} | {ground} |"
        )
    add("")

    add("## 5. 보유기간 근거의 확인 상태")
    add("")
    add("**법정 보존기간 — 원문 확인 완료**")
    add("")
    add("| 항목 | 기간 | 근거 |")
    add("|---|---|---|")
    seen: set[str] = set()
    for item in statutory:
        basis = (item["retention"].get("basis") or "").strip()
        if basis in seen:
            continue
        seen.add(basis)
        add(f"| {item['name']} | {item['retention']['period']} | {basis} |")
    add("")

    if unverified:
        add("**근거 미확정 — 확정 근거로 사용하지 않습니다**")
        add("")
        add("| ID | 항목 | 기재된 기간 | 사유 |")
        add("|---|---|---|---|")
        for item in unverified:
            r = item["retention"]
            add(f"| `{item['id']}` | {item['name']} | {r.get('period')} | {r.get('basis') or '근거 미기재'} |")
        add("")

    add("## 6. 자유 입력 채널")
    add("")
    add("| ID | 채널 | 입력 유형 | 저장 | 외부 전송 | 사전 필터 |")
    add("|---|---|---|---|---|---|")
    for c in doc.get("channels", []):
        add(
            f"| `{c['id']}` | {c['name']} | {c['input_type']} "
            f"| {'예' if c.get('is_stored') else '아니오'} "
            f"| {'예' if c.get('is_transferred') else '아니오'} "
            f"| {c.get('pii_prefilter') or '**없음**'} |"
        )
    add("")

    add("## 7. 미충족 상태 (룰 평가 대상)")
    add("")
    add("이 인벤토리에서 룰이 발동할 지점입니다. 실제 판정은 룰 엔진 구현 후 수행합니다.")
    add("")
    svc = doc["service"]
    add("| 대상 | 상태 |")
    add("|---|---|")
    for key, label in [
        ("privacy_policy_url", "개인정보 처리방침"),
        ("privacy_notice_eu", "EU privacy notice"),
        ("privacy_contact", "권리행사 창구"),
        ("data_access_ui", "열람 수단"),
        ("erasure_mechanism", "삭제 수단"),
        ("age_verification", "연령 확인"),
        ("age_gate_branching", "연령 게이트 관할 분기"),
    ]:
        add(f"| {label} | {svc.get(key) or '**미수립**'} |")
    no_dpa = [v["name"] for v in doc["vendors"] if not v.get("dpa")]
    add(f"| 처리위탁 계약(DPA) | **미체결 {len(no_dpa)}개** — {', '.join(no_dpa)} |")
    no_ground = [f["id"] for f in doc["flows"] if f.get("is_overseas") and not f.get("transfer_ground")]
    if no_ground:
        add(f"| 국외이전 근거 미정의 | **{', '.join(no_ground)}** |")
    add("")

    add("---")
    add("")
    add(f"원본: `inventory/incant_tobe.yaml` v{doc['meta']['version']} ({doc['meta']['updated']})")
    add("")

    return "\n".join(L)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    check_only = "--check" in sys.argv

    if not SRC.exists():
        fail(f"원본 없음: {SRC}")
    doc = yaml.safe_load(SRC.read_text(encoding="utf-8"))

    errors = validate(doc)
    if errors:
        print(f"[FAIL] 스키마 검증 실패 ({len(errors)}건)")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    content = render(doc)

    if check_only:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != content:
            print("[FAIL] 03_data_inventory.md가 원본 YAML과 다릅니다. "
                  "`python tools/render_inventory.py`로 다시 생성하세요.")
            sys.exit(1)
        print(f"[OK] 항목 {len(doc['data_items'])}건 검증 통과, 문서 최신 상태")
        return

    OUT.write_text(content, encoding="utf-8", newline="\n")
    unverified = sum(1 for i in doc["data_items"] if not (i.get("retention") or {}).get("verified"))
    print(f"[OK] 항목 {len(doc['data_items'])}건 -> {OUT.relative_to(ROOT).as_posix()}")
    if unverified:
        print(f"[WARN] 보유기간 근거 미확정 {unverified}건")


if __name__ == "__main__":
    main()
