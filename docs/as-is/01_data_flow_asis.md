# INCANT 개인정보 흐름표 — As-Is

> **As-Is 문서**입니다. 실제 코드에 존재하는 처리만 기록하며, 가정·추정을 섞지 않습니다.
> 상용화를 가정한 분석은 `docs/to-be/` 로 분리합니다.

## 문서 정보

| 항목 | 내용 |
|---|---|
| 대상 시스템 | INCANT (웹 브라우저 로그라이크 게임) |
| 대상 저장소 | `jaepaly/NHN-Project` |
| **고정 커밋** | `852bbd544133f840d972cfc667d17a16618d10db` (2026-08-09 21:32 KST, `main`) |
| 배포 URL | `https://jaepaly.github.io/NHN-Project/` |
| 분석 기준일 | 2026-08-10 |
| 문서 버전 | v0.1 (초안) |

**커밋을 고정하는 이유**: 증적은 시점이 고정되어야 합니다. 브랜치 링크는 코드가 바뀌면 줄 번호가 어긋나 근거가 조용히 사라집니다. 이 문서의 모든 근거 링크는 위 커밋 해시로 고정되어 있습니다.

근거 링크 기준 경로:
`https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/`

## 분석 범위와 한계

- **범위**: 위 커밋 기준으로 프로덕션 빌드에서 실제로 실행되는 처리만.
- **제외**: 개발 모드 전용 처리는 §6에 별도로 확인 결과를 남기고 본 흐름표에서 제외.
- **한계**: 외부 사업자(Google, Cloudflare, GitHub) 내부의 로그 보관·이용 정책은 코드로 확인할 수 없습니다. §7에 미확인 항목으로 명시했습니다.
- INCANT은 해커톤 사전과제 제출작이며 상용 서비스가 아닙니다. 본 문서는 **학습·포트폴리오 목적의 자체 분석**이며 법률 자문이 아닙니다.
- 프록시 운영 계정을 식별할 수 있는 하위 도메인 문자열은 의도적으로 마스킹했습니다.

---

## 1. 대상 시스템 개요

INCANT은 이용자가 **자유 텍스트로 입력한 문장**을 LLM이 판정해 게임 효과로 변환하는 브라우저 게임입니다.

없는 것:
- 회원가입·로그인·계정 없음
- 결제 없음
- 고객센터·문의 채널 없음
- **서버측 이용자 데이터베이스 없음** — 게임 상태는 전부 이용자 단말에 저장

있는 것:
- **이용자가 입력한 문장을 외부 LLM(Google Gemini)으로 실시간 전송**
- 이용자 입력 원문을 단말에 영구 저장
- 프록시에서 접속 IP 처리(레이트리밋)

즉 전형적인 "회원 DB형" 서비스가 아니라, **자유 텍스트가 외부 AI로 흘러가는 구조**가 개인정보 관점의 핵심입니다.

## 2. 시스템 구성

```text
이용자 브라우저
   │
   ├─(a) 정적 자산 요청 ───────────────→ GitHub Pages (GitHub Inc., 미국)
   │                                        └ 웹서버 접속 로그 — 사업자 영역, 통제 불가
   │
   ├─(b) 게임 상태 저장 ───────────────→ 이용자 단말 localStorage (키 8종)
   │                                        └ 만료·삭제 기능 없음
   │
   └─(c) 주문 판정 / 보스 대사 / 작명 ─→ Cloudflare Worker 프록시
                                            incant-judge-proxy.<팀원 개인 계정>.workers.dev
                                            │  └ CF-Connecting-IP 로 분당 15회 레이트리밋
                                            ↓
                                          Google Gemini API (미국)
                                          generativelanguage.googleapis.com
```

**주목할 구성상 특징**: 판정 프록시가 조직 계정이 아닌 **팀원 개인 Cloudflare 계정**에서 운영됩니다. 접근 권한·로그 보관 설정·계정 회수 절차가 정의되어 있지 않습니다.

---

## 3. 개인정보 흐름표

`P` = 이용자 입력에서 직접 파생된 항목 / `T` = 기술적 식별 정보 / `B` = 행태 정보

| ID | 데이터 항목 | 유형 | 수집 경로 | 저장 위치 | 외부 전송 | 처리 목적 | 보유기간 | 삭제 수단 | 근거 |
|---|---|---|---|---|---|---|---|---|---|
| A-01 | **주문 입력 원문** (자유 텍스트, 60자 절단) | P | 게임 내 영창 입력창 | 미저장(프록시) | **Google (미국)** | 주문 의미 판정 | 미정의 | 없음 | [geminiJudge.ts#L192](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/geminiJudge.ts#L192) · [worker.js#L421](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L421) |
| A-02 | 필살기 공명 정보 (원소·형태·**최근 주문명**) | P·B | 이전 주문 이력에서 파생 | 미저장(프록시) | **Google (미국)** | 필살 영창 문맥 제공 | 미정의 | 없음 | [worker.js#L175](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L175) |
| A-03 | 런 전적 요약 (사망/클리어 횟수, 애용 원소, **최고 주문명**, 최근 결과) | B·P | 누적 플레이 기록 | 미저장(프록시) | **Google (미국)** | 보스 도발 대사 생성 | 미정의 | 없음 | [bossLine.ts#L41-L49](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/bossLine.ts#L41-L49) · [worker.js#L301](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L301) |
| A-04 | 진화·융합 작명 요청 (기존 주문명, 원소) | P | 주문 진화 시점 | 미저장(프록시) | **Google (미국)** | 격상 주문 작명 | 미정의 | 없음 | [evolveName.ts#L113](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/evolveName.ts#L113) · [worker.js#L355](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L355) |
| A-05 | **접속 IP 주소** (`CF-Connecting-IP`) | T | HTTP 요청 헤더 | 프록시 인메모리 Map | 없음 | 분당 15회 레이트리밋 | 60초 슬라이딩 윈도우(사실상) | 없음 | [worker.js#L400](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L400) · [worker.js#L273-L280](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L273-L280) |
| B-01 | **주문 입력 원문** (`rawText`) + 정규화 문자열 | P | 영창 입력창 | 단말 localStorage | 없음 | 주문서(그리모어) 재사용 | **무기한** | 없음 | [grimoire.ts#L30-L44](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/grimoire.ts#L30-L44) |
| B-02 | 판정 결과 메타 (주문명·원소·형태·위력·승패·기록시각) | B | 판정 결과 | 단말 localStorage | 없음 | 주문서 관리 | **무기한** | 없음 | [grimoire.ts#L30-L44](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/grimoire.ts#L30-L44) |
| B-03 | 메타 진행도 (통찰·토큰·발견 시그니처·계약 이수·최고 깊이·총 런/승수) | B | 플레이 누적 | 단말 localStorage | 없음 | 런 간 성장 계승 | **무기한** | 없음 | [metaProfile.ts#L8-L21](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/meta/metaProfile.ts#L8-L21) |
| B-04 | **행태 프로파일** (사망/클리어 수, 애용 원소·형태, 최고 주문명, 이동거리·수동시전 횟수 등) | B·P | 플레이 누적 | 단말 localStorage | A-03 경유 일부 전송 | 보스 "기억" 연출 | **무기한** | 없음 | [runMemory.ts#L36-L55](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/runMemory.ts#L36-L55) |
| B-05 | 도감·설정·온보딩 플래그 | B | 플레이·설정 변경 | 단말 localStorage | 없음 | 진행 상태 유지 | **무기한** | 없음 | 키 목록 §5 |
| C-01 | 웹서버 접속 로그 (IP·UA 등) | T | 페이지 접속 | GitHub Pages | — (호스팅 사업자 내부) | 호스팅 운영 | 확인 불가 | 없음 | [deploy.yml](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/.github/workflows/deploy.yml) |

> **A-05 보유기간 주의**: 코드상 60초 윈도우 밖 항목은 필터링되지만, 해당 IP로 재요청이 없으면 Map 엔트리 자체는 워커 인스턴스가 살아있는 동안 남습니다([worker.js#L273-L280](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L273-L280)). "60초 후 삭제"로 단정할 수 없어 *사실상*으로 표기했습니다.

---

## 4. 상세 — 외부 전송 (Google Gemini)

세 경로 모두 프록시를 거쳐 `generativelanguage.googleapis.com` 으로 나갑니다
([worker.js#L23-L26](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L23-L26)).

### 4.1 주문 판정 — `POST /`

클라이언트가 보내는 것:
```json
{ "text": "<이용자 입력 원문>", "castMode": "normal|ultimate", "resonance": { ... } }
```
[geminiJudge.ts#L192-L196](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/geminiJudge.ts#L192-L196)

프록시는 `text`를 60자로 절단한 뒤 판정 프롬프트에 붙여 Gemini로 전송합니다
([worker.js#L421](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L421),
[worker.js#L484](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L484)).

**이 경로가 개인정보 관점에서 가장 중요합니다.** 입력이 자유 텍스트이므로 무엇이 들어올지 사전에 통제할 수 없습니다. 이용자가 자신의 이름·소속·감정 상태·건강 상태·종교적 표현을 문장에 담는 것을 막는 장치가 없고, 담긴 내용은 그대로 국외 사업자에게 전송됩니다.

현재 존재하는 입력 필터는 개인정보 목적이 아닙니다:
- 60자 절단 — 토큰 비용·응답 지연 목적
- 무의미 입력 판별(`isObviousNonsense`) — 게임 판정 품질 목적 ([worker.js#L34-L39](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L34-L39))
- `blocked` 판정(욕설·혐오) — 콘텐츠 안전 목적이며, **판정은 이미 전송된 후** 모델이 수행

즉 **전송 전 개인정보 탐지·차단은 존재하지 않습니다.**

### 4.2 보스 대사 — `POST /boss-line`

```json
{ "deaths": 0, "clears": 0, "favoriteElement": null, "topSpellName": null, "lastResult": null }
```
[bossLine.ts#L41-L49](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/bossLine.ts#L41-L49)

`topSpellName`은 이용자가 입력한 문장에서 파생된 값이므로, 입력 원문의 일부가 이 경로로도 국외 전송됩니다.

### 4.3 진화·융합 작명 — `POST /evolve-name`

기존 주문명과 원소 정보를 전송합니다
([evolveName.ts#L113](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/evolveName.ts#L113)).
주문명 역시 이용자 입력 파생입니다.

### 4.4 IP 처리

`CF-Connecting-IP` 헤더를 읽어 분당 15회 제한에 사용하며, 인메모리 `Map`에 요청 시각 배열로 보관합니다
([worker.js#L30-L31](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L30-L31),
[worker.js#L400-L406](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/proxy/worker.js#L400-L406)).
Gemini로는 전송되지 않습니다.

---

## 5. 상세 — 단말 저장 (localStorage)

| 키 | 내용 | 이용자 입력 원문 포함 |
|---|---|---|
| `incant:grimoire:v1:entries` | 주문서 항목 — `rawText`, `normalized`, 주문명, 원소, 형태, 위력, 승패, 기록시각 | **예** |
| `incant:grimoire:v1:last-legacy` | 직전 계승 주문 | **예** |
| `incant:runmemory:v1:profile` | 사망·클리어 수, 애용 원소·형태, 최고 주문명/위력, 최근 결과, 저주 행동 통계 | **예**(주문명) |
| `incant:meta:v1` | 통찰, 주문 토큰, 토큰 판매 이력, 발견 시그니처, 계약 이수, 최고 깊이, 총 런/승수 | 아니오 |
| `incant:codex:v1` | 주문 도감 | 부분 |
| `incant:settings:v1` | 게임 설정 | 아니오 |
| `incant:onboarded:v1` / `incant:tutorial:v1` | 온보딩·튜토리얼 완료 플래그 | 아니오 |
| `incant.audio.muted` | 음소거 상태 | 아니오 |

**확인 결과: 저장 데이터를 삭제하는 기능이 코드에 존재하지 않습니다.**
저장소 전체에서 `localStorage.removeItem` 호출이 0건이며, 게임 내 데이터 초기화 UI도 없습니다. 이용자가 자신의 입력 이력을 지우려면 브라우저 개발자도구나 사이트 데이터 삭제 기능을 직접 사용해야 합니다.

---

## 6. 프로덕션 미해당 — 확인 완료 항목

코드에는 존재하지만 **프로덕션 빌드에서는 실행되지 않음을 확인**한 처리입니다. 감사 추적을 위해 제외 근거를 남깁니다.

| 처리 | 내용 | 제외 근거 |
|---|---|---|
| `postPlayLog` → `POST /__log` | 플레이 이벤트(입력 텍스트 포함)를 Vite 개발 서버 로거로 전송 | 전 호출부가 `import.meta.env.DEV` 가드 안에 있음 — [playLog.ts#L32](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/playLog.ts#L32), 호출부 6곳 전수 확인 |
| `LoggingJudge` | 판정 입출력을 `logs/play.jsonl`로 기록 | `withDevLogging`이 DEV에서만 래핑 — [createJudge.ts#L44-L53](https://github.com/jaepaly/NHN-Project/blob/852bbd544133f840d972cfc667d17a16618d10db/src/spell/createJudge.ts#L44-L53) |

**제3자 스크립트 없음 확인**: 소스와 `index.html` 전체에서 외부 호스트 참조는 판정 프록시와 자체 도메인 OG 이미지뿐입니다. 분석 도구(GA 등), 광고 SDK, CDN 폰트, 오류 수집 서비스가 **없습니다**.

---

## 7. 현재 통제 상태

| 통제 항목 | 상태 |
|---|---|
| 개인정보 처리방침 | **없음** |
| 수집·이용 동의 절차 | **없음** |
| 국외 이전 고지·동의 | **없음** |
| 처리 목적 정의 | 문서화 없음 (코드 주석 수준) |
| 항목별 보유기간 정의 | **없음** |
| 파기 절차·삭제 수단 | **없음** (§5) |
| 처리위탁 계약(DPA) | **없음** — Google·Cloudflare·GitHub 모두 표준 약관만 |
| 연령 확인 / 법정대리인 동의 | **없음** |
| 전송 전 개인정보 탐지·마스킹 | **없음** (§4.1) |
| 접근 권한 관리 | 프록시가 팀원 개인 계정에서 운영, 권한 정의 없음 |
| 처리 기록·로그 관리 | 정의 없음 |

## 8. 미확인 — 후속 확인 필요

코드만으로 판단할 수 없어 **판단을 보류한** 항목입니다. 추정으로 채우지 않습니다.

| # | 확인 대상 | 필요한 것 |
|---|---|---|
| U-01 | Google Gemini API가 전송된 입력을 얼마나 보관하는지, 모델 학습에 이용하는지 | Google API 약관·데이터 처리 조건 원문 확인 |
| U-02 | Cloudflare Workers의 요청 로그 보관 여부·기간 | 해당 계정 설정 확인 필요 (개인 계정으로 직접 접근 불가) |
| U-03 | GitHub Pages 접속 로그 보관 정책 | GitHub 개인정보 보호정책 확인 |
| U-04 | 워커 인스턴스 수명과 `hits` Map 실제 잔존 시간 | Cloudflare Workers 런타임 동작 문서 확인 |
| U-05 | 프록시 계정 접근 권한 현황 및 회수 절차 | 운영 담당자 확인 |

---

## 9. 다음 단계

1. §7·§8을 입력으로 **KR / EU 룰셋 적용 → Finding 도출** (`docs/as-is/02_findings_asis.md`)
2. 동종 서비스 처리방침 벤치마크 (`docs/to-be/`) — To-Be 인벤토리의 근거 확보
3. 통제 참조 구현 — 전송 전 개인정보 탐지 모듈 + 테스트 (`tools/`)

---

## 변경 이력

| 버전 | 일자 | 내용 |
|---|---|---|
| v0.1 | 2026-08-10 | 최초 작성. 대상 커밋 `852bbd5` 고정. |
