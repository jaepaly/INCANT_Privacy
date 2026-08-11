"""전송 전 개인정보 필터.

As-Is Finding `F-005`(자유 텍스트를 통한 개인정보 비의도적 유입)에 대응하는
통제 `CTRL-001`의 참조 구현이다.

    from controls.pii_filter import apply

    result = apply("내 번호 010-1234-5678로 불을 보내라")
    if result.allowed:
        send_to_judge(result.text)     # "내 번호 010-****-****로 불을 보내라"
    else:
        show_to_user(result.reason)

자세한 배경은 `controls/README.md`.
"""

from .detectors import (
    ALL_DETECTORS, Action, Category, Detection, Detector, detect,
    luhn_ok, rrn_checksum_ok,
)
from .filter import (
    KR_DEFAULT, MASK_ONLY, AuditRecord, FilterPolicy, FilterResult,
    BLOCK_MESSAGE, apply, mask_value,
)

__all__ = [
    "ALL_DETECTORS", "Action", "Category", "Detection", "Detector", "detect",
    "luhn_ok", "rrn_checksum_ok",
    "KR_DEFAULT", "MASK_ONLY", "AuditRecord", "FilterPolicy", "FilterResult",
    "BLOCK_MESSAGE", "apply", "mask_value",
]
