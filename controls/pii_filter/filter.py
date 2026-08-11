"""전송 전 개인정보 필터 — 탐지 결과에 정책을 적용해 차단·마스킹한다.

## 설계 원칙

**① 마스킹은 문장의 의미를 보존해야 한다.**
이 필터의 출력은 곧바로 LLM 판정기로 들어간다. 마스킹 때문에 주문이 판정되지
않으면 통제가 기능을 파괴한 것이고, 그러면 통제가 꺼진다. 자리 표시를 남기는
방식으로 마스킹해 문장 구조를 유지한다.

**② 탐지 로그에 원문을 남기지 않는다.**
개인정보 유출을 막는 필터가 그 개인정보를 로그에 적으면 위험을 옮긴 것에 불과하다.
감사 기록에는 무엇이 몇 개 탐지되었는지와 위치만 남기고 값은 남기지 않는다.

**③ 차단은 조용히 하지 않는다.**
차단 시 이용자에게 무엇 때문인지 알려야 한다. 알리지 않으면 이용자는 게임이
고장난 것으로 인식하고, 우회를 시도한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .detectors import ALL_DETECTORS, Action, Category, Detection, Detector, detect


@dataclass(frozen=True)
class FilterPolicy:
    """탐지기별 조치. 지정하지 않은 탐지기는 기본 조치를 따른다."""
    overrides: dict[str, Action] = field(default_factory=dict)
    detectors: list[Detector] | None = None

    def action_for(self, detection: Detection) -> Action:
        return self.overrides.get(detection.detector, detection.action)


#: 국내 기준 기본 정책 — 고유식별정보·금융정보는 차단, 연락처는 마스킹
KR_DEFAULT = FilterPolicy()

#: 최소 개입 정책 — 전부 마스킹만. 차단이 서비스에 미치는 영향을 검토하는 단계용
MASK_ONLY = FilterPolicy(overrides={d.name: Action.MASK for d in ALL_DETECTORS})


@dataclass(frozen=True)
class AuditRecord:
    """감사 기록. **탐지된 값 자체는 담지 않는다.**"""
    detected: dict[str, int]
    blocked: bool
    masked_count: int

    def as_dict(self) -> dict:
        return {"detected": dict(self.detected), "blocked": self.blocked,
                "masked_count": self.masked_count}


@dataclass(frozen=True)
class FilterResult:
    allowed: bool
    text: str
    detections: list[Detection]
    audit: AuditRecord
    reason: str | None = None

    @property
    def modified(self) -> bool:
        return self.audit.masked_count > 0


# ── 마스킹 ──────────────────────────────────────────────────

def _mask_email(value: str) -> str:
    local, _, domain = value.partition("@")
    head = local[0] if local else "*"
    tld = domain.rpartition(".")[2]
    return f"{head}{'*' * max(len(local) - 1, 1)}@{'*' * 3}.{tld}"


def _mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    return f"{digits[:3]}-****-****"


def _mask_generic(value: str) -> str:
    return "*" * len(re.sub(r"\D", "", value))


_MASKERS = {
    "email_address": _mask_email,
    "korean_mobile_number": _mask_phone,
}


def mask_value(detection: Detection) -> str:
    return _MASKERS.get(detection.detector, _mask_generic)(detection.matched)


# ── 파이프라인 ───────────────────────────────────────────────

BLOCK_MESSAGE = (
    "주문에 주민등록번호·카드번호 같은 정보가 포함된 것으로 보입니다. "
    "해당 정보는 외부로 전송되지 않으며, 빼고 다시 영창해 주세요."
)


def apply(text: str, policy: FilterPolicy = KR_DEFAULT) -> FilterResult:
    """전송 전 필터를 적용한다.

    차단 대상이 하나라도 있으면 `allowed=False`이며, 이때 `text`는 **원문을 담지
    않는다**. 호출부가 실수로 차단된 원문을 전송하는 것을 구조적으로 막기 위한 것이다.
    """
    detections = detect(text, policy.detectors)
    counts: dict[str, int] = {}
    for det in detections:
        counts[det.detector] = counts.get(det.detector, 0) + 1

    blocked = [d for d in detections if policy.action_for(d) is Action.BLOCK]
    if blocked:
        return FilterResult(
            allowed=False,
            text="",
            detections=detections,
            audit=AuditRecord(detected=counts, blocked=True, masked_count=0),
            reason=BLOCK_MESSAGE,
        )

    masked_count = 0
    out = text
    for det in sorted(detections, key=lambda d: d.start, reverse=True):
        if policy.action_for(det) is not Action.MASK:
            continue
        out = out[:det.start] + mask_value(det) + out[det.end:]
        masked_count += 1

    return FilterResult(
        allowed=True,
        text=out,
        detections=detections,
        audit=AuditRecord(detected=counts, blocked=False, masked_count=masked_count),
    )


__all__ = [
    "Action", "Category", "Detection", "FilterPolicy", "FilterResult", "AuditRecord",
    "KR_DEFAULT", "MASK_ONLY", "apply", "mask_value", "BLOCK_MESSAGE",
]
