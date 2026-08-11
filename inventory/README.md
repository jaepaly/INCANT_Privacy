# 개인정보 인벤토리

## 왜 YAML인가

인벤토리를 문서로만 관리하면 **룰 엔진이 읽을 수 없고**, YAML로만 두면 사람이 읽지
않습니다. 원본은 YAML 하나로 두고 사람이 읽는 문서는 생성합니다.

| 파일 | 역할 |
|---|---|
| `incant_tobe.yaml` | INCANT 상용화 가정 인벤토리 — **원본** |
| `../docs/to-be/03_data_inventory.md` | 사람이 읽는 인벤토리 — **생성물. 직접 수정 금지** |

```bash
python tools/render_inventory.py           # 생성
python tools/render_inventory.py --check   # 검증만 (CI용)
```

## 룰 엔진과의 관계

**이 스키마는 룰의 `check_expr`가 참조하는 대상입니다.**

`rules/*.yaml`의 `check_expr`는 현재 실행되지 않는 초안 표현식입니다. 실행되지 않는
이유가 "평가 데이터 모델이 없어서"였고, 이 인벤토리가 그 데이터 모델입니다.

| 룰의 참조 | 인벤토리 위치 |
|---|---|
| `service.privacy_policy.url` | `service.privacy_policy_url` |
| `service.age_verification` | `service.age_verification` |
| `service.erasure_mechanism` | `service.erasure_mechanism` |
| `item.retention_period` | `data_items[].retention.period` |
| `item.deletion_procedure` | `data_items[].retention` (파기 절차는 별도 필드 예정) |
| `flow.destination.is_overseas` | `flows[].is_overseas` |
| `flow.transfer_ground` | `flows[].transfer_ground` |
| `channel.input_type` | `channels[].input_type` |
| `channel.pii_prefilter` | `channels[].pii_prefilter` |

일부 필드명이 아직 어긋납니다. **룰 엔진을 구현할 때 양쪽 이름을 맞추는 작업이 선행되어야
합니다.** 지금 억지로 맞추지 않고 어긋난 상태를 기록해 둡니다.

## 스키마

```yaml
service:                      # 서비스 수준 속성 — 룰의 service.* 참조 대상
  jurisdictions: [KR, EU]
  privacy_policy_url: null    # null = 미수립 (룰이 발동)
  ...

systems:   [{id, name, location, country}]
vendors:   [{id, name, relation, task, country, is_overseas, dpa, note}]
channels:  [{id, name, input_type, is_stored, is_transferred, pii_prefilter, ...}]

data_items:
  - id: PD-001
    name:
    activity:                 # 처리활동 — 처리대장 생성 시 묶음 단위
    category: 일반 | 고유식별정보 | 민감정보 | 인증정보 | 행태정보
    gdpr_special_category_risk: true   # 선택. 자유 텍스트 채널 경유 항목
    purposes: []
    collected_at:
    channel:                  # 선택. channels[].id
    legal_ground: {kr: , eu: }
    retention:
      period:
      type: 법정 | 정책 | 조건부
      basis:                  # type이 '법정'이면 필수
      verified: true|false    # 근거를 원문으로 확인했는가
    stored_in: [SYS-...]
    vendors: [V-...]
    overseas: []              # 선택
    encrypted:
    note:                     # 선택

flows:
  - {id, name, from, to, items: [PD-...], type, is_overseas, transfer_ground, disclosure}
```

## 검증 규칙

`render_inventory.py`가 생성 전에 검사합니다. 위반 시 exit 1.

- 필수 필드 존재 (단, 보유기간이 `미보관`인 항목은 `stored_in`이 비어 있어도 됨)
- `category`·`retention.type`의 허용값
- **`retention.type`이 `법정`이면 `basis`(근거 법령·조문) 필수**
- **`retention.verified` 명시 필수** — 누락 불가
- `stored_in`·`vendors`·`channel`·`flows[].items`의 참조 무결성

## `verified` 필드에 대해

룰 카탈로그의 `legal_basis.verification`과 같은 취지입니다.
**보유기간의 근거를 원문으로 확인했는지**를 항목마다 기록합니다.

`verified: false`인 항목은 생성 문서의 §5에 별도 집계되며 표에 ⚠️ 로 표시됩니다.
확정 근거로 사용하지 않습니다.

현재 `false`인 항목은 접속 관련 2건입니다 — 통신비밀보호법을 근거로 인용하는 것이
업계 관행이나, 제15조의2가 "전기통신사업자의 협조의무"이며 게임 사업자 적용 여부가
별도 판단 대상이기 때문입니다 (U-12).
