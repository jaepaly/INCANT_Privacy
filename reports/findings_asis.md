# 룰 적용 결과 — As-Is (실제 배포 데모)

> **생성물입니다. 직접 수정하지 마세요.**
> `python tools/run_rules.py`로 생성됩니다.

> **이것은 Finding 후보입니다.** 엔진은 룰의 술어가 인벤토리에서 참이 되는
> 지점만 기계적으로 찾습니다. 위험도 산정·리스크 시나리오·개선 우선순위는
> 인벤토리에 없는 맥락 판단이므로 사람이 붙여야 합니다.

## 요약

- 데이터셋: `asis` — INCANT (실제 배포 데모) (v0.1)
- 적용 관할: KR / **조건부** EU
- 평가한 룰 **12개** 중 **12개 발동**, 0개 미발동
- Finding 후보 **38건**

| 기본 심각도 | 후보 수 | 발동 룰 |
|---|---|---|
| CRITICAL | 4 | `EU-TRF-001` |
| HIGH | 30 | `EU-RET-001`, `EU-SPC-001`, `EU-TRP-001`, `KR-RET-001`, `KR-SPC-001`, `KR-TRF-001`, `KR-TRP-001` |
| MEDIUM | 4 | `EU-AGE-001`, `EU-RGT-001`, `KR-AGE-001`, `KR-RGT-001` |

> ⚠️ `EU` 관할 룰의 판정은 **조건부**입니다.
> 해당 관할의 적용 여부 자체가 확정되지 않았습니다. 위반 사실로 기재하지 마세요.

## 발동 룰별 상세

### `EU-TRF-001` 제3국 이전 근거 부재 및 재이전 미검토

국외이전 · EU · 기본 심각도 **CRITICAL** · **조건부** · 대상 4건

근거: GDPR Art.44 · GDPR Art.45 · GDPR Art.46

| 대상 | 발동 사유 |
|---|---|
| `FL-A1` 주문 판정 | `is_overseas` is_true → true / `transfer_mechanism` is_null → null |
| `FL-A2` 보스 대사 생성 | `is_overseas` is_true → true / `transfer_mechanism` is_null → null |
| `FL-A3` 진화·융합 작명 | `is_overseas` is_true → true / `transfer_mechanism` is_null → null |
| `FL-A6` 호스팅 접속로그 | `is_overseas` is_true → true / `transfer_mechanism` is_null → null |

개선 조치:

- Google·Cloudflare·GitHub 각각의 이전 근거 확인 및 문서화
- 데이터 처리 계약(DPA) 및 표준계약조항(SCC) 체결 여부 확인
- 이전 경로 전체를 구간별로 도식화하고 각 구간의 근거 명시

### `EU-RET-001` 보관 기간 제한 원칙 위반

보유·파기 · EU · 기본 심각도 **HIGH** · **조건부** · 대상 11건

근거: GDPR Art.5(1)(e) · GDPR Art.5(2)

| 대상 | 발동 사유 |
|---|---|
| `A-01` 주문 입력 원문 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `A-02` 필살기 공명 정보 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `A-03` 런 전적 요약 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `A-04` 진화·융합 작명 요청 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `A-05` 접속 IP 주소 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `B-01` 주문 입력 원문 (rawText) | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `B-02` 판정 결과 메타 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `B-03` 메타 진행도 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `B-04` 행태 프로파일 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `B-05` 도감·설정·온보딩 플래그 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |
| `C-01` 웹서버 접속 로그 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null / `service.retention_evidence` is_null → null |

개선 조치:

- 목적별 보유기간 산정 근거 문서화
- 자동 파기 구현 및 실행 기록 확보
- accountability 입증 자료 체계 수립

### `EU-SPC-001` 자유 텍스트를 통한 특별범주 정보의 비의도적 처리

특별범주 · EU · 기본 심각도 **HIGH** · **조건부** · 대상 1건

근거: GDPR Art.9(1) · GDPR Art.9(2) · GDPR Art.5(1)(c)

| 대상 | 발동 사유 |
|---|---|
| `CH-A1` 주문 입력창 | `input_type` eq → "free_text" / `special_category_filter` is_null → null / `is_stored` is_true → true / `is_transferred` is_true → true |

개선 조치:

- 전송·저장 전 특별범주 탐지 계층 도입
- 탐지 시 저장 제외 및 전송 차단 정책 적용
- 최소수집 관점에서 자유 텍스트 보관 필요성 재검토

### `EU-TRP-001` 정보주체에 대한 정보 제공 의무 미이행

투명성 · EU · 기본 심각도 **HIGH** · **조건부** · 대상 1건

근거: GDPR Art.12(1) · GDPR Art.13 · GDPR Art.13(2)(a) · WP29 Guidelines (EDPB 승인) — 법령 아님, 유권해석 WP260 rev.01, Annex — Art.13.2(a)/14.2(a) 행 (p.38-39)

| 대상 | 발동 사유 |
|---|---|
| `(서비스 전체)` (서비스 전체) | `privacy_notice_eu` is_null → null |

개선 조치:

- Art.13 요구 항목을 충족하는 privacy notice 작성
- 수집 시점(최초 실행·입력 전)에 접근 가능한 위치에 배치
- 국내 처리방침(제30조 제1항 각 호)과 항목 대조표 작성

### `KR-RET-001` 보유기간 미정의 및 파기 절차 부재

보유·파기 · KR · 기본 심각도 **HIGH** · 대상 11건

근거: 개인정보 보호법 제21조 제1항 · 개인정보 보호법 시행령 제16조

| 대상 | 발동 사유 |
|---|---|
| `A-01` 주문 입력 원문 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `A-02` 필살기 공명 정보 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `A-03` 런 전적 요약 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `A-04` 진화·융합 작명 요청 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `A-05` 접속 IP 주소 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `B-01` 주문 입력 원문 (rawText) | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `B-02` 판정 결과 메타 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `B-03` 메타 진행도 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `B-04` 행태 프로파일 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `B-05` 도감·설정·온보딩 플래그 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |
| `C-01` 웹서버 접속 로그 | `retention.period` is_null → null / `service.deletion_procedure` is_null → null |

개선 조치:

- 항목별 보유기간 정의 및 산정 근거 문서화
- 보유기간 경과 데이터의 자동 파기 구현 — 시행령 제16조의 복원 불가능한 방법
- 파기 실행 기록 확보 방안 수립

### `KR-SPC-001` 자유 텍스트를 통한 민감정보 비의도적 수집·국외전송

특별범주 · KR · 기본 심각도 **HIGH** · 대상 1건

근거: 개인정보 보호법 제23조 제1항

| 대상 | 발동 사유 |
|---|---|
| `CH-A1` 주문 입력창 | `input_type` eq → "free_text" / `pii_prefilter` is_null → null / `is_stored` is_true → true / `is_transferred` is_true → true |

개선 조치:

- 전송 전 개인정보·민감정보 탐지 및 마스킹 계층 도입
- 탐지 시 저장 제외 정책 적용
- 최소수집 관점에서 원문 보관 필요성 자체를 재검토

### `KR-TRF-001` 국외 이전 고지·동의 부재

국외이전 · KR · 기본 심각도 **HIGH** · 대상 4건

근거: 개인정보 보호법 제28조의8 제1항 · 개인정보 보호법 제28조의8 제2항

| 대상 | 발동 사유 |
|---|---|
| `FL-A1` 주문 판정 | `is_overseas` is_true → true / `transfer_ground` is_null → null / `disclosure` is_null → null |
| `FL-A2` 보스 대사 생성 | `is_overseas` is_true → true / `transfer_ground` is_null → null / `disclosure` is_null → null |
| `FL-A3` 진화·융합 작명 | `is_overseas` is_true → true / `transfer_ground` is_null → null / `disclosure` is_null → null |
| `FL-A6` 호스팅 접속로그 | `is_overseas` is_true → true / `transfer_ground` is_null → null / `disclosure` is_null → null |

개선 조치:

- 제28조의8 제1항 각 호 중 어느 근거로 이전하는지 확정
- 제2항 각 호 5개 고지사항을 갖춘 국외 이전 현황표 작성
- 처리방침에 국외 이전 항목 반영 및 이전 거부 방법·절차 제공
- 시행령상 국외 이전 시 보호조치 이행 여부 확인

### `KR-TRP-001` 개인정보 처리방침 미수립·미공개

투명성 · KR · 기본 심각도 **HIGH** · 대상 1건

근거: 개인정보 보호법 제30조 제1항 · 개인정보 보호법 제30조 제2항

| 대상 | 발동 사유 |
|---|---|
| `(서비스 전체)` (서비스 전체) | `privacy_policy_url` is_null → null |

개선 조치:

- 개인정보 처리방침 수립 — 제30조 제1항 각 호의 법정 기재사항 포함
- 게임 타이틀 화면 및 최초 실행 시 상시 접근 가능한 경로 제공
- 처리방침 개정 이력 관리 체계 수립

### `EU-AGE-001` 아동 동의 요건 미충족 및 연령 확인 부재

아동 · EU · 기본 심각도 **MEDIUM** · **조건부** · 대상 1건

근거: GDPR Art.8(1) · GDPR Art.8(2)

| 대상 | 발동 사유 |
|---|---|
| `(서비스 전체)` (서비스 전체) | `child_access_restricted` is_false → false / `age_verification` is_null → null / `age_gate_branching` is_null → null |

개선 조치:

- 회원국별 아동 연령 기준 조사표 작성 (13~16세 범위)
- 관할 판별 후 연령 게이트를 분기하는 구조 설계
- 친권자 동의 확인 방법 검토 — Art.8(2)의 '합리적 노력' 수준 정의

### `EU-RGT-001` 삭제권 행사 수단 부재

정보주체 권리 · EU · 기본 심각도 **MEDIUM** · **조건부** · 대상 1건

근거: GDPR Art.17 · GDPR Art.12(2)

| 대상 | 발동 사유 |
|---|---|
| `(서비스 전체)` (서비스 전체) | `erasure_mechanism` is_null → null / `privacy_contact` is_null → null |

개선 조치:

- 게임 내 데이터 삭제 기능 제공
- privacy notice에 권리 행사 방법 및 연락 창구 명시
- 권리 행사 요청 처리 절차 수립

### `KR-AGE-001` 연령 확인 수단 부재

아동 · KR · 기본 심각도 **MEDIUM** · 대상 1건

근거: 개인정보 보호법 제22조의2 제1항

| 대상 | 발동 사유 |
|---|---|
| `(서비스 전체)` (서비스 전체) | `age_verification` is_null → null / `child_access_restricted` is_false → false |

개선 조치:

- 연령 확인 절차 설계
- 만 14세 미만 식별 시 법정대리인 동의 및 동의 여부 확인 절차 적용
- 아동 대상 고지문 별도 작성

### `KR-RGT-001` 정보주체 권리행사 수단 부재

정보주체 권리 · KR · 기본 심각도 **MEDIUM** · 대상 1건

근거: 개인정보 보호법 제35조 · 개인정보 보호법 제36조 제1항 · 개인정보 보호법 제38조

| 대상 | 발동 사유 |
|---|---|
| `(서비스 전체)` (서비스 전체) | `data_access_ui` is_null → null / `privacy_contact` is_null → null |

개선 조치:

- 게임 내 저장 데이터 열람·삭제 기능 제공
- 처리방침에 권리행사 방법 및 접수 창구 명시

## 미발동 룰

없음 — 평가한 모든 룰이 발동했습니다.

---

룰 카탈로그 `rules/` · 인벤토리 `inventory/incant_asis.yaml`
