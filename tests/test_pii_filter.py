"""전송 전 개인정보 필터 테스트 — 통제 CTRL-001의 증적.

이 테스트가 증명하려는 것은 "탐지가 된다"가 아니다. 그건 정규식만 있어도 된다.
증명해야 하는 것은 다음 넷이다.

1. **게임 주문이 오탐되지 않는다** — 오탐이 잦으면 통제가 꺼진다
2. **검증식이 형식만 맞는 값을 걸러낸다** — 게임에 우연히 들어간 숫자열 대응
3. **성명은 탐지하지 않는다** — F-005 식별가능성 분석의 결론을 코드에 고정
4. **차단·마스킹 후 원문이 밖으로 나가지 않는다** — 통제가 위험을 옮기지 않음

테스트에 쓰는 식별번호는 전부 **합성값**이다. 검증식을 통과하도록 계산해 만든 것이며
실재하는 번호가 아니다. 카드번호는 업계 공용 테스트 번호를 쓴다.
"""

from __future__ import annotations

import pytest

from controls.pii_filter import (
    Action, Category, KR_DEFAULT, MASK_ONLY, apply, detect, luhn_ok, rrn_checksum_ok,
)

# 합성 주민등록번호 — 검증식을 통과하도록 계산한 값
VALID_RRN = "900101-1234568"
INVALID_RRN = "900101-1234567"      # 검사숫자만 틀림
VALID_CARD = "4111-1111-1111-1111"  # 업계 공용 테스트 카드번호
INVALID_CARD = "4111-1111-1111-1112"


# ── 1. 게임 주문 오탐 방지 ─────────────────────────────────

GAME_SPELLS = [
    "화염구를 던져라",
    "번개가 세 번 내리쳐라",
    "얼음의 장벽이여 나를 지켜라",
    "빛과 어둠이 교차하는 일식의 왈츠",
    "파고들어 베고 빠져나온다",
    "팔원소 대합창",
    "배고프다",
    "1000의 검이 쏟아져라",
    "3연타로 베어라",
    "2026년의 종말을 부르는 불꽃",
    "레벨 99999999999999 마법",       # 긴 숫자열이지만 식별번호 아님
    "010 부대를 소환하라",              # 전화번호 접두만 있고 번호 아님
]


@pytest.mark.parametrize("spell", GAME_SPELLS)
def test_game_spells_are_not_flagged(spell: str) -> None:
    """정상 주문은 어떤 탐지기에도 걸리지 않는다."""
    result = apply(spell)
    assert result.detections == [], f"오탐: {spell} -> {result.detections}"
    assert result.allowed
    assert result.text == spell


# ── 2. 성명은 탐지 대상이 아니다 ────────────────────────────

NAME_SPELLS = [
    "김철수를 불태워라",
    "이영희에게 축복을",
    "박민수 님의 이름으로 심판하라",
]


@pytest.mark.parametrize("spell", NAME_SPELLS)
def test_personal_names_are_not_detected(spell: str) -> None:
    """성명 문자열은 탐지하지 않는다.

    As-Is F-005의 식별가능성 분석 결론이다. 성명만으로는 특정 개인을 알아볼 수 없고
    결합할 정보도 없으므로 개인정보로 보기 어렵다. 이름을 잡으려 들면 오탐만 커진다.
    이 테스트는 그 판단이 나중에 조용히 뒤집히는 것을 막는다.
    """
    assert apply(spell).detections == []


# ── 3. 검증식이 형식만 맞는 값을 걸러낸다 ──────────────────

def test_rrn_checksum_accepts_valid() -> None:
    assert rrn_checksum_ok("9001011234568")


def test_rrn_checksum_rejects_invalid() -> None:
    assert not rrn_checksum_ok("9001011234567")


def test_invalid_rrn_is_not_detected() -> None:
    """형식은 맞지만 검증식을 통과하지 못하면 탐지하지 않는다."""
    assert detect(f"주문에 {INVALID_RRN} 를 담는다") == []


def test_impossible_birthdate_is_not_detected() -> None:
    """생년월일이 성립하지 않으면 탐지하지 않는다 (13월, 32일)."""
    assert detect("901301-1234567") == []
    assert detect("900132-1234567") == []


def test_luhn_accepts_and_rejects() -> None:
    assert luhn_ok("4111111111111111")
    assert not luhn_ok("4111111111111112")


def test_invalid_card_is_not_detected() -> None:
    assert detect(f"결제는 {INVALID_CARD} 로") == []


# ── 4. 탐지와 조치 ────────────────────────────────────────

def test_rrn_is_detected_and_blocked() -> None:
    result = apply(f"내 주민번호는 {VALID_RRN} 이다")
    assert not result.allowed
    assert result.detections[0].category is Category.UNIQUE_ID
    assert result.detections[0].action is Action.BLOCK


def test_card_is_detected_and_blocked() -> None:
    result = apply(f"카드 {VALID_CARD} 로 결제")
    assert not result.allowed
    assert result.detections[0].category is Category.FINANCIAL


@pytest.mark.parametrize("phone", ["010-1234-5678", "01012345678", "010 1234 5678"])
def test_mobile_number_is_masked(phone: str) -> None:
    result = apply(f"내 번호 {phone}로 불을 보내라")
    assert result.allowed
    assert phone not in result.text
    assert "010-****-****" in result.text


def test_email_is_masked() -> None:
    result = apply("hong@example.com 으로 번개를 보내라")
    assert result.allowed
    assert "hong@example.com" not in result.text
    assert result.text.endswith("으로 번개를 보내라")


# ── 5. 마스킹이 문장의 의미를 보존한다 ─────────────────────

def test_masking_preserves_sentence_structure() -> None:
    """마스킹 후에도 주문이 문장으로 읽혀야 한다.

    이 필터의 출력은 곧바로 LLM 판정기로 간다. 마스킹이 문장을 부수면
    통제가 기능을 파괴한 것이고, 그러면 통제가 꺼진다.
    """
    result = apply("010-1234-5678 번호로 화염구를 세 번 던져라")
    assert result.allowed
    assert result.text == "010-****-**** 번호로 화염구를 세 번 던져라"
    assert "화염구를 세 번 던져라" in result.text


def test_multiple_detections_are_all_masked() -> None:
    result = apply("010-1234-5678 과 a@b.com 으로 보내라")
    assert result.allowed
    assert "010-1234-5678" not in result.text
    assert "a@b.com" not in result.text
    assert result.audit.masked_count == 2


# ── 6. 통제가 위험을 옮기지 않는다 ─────────────────────────

def test_blocked_result_does_not_carry_original_text() -> None:
    """차단 시 결과에 원문이 남지 않는다.

    호출부가 실수로 차단된 원문을 전송하는 것을 구조적으로 막는다.
    """
    original = f"주민번호 {VALID_RRN}"
    result = apply(original)
    assert not result.allowed
    assert result.text == ""
    assert VALID_RRN not in result.text


def test_audit_record_contains_no_personal_data() -> None:
    """감사 기록에 탐지된 값 자체를 담지 않는다.

    개인정보 유출을 막는 필터가 그 개인정보를 로그에 적으면 위험을 옮긴 것에 불과하다.
    """
    result = apply(f"주민번호 {VALID_RRN} 카드 {VALID_CARD} 폰 010-1234-5678")
    serialized = repr(result.audit.as_dict())
    for secret in (VALID_RRN, VALID_CARD, "010-1234-5678", "9001011234568"):
        assert secret not in serialized
    assert result.audit.detected["resident_registration_number"] == 1
    assert result.audit.blocked is True


def test_block_message_tells_user_why() -> None:
    """차단은 조용히 하지 않는다. 이유를 모르면 이용자는 우회를 시도한다."""
    result = apply(f"주민번호 {VALID_RRN}")
    assert result.reason
    assert "전송되지 않" in result.reason


# ── 7. 정책 전환 ──────────────────────────────────────────

def test_mask_only_policy_does_not_block() -> None:
    """차단이 서비스에 미치는 영향을 검토하는 단계에서 쓰는 정책."""
    result = apply(f"주민번호 {VALID_RRN}", policy=MASK_ONLY)
    assert result.allowed
    assert VALID_RRN not in result.text
    assert result.audit.masked_count == 1


def test_default_policy_blocks_unique_id() -> None:
    assert not apply(f"{VALID_RRN}", policy=KR_DEFAULT).allowed


# ── 8. 겹치는 탐지 처리 ────────────────────────────────────

def test_overlapping_detections_are_deduplicated() -> None:
    """같은 구간을 두 탐지기가 잡아도 결과는 하나다."""
    result = apply(VALID_RRN)
    spans = [(d.start, d.end) for d in result.detections]
    assert len(spans) == len(set(spans))
    for i, a in enumerate(result.detections):
        for b in result.detections[i + 1:]:
            assert not (a.start < b.end and b.start < a.end)
