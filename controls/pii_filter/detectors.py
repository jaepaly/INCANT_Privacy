"""전송 전 개인정보 탐지기.

## 탐지 범위를 좁힌 이유

앞선 분석(As-Is F-005)에서 두 가지가 확인되었다.

1. 자유 텍스트에 이용자 본인의 민감정보가 들어올 확률은 낮다
2. 성명 문자열만으로는 특정 개인을 알아볼 수 없어 개인정보로 보기 어렵다
   (결합 용이성 — 개인정보 보호법 제2조 제1호 나목)

따라서 이 모듈은 **"그 자체로 식별 가능하거나 법이 특별히 규정한 정형 식별자"만**
탐지한다. 이름 같아 보인다, 건강 얘기 같다 같은 **비정형 추론은 하지 않는다.**

그런 추론은 오탐이 크고, 게임 맥락에서는 특히 그렇다. "김철수를 불태워라"는
탐지 대상이 아니며, 그 판단의 근거는 F-005의 식별가능성 분석에 있다.

## 오탐을 줄이는 방법

정규식만 쓰지 않는다. 형식이 맞아도 **검증식을 통과해야** 탐지로 인정한다.
주민등록번호는 생년월일 유효성과 체크섬, 신용카드는 Luhn 검증을 거친다.
게임 주문에 우연히 13자리 숫자가 들어가는 경우를 걸러내기 위한 것이다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    """탐지 시 취할 조치."""
    BLOCK = "block"   # 전송 차단
    MASK = "mask"     # 마스킹 후 전송
    ALLOW = "allow"   # 통과 (기록만)


class Category(str, Enum):
    """국내 개인정보 보호법 기준 분류."""
    UNIQUE_ID = "고유식별정보"      # 제24조
    FINANCIAL = "금융정보"
    CONTACT = "연락처"


@dataclass(frozen=True)
class Detection:
    detector: str
    category: Category
    start: int
    end: int
    matched: str
    action: Action

    @property
    def length(self) -> int:
        return self.end - self.start


# ── 검증식 ──────────────────────────────────────────────────

def _valid_birth(yymmdd: str, century_digit: str) -> bool:
    """주민등록번호 앞 6자리 + 성별코드로 생년월일 유효성을 본다."""
    if century_digit not in "1234":     # 5~8은 외국인, 9·0은 1800년대
        return False
    month, day = int(yymmdd[2:4]), int(yymmdd[4:6])
    if not 1 <= month <= 12:
        return False
    days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    return 1 <= day <= days_in_month


def rrn_checksum_ok(digits: str) -> bool:
    """주민등록번호 검증식.

    가중치 [2,3,4,5,6,7,8,9,2,3,4,5]를 앞 12자리에 곱해 합한 뒤,
    (11 - 합 % 11) % 10 이 13번째 자리와 같아야 한다.
    """
    if len(digits) != 13 or not digits.isdigit():
        return False
    weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    total = sum(int(d) * w for d, w in zip(digits[:12], weights))
    return (11 - total % 11) % 10 == int(digits[12])


def luhn_ok(digits: str) -> bool:
    """신용카드 번호 Luhn 검증."""
    if not digits.isdigit() or not 13 <= len(digits) <= 19:
        return False
    total, parity = 0, len(digits) % 2
    for index, char in enumerate(digits):
        value = int(char)
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


# ── 탐지기 ──────────────────────────────────────────────────

class Detector:
    name: str
    category: Category
    default_action: Action
    pattern: re.Pattern

    def validate(self, match: re.Match) -> bool:
        return True

    def find(self, text: str) -> list[Detection]:
        found = []
        for match in self.pattern.finditer(text):
            if not self.validate(match):
                continue
            found.append(Detection(
                detector=self.name,
                category=self.category,
                start=match.start(),
                end=match.end(),
                matched=match.group(0),
                action=self.default_action,
            ))
        return found


class ResidentRegistrationNumber(Detector):
    """주민등록번호. 개인정보 보호법 제24조의2에 따라 처리가 원칙적으로 제한된다."""

    name = "resident_registration_number"
    category = Category.UNIQUE_ID
    default_action = Action.BLOCK
    pattern = re.compile(r"(?<![0-9])(\d{6})[-\s]?([1-4]\d{6})(?![0-9])")

    def validate(self, match: re.Match) -> bool:
        front, back = match.group(1), match.group(2)
        return _valid_birth(front, back[0]) and rrn_checksum_ok(front + back)


class ForeignerRegistrationNumber(Detector):
    """외국인등록번호. 성별코드가 5~8이다.

    ⚠️ 검증식을 적용하지 않는다. 2020년 이후 발급분의 검증식 적용 여부를
    확인하지 못했다(U-13). 확인 전까지 **형식만으로 판단**하며, 그만큼
    오탐 가능성이 주민등록번호보다 높다는 점을 인지하고 사용해야 한다.
    """

    name = "foreigner_registration_number"
    category = Category.UNIQUE_ID
    default_action = Action.BLOCK
    pattern = re.compile(r"(?<![0-9])(\d{6})[-\s]?([5-8]\d{6})(?![0-9])")

    def validate(self, match: re.Match) -> bool:
        return _valid_birth(match.group(1), "1")   # 생년월일 형식만 확인


class CreditCardNumber(Detector):
    name = "credit_card_number"
    category = Category.FINANCIAL
    default_action = Action.BLOCK
    pattern = re.compile(r"(?<![0-9])(?:\d{4}[-\s]?){3}\d{4}(?![0-9])")

    def validate(self, match: re.Match) -> bool:
        return luhn_ok(re.sub(r"[-\s]", "", match.group(0)))


class KoreanMobileNumber(Detector):
    name = "korean_mobile_number"
    category = Category.CONTACT
    default_action = Action.MASK
    pattern = re.compile(r"(?<![0-9])01[016789][-\s]?\d{3,4}[-\s]?\d{4}(?![0-9])")


class EmailAddress(Detector):
    name = "email_address"
    category = Category.CONTACT
    default_action = Action.MASK
    pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


ALL_DETECTORS: list[Detector] = [
    ResidentRegistrationNumber(),
    ForeignerRegistrationNumber(),
    CreditCardNumber(),
    KoreanMobileNumber(),
    EmailAddress(),
]


def detect(text: str, detectors: list[Detector] | None = None) -> list[Detection]:
    """탐지 결과를 위치순으로 반환한다. 겹치는 구간은 먼저 잡힌 쪽을 남긴다."""
    results: list[Detection] = []
    for detector in detectors if detectors is not None else ALL_DETECTORS:
        results.extend(detector.find(text))

    results.sort(key=lambda d: (d.start, -d.length))
    kept: list[Detection] = []
    for det in results:
        if any(det.start < k.end and k.start < det.end for k in kept):
            continue
        kept.append(det)
    return kept
