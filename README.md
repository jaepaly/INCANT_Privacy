# INCANT_Privacy

[![CI](https://github.com/jaepaly/INCANT_Privacy/actions/workflows/ci.yml/badge.svg)](https://github.com/jaepaly/INCANT_Privacy/actions/workflows/ci.yml)

**자유 텍스트를 외부 생성형 AI로 처리하는 게임 서비스의 개인정보 컴플라이언스 진단.**

개인정보 흐름을 식별하고, 국내 개인정보보호법과 GDPR 양 관할에서 리스크를 진단해 통제와 증적으로 연결하는 것을 목표로 합니다.

---

## 배경

해커톤에서 [INCANT](https://github.com/jaepaly/NHN-Project)이라는 게임을 만들었습니다. 이용자가 자유롭게 쓴 문장을 LLM이 판정해 마법으로 바꿔주는 게임입니다.

게임 기능은 구현했지만 개인정보 관련 이슈는 전혀 손대지 않았습니다. 특히 **이용자가 쓴 문장을 그대로 외부 AI로 보내는 구조**라서, 어디까지가 수집이고 어디부터가 국외 이전인지부터 애매했습니다. 그래서 이 서비스를 실제로 운영한다면 무엇을 고려해야 하고 어떤 규제를 검토해야 하는지 개인적으로 정리해보기로 했습니다.

## 이 저장소의 구성 원칙

**As-Is와 To-Be를 물리적으로 분리합니다.** 섞이면 어디까지가 사실이고 어디부터가 가정인지 알 수 없게 됩니다.

| | As-Is | To-Be |
|---|---|---|
| 대상 | 실제 배포된 INCANT | 상용 서비스로 확장한 경우 |
| 근거 | 실제 코드 — **커밋 해시로 고정된 permalink** | 실제 게임사 개인정보 처리방침 벤치마크 |
| 성격 | 사실 | 가정 (근거 있는) |
| 검증 | 저장소에서 직접 확인 가능 | 출처 문서로 확인 가능 |

**가정을 지어내지 않습니다.** To-Be의 수집 항목·보유기간·수탁사는 상상으로 채우지 않고, 글로벌 서비스 중인 게임사의 한국어 처리방침과 EU/영문 처리방침을 비교해 도출합니다.

**스키마를 먼저, 룰을 나중에 씁니다.** 순서를 지켜야 합니다. 룰을 먼저 쓰고 대상을 나중에 만들면 내가 판 구덩이를 내가 찾는 자가채점이 됩니다. 스키마는 벤치마크에서, 룰은 법조문에서 각각 독립적으로 도출합니다.

## 관할

**국내 개인정보보호법 + GDPR** 이중 관할로 검토합니다. 게임을 스토어에 올리면 EU 이용자는 자동으로 유입되므로, 글로벌 서비스는 예외가 아니라 기본값입니다.

룰 모델에 `jurisdiction` 축을 두고 같은 인벤토리에 두 룰셋을 적용해, **"국내 기준 통과 / EU 기준 위반"** 구간을 갭으로 도출합니다.

깊이 있게 다루는 논점:

- 처리 근거 구조의 차이 — 동의 중심 vs 6개 근거 선택
- **자유 텍스트를 통한 특별 범주 정보의 비의도적 수집** ← 이 서비스의 핵심 논점
- 국제 이전 연쇄 — EU 이용자 → 국내 서비스 → 미국 LLM 사업자로의 재이전
- 자유 텍스트 × 생성형 AI 구조에 대한 영향평가(DPIA)

## 진행 상황

- [x] As-Is 개인정보 흐름표 — [docs/as-is/01_data_flow_asis.md](docs/as-is/01_data_flow_asis.md)
- [x] 컴플라이언스 룰 카탈로그 v0.2 — [rules/CATALOG.md](rules/CATALOG.md) · 6개 영역 12룰 (KR 6 / EU 6)
- [x] 근거 조문 원문 검증 24/24 — [rules/VERIFICATION_LOG.md](rules/VERIFICATION_LOG.md) · 정정 2건, 판단 보류 2건
- [ ] 판단 보류분 확인 — EDPB Guidelines 3/2018 원문, 한국 적정성 결정의 재이전 커버 범위
- [x] As-Is Finding 도출 — [docs/as-is/02_findings_asis.md](docs/as-is/02_findings_asis.md) · Finding 6건 (CRITICAL 1 / HIGH 3 / MEDIUM 2)
- [x] 동종 서비스 처리방침 벤치마크 — [docs/to-be/01_policy_benchmark.md](docs/to-be/01_policy_benchmark.md) · 6개사 12개 문서 (KR판 vs 글로벌판)
- [x] To-Be 서비스 모델 — [docs/to-be/02_service_model.md](docs/to-be/02_service_model.md)
- [x] To-Be 개인정보 인벤토리 — [docs/to-be/03_data_inventory.md](docs/to-be/03_data_inventory.md) · 25개 항목 (원본 `inventory/incant_tobe.yaml`)
- [ ] 처리대장 (Processing Register)
- [x] **룰 엔진 구현** — [reports/](reports/) · 룰 12개를 As-Is·To-Be 인벤토리에 적용 (후보 As-Is 38 / To-Be 68건)
- [ ] 룰 확장 — 처리근거·처리위탁·안전조치·영향평가 영역
- [ ] 리스크 평가 및 대시보드
- [x] **통제 참조 구현** — [controls/](controls/) · `CTRL-001` 전송 전 개인정보 필터 (테스트 35건 통과)
- [ ] DPIA
- [ ] 최종 리포트

## 저장소 구조

```text
docs/
  as-is/            실제 코드 기반 분석 (근거: permalink)
  to-be/            상용화 가정 분석 (근거: 처리방침 벤치마크)
rules/
  kr.yaml               국내 개인정보 보호법 룰 — 원본
  eu.yaml               GDPR 룰 — 원본
  CATALOG.md            사람이 읽는 카탈로그 — 생성물
  README.md             룰 스키마·ID 체계·작성 규칙
  VERIFICATION_LOG.md   근거 조문 검증 기록
inventory/
  incant_asis.yaml      As-Is 인벤토리 — 룰 엔진 입력 전용 (정본은 docs/as-is/)
  incant_tobe.yaml      To-Be 개인정보 인벤토리 — 원본
  README.md             인벤토리 스키마·룰 엔진과의 대응 관계
controls/
  pii_filter/           CTRL-001 전송 전 개인정보 필터 — 통제 참조 구현
  README.md             Risk -> Control -> Evidence 매핑
tests/                  통제 증적
tools/
  render_rules.py       rules/*.yaml -> CATALOG.md
  render_inventory.py   inventory/*.yaml -> 03_data_inventory.md
  run_rules.py          룰 엔진 — 룰을 인벤토리에 적용
reports/                룰 적용 결과 (생성물)
```

원본(YAML)만 고치고 문서는 다시 생성합니다.

```bash
python tools/render_rules.py && python tools/render_inventory.py && python tools/run_rules.py
python -m pytest              # 통제 증적
```

**엔진이 내는 것은 Finding 후보입니다.** 위험도 산정·리스크 시나리오·개선 우선순위는
인벤토리에 없는 맥락 판단이므로 사람이 붙입니다 — [reports/README.md](reports/README.md).

## CI

산출물이 대부분 생성물이라 원본과 어긋나기 쉽습니다. `--check`가 그 규율을 강제하고,
통제 테스트가 "동작함을 입증했다"는 주장을 지탱합니다. 매 실행마다 현재 룰 수·미검증
조문 수·Finding 후보 수를 작업 요약에 남깁니다.

```bash
python tools/render_rules.py --check
python tools/render_inventory.py --check
python tools/run_rules.py --check
python -m pytest
python tools/ci_summary.py    # 현재 상태 요약
```

## 원칙

- **조문은 원문으로 확인합니다.** 각 룰에 근거 조문·확인일자·실제로 읽은 출처 URL을 병기합니다. 교차검증에 다른 모델을 쓰되, **모델 합의는 원문을 대체하지 않습니다** — 실제로 한 모델이 확신도 "높음"으로 틀린 조문 내용을 답한 사례가 있습니다([검증 기록](rules/VERIFICATION_LOG.md)).
- **판단을 보류한 것은 보류했다고 씁니다.** 코드나 공개 문서로 확인할 수 없는 항목은 추정으로 채우지 않고 "미확인"으로 남깁니다.
- **이 저장소에는 실제 개인정보를 두지 않습니다.** 샘플 데이터는 전부 합성이며, 특정 개인을 식별할 수 있는 정보는 마스킹합니다.

## 고지

본 저장소의 문서는 **학습 및 포트폴리오 목적의 자체 분석**이며 법률 자문이 아닙니다. 법 해석에 오류가 있을 수 있으며, 실제 컴플라이언스 판단에 그대로 사용해서는 안 됩니다.

분석 대상인 INCANT은 해커톤 사전과제 제출작으로 상용 서비스가 아닙니다. As-Is 분석은 제출 시점 코드(`852bbd5`)를 대상으로 한 기술적 사실 기록이며, 특정 개인이나 팀의 과실을 지적하기 위한 것이 아닙니다.

## 라이선스

- 코드: [MIT](LICENSE)
- 문서(`docs/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
