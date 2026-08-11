# LLM 사업자 데이터 취급 평가 — Google Gemini API

> **U-01 조사 결과.** As-Is·To-Be 양쪽의 여러 판단이 이 문서에 의존합니다.
> 조사일 2026-08-11.

## 왜 이것부터 확인했는가

`V-02`(Google)를 **위탁(제26조)**으로 볼지 **제3자 제공(제17조)**으로 볼지가
확정되지 않아, 다음이 모두 막혀 있었습니다.

```text
U-01 (이 문서)
  → V-02 관계 확정 → PD-008 처리 근거 확정
                   → DPIA R-06 위험도 산정 → Art.36 사전 협의 판단
```

판단의 갈림길은 하나였습니다 — **Google이 입력을 자기 목적으로 이용하는가.**

## 조사 대상 제품

| | |
|---|---|
| 대상 | **Gemini Developer API** (Google AI Studio 계열) |
| 엔드포인트 | `generativelanguage.googleapis.com` |
| 제외 | Vertex AI / Gemini Enterprise Agent Platform (`aiplatform.googleapis.com`), Gemini 앱(소비자용) |

약관 본문도 *"these Terms do not govern your direct use of any Google Cloud Platform service"*
라며 GCP와 선을 긋습니다. **세 제품은 약관이 다르므로 결론을 서로 옮기면 안 됩니다.**

## 확인한 문서

| 문서 | 최종 수정·시행일 |
|---|---|
| [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms?hl=en) | 시행 2026-03-23 / 갱신 2026-04-28 |
| [Abuse monitoring](https://ai.google.dev/gemini-api/docs/usage-policies?hl=en) | 2026-06-09 |
| [Logs policy](https://ai.google.dev/gemini-api/docs/logs-policy?hl=en) | 2026-07-09 |
| [Zero data retention](https://ai.google.dev/gemini-api/docs/zdr?hl=en) | 2026-05-28 |
| [Google Data Processing Addendum (Processor)](https://business.safety.google/processorterms/) | Version 10, 2026-05-07 |
| [Data Processing Services 목록](https://business.safety.google/services/) | — |
| [Google APIs Terms of Service](https://developers.google.com/terms?hl=en) | 2021-11-09 |

> ⚠️ **한국어판을 근거로 쓰지 마세요.** `ai.google.dev/gemini-api/terms`의 한국어
> 로컬라이즈판과 영문 원문(`?hl=en`)은 **같은 갱신일(2026-04-28)로 표시되지만 내용이
> 다릅니다.** 특히 **Paid Services의 정의 자체가 다릅니다.** 이 문서는 전부 영문 원문
> 기준입니다. (**U-16**)

---

## 1. 티어 판정 기준

**결제 계정 연결 여부가 데이터 취급의 실질적 스위치입니다.**

| 상태 | 티어 |
|---|---|
| API 키만 발급받아 **무료 quota**로 호출 | **무료** (Unpaid Services) |
| **활성 결제 계정이 연결된 Cloud 프로젝트**를 통해 API 접근 | **유료** (Paid Services) |

> Google AI Studio는 별도 특칙이 있습니다 — 무상 제공이라도 사용 계정이 활성 Cloud
> Billing 계정이 연결된 프로젝트에 접근 권한이 있거나 Workspace 엔터프라이즈 계정이면
> Paid Service로 봅니다.

---

## 2. 티어별 데이터 취급 — 핵심 대조

| 항목 | 무료 (Unpaid) | 유료 (Paid) |
|---|---|---|
| **제품·모델 개선에 이용** | **예** — 제출 콘텐츠와 생성 응답을 Google 제품·서비스·머신러닝 기술의 제공·개선·개발에 사용. 엔터프라이즈 기능 포함 | **아니오** (기본값) |
| **품질·개선 목적 인적 검토** | **예** — 검토자가 API 입출력을 읽고 주석·처리. 검토 전 계정·API 키·프로젝트와 연결 해제 | 해당 조항 없음 |
| **Google의 지위** | 처리자 아님 | **처리자 (processor)** |
| **DPA (Art.28 처리자 계약)** | **없음** | **있음** |
| **SCC 편입** | 없음 | 조건부 편입 |
| **약관의 지시** | *"Do not submit sensitive, confidential, or personal information to the Unpaid Services."* | — |
| **콘텐츠 라이선스** | Google APIs ToS의 영구·취소불가·전세계·무상 라이선스가 제출 콘텐츠와 생성 응답까지 확장 | — |

### 2.1 유료 티어의 예외 — 무조건적 보장이 아닙니다

**독립 검증 두 건이 모두 지적한 사항이며, 1차 조사는 놓쳤던 부분입니다.**

유료 프로젝트라도 개발자가 **로그를 데이터셋으로 Google에 공유하기로 옵트인**하면,
해당 데이터는 명시적으로 **`Unpaid Services` 약관에 따라 처리**되어 모델 학습에
사용됩니다([logs-policy](https://ai.google.dev/gemini-api/docs/logs-policy?hl=en)).

> 따라서 컴플라이언스 문서에 *"유료 티어는 학습에 사용되지 않는다"* 라고만 쓰면
> 부정확합니다. **"기본 설정에서는 사용되지 않으며, 데이터셋 공유를 옵트인하지 않는 것이
> 전제"** 로 써야 합니다.

### 2.2 유료 티어라도 Google이 **독립 컨트롤러**인 데이터가 있습니다

프롬프트·응답에 대해서는 Google이 처리자이지만, **서비스 운영 과정의 '기타 데이터'** 는
`Google Controller-Controller Data Protection Terms`가 적용되어 **양 당사자가 각자
독립 컨트롤러**입니다.

해당 데이터: 계정 정보·설정, 과금 이력, 직접 커뮤니케이션·피드백, 사용 상세
(프롬프트/응답별 토큰 수, 운영 상태, 안전 필터 발동, 오류·크래시 리포트, 인증 정보,
품질·성능 지표, **기기 식별자·쿠키/토큰 식별자·IP 주소** 포함).

> **이 데이터에는 Art.28 처리자 통제(지시 구속, 삭제 지시권 등)가 적용되지 않습니다.**
> 인벤토리와 DPIA에서 프롬프트·응답과 **분리해 기술해야 합니다.**

### 2.3 남용 모니터링 — 티어 공통

프롬프트·맥락 정보·출력을 **55일 보관**합니다. 정책 집행·위반 방지 목적으로만 사용되며,
정책 집행 전용 모델 외의 AI/ML 모델 학습·미세조정에는 사용하지 않는다고 명시합니다.
인가된 Google 직원의 제한적 인적 검토가 있습니다.

**무료 티어의 '품질·제품 개선 목적 인적 검토'와는 목적이 다른 별개 항목입니다.**

---

## 3. 유료 티어의 DPA — 어느 문서인가

**흔한 오해를 하나 걷어냈습니다.** Gemini Developer API에 적용되는 DPA는
Google Cloud의 **CDPA가 아닙니다.**

| | |
|---|---|
| 적용 DPA | **Google Data Processing Addendum for Products Where Google is a Data Processor** (Version 10, 2026-05-07) |
| URL | `business.safety.google/processorterms/` |
| 적용 서비스 등재 | [Data Processing Services 목록](https://business.safety.google/services/)에 **`Gemini API Paid Services`** 로 등재. 처리 대상은 *"제출된 프롬프트 및 그에 대한 응답에서 처리되는 개인정보"* |
| 적용 안 되는 것 | `cloud.google.com/terms/data-processing-addendum`(CDPA)는 약관 어디에서도 링크되지 않음 |

**서비스명이 `Paid Services`로 한정되어 있다는 점이 결정적입니다.** 무료 quota는 이
목록에 없습니다.

Art.28(3) 요건 항목(처리의 대상·기간·성격·목적, 지시 구속과 위법 지시 통지, 기밀유지,
보안조치, 하위처리자 통제와 사전 이의권, 종료 시 삭제, 감사권, 정보주체 권리행사 지원)이
모두 담겨 있음을 확인했습니다.

**SCC**는 Appendix 3A §7에 조건부 편입되어 있으며, 적정국 이전에는 SCC를 요구하지 않고
`Restricted European Transfer` 발생 시 Data Transfer Solution(EU-US DPF 등) 또는 SCC가
역할별로 적용되는 구조입니다.

---

## 4. 유럽 특칙 — 두 가지

**① 이용 제한 (약관 위반이 될 수 있는 지점)**

> EEA·스위스·영국 이용자에게 API Client를 제공할 때는 **유료 서비스만 사용할 수 있습니다.**

즉 **유럽 이용자를 대상으로 무료 quota를 쓰는 것은 약관 위반**입니다.

**② 데이터 이용**

EEA·스위스·영국에 소재한 이용자에게는 무상 제공이더라도 `Paid Services`의
데이터 취급 조항이 적용됩니다. 따라서 유럽 이용자의 프롬프트는 무료 quota라도
제품 개선에 사용되지 않는 것으로 읽힙니다.

> **①과 ②는 별개입니다.** ②가 데이터 취급을 완화한다고 해서 ①의 이용 제한이
> 사라지지는 않습니다.

---

## 5. 데이터 처리 위치

| | Gemini Developer API | Gemini Enterprise Agent Platform (구 Vertex AI) |
|---|---|---|
| 리전 지정 | **불가** — 리전 파라미터·리전별 엔드포인트·데이터 상주 보장을 제시하는 공식 문서가 확인되지 않음 | **가능** — 저장 위치(at rest)와 ML 처리 위치(in use)를 분리 통제 |
| 약관상 위치 | 유료 조항에 *"어느 나라에서든"* 일시 저장·캐시될 수 있다고 명시 | 관할권 멀티리전(`us`, `eu`), 위치별(`us-central1`, `europe-west9` 등), 글로벌의 3종 |
| EU 상주 | — | EU 멀티리전 엔드포인트 `aiplatform.eu.rep.googleapis.com` |

**주의 세 가지**

- `available-regions` 페이지의 "리전"은 **서비스 이용 가능 국가**이지 데이터 처리 위치가 아닙니다. 혼동하면 안 됩니다
- Agent Platform이라도 **글로벌 엔드포인트를 쓰면 데이터 상주가 보장되지 않습니다.** 엔드포인트 선택이 곧 통제입니다
- **EU 멀티리전은 영국·스위스를 포함하지 않습니다.** 영국 데이터는 `europe-west2`를 별도로 써야 합니다

---

## 6. 판정

### As-Is (무료 티어) — Google은 처리자 지위를 부담하지 않습니다

무료 티어에는 **DPA가 없고**, Google이 제출 콘텐츠를 **자기 목적(제품·모델 개선)으로
이용**하며, **품질·개선 목적의 인적 검토**가 있습니다.

수령자가 데이터를 자기 목적으로 이용하는 구조는 **위탁(제26조)으로 구성하기 어렵습니다.**
위탁은 수탁자의 이용 목적이 위탁자의 목적에 종속되는 것을 전제하기 때문입니다.

> 이는 Google 자신의 규정 방식과도 일치합니다 — 약관은 유료 서비스에 대해서만
> *"Data Processing Addendum for Products Where Google is a **Data Processor**"* 를
> 적용한다고 명시합니다.

**다만 최종적인 법적 성격 결정(제17조 제3자 제공 해당 여부)은 법률 판단 영역이며,
이 문서는 그 판단의 근거가 되는 사실관계까지만 확정합니다.**

### To-Be (유료 티어 가정) — 위탁으로 구성 가능. 단 조건부

| 조건 | 필요성 |
|---|---|
| 활성 결제 계정이 연결된 Cloud 프로젝트로 접근 | 티어 요건 |
| **로그 데이터셋 공유를 옵트인하지 않음** | 옵트인 시 무료 약관으로 처리됨 (§2.1) |
| '기타 데이터'는 별도 기술 | Google이 독립 컨트롤러 (§2.2) |
| 55일 남용 모니터링 로그를 인지·기재 | 티어 공통 (§2.3) |

---

## 7. 이 조사가 바꾸는 것

| 대상 | 변경 |
|---|---|
| As-Is 흐름표·인벤토리 | `V-A1` 관계와 무료 티어 사실 반영 |
| **As-Is Finding** | **신규 `F-007`** — 수령자의 자기 목적 이용 및 인적 검토 |
| To-Be 인벤토리 | `V-02` 관계 = 위탁(조건부), DPA 지정, `PD-008` 처리 근거 |
| **DPIA** | **`R-06` 위험도 산정 가능** → §6 Art.36 재판단 |

---

## 미확인

| # | 내용 | 영향 |
|---|---|---|
| **U-16** | `ai.google.dev/gemini-api/terms` 한국어판과 영문판의 내용 불일치 (Paid Services 정의 포함) | 국내 실무에서 어느 판본을 근거로 삼을지 |
| U-17 | 무료 티어에서 제품·개선 목적으로 수집된 데이터의 **보관 기간·삭제 절차** | 어느 문서에서도 확인되지 않음. 55일은 남용 모니터링 로그 한정 |
| U-18 | 유료 티어 약관의 *"a limited period of time"* 의 구체적 기간 | 55일과 같은지 문서가 연결하지 않음 |
| U-19 | 계약 당사자 Google 법인(`cloud.google.com/terms/google-entity`) | **SCC 모듈 판정에 직결** — DPA §7.1(b)가 Google 주소의 적정국 여부로 적용 모듈을 가름 |
| U-20 | 무료 티어 인적 검토 데이터의 검토 후 보관 기간, 연결 해제(de-identification)의 구체적 방식 | 문서에 없음 |

## 변경 이력

| 버전 | 일자 | 내용 |
|---|---|---|
| v0.1 | 2026-08-11 | 최초 조사. 4개 주제 병렬 확인 + 독립 검증 2건. |
