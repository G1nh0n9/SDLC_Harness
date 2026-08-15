# Agent Workflow Harness 사용 설명서

## 1. 이 문서의 목적

Agent Workflow Harness는 Hermes에서 소프트웨어 개발 과업을 여러 전문 에이전트에게 나누고, 단계·권한·후보본·증거를 코드로 관리하는 플러그인입니다.

이 설명서는 다음 독자를 대상으로 합니다.

- Hermes 대화창에서 하네스를 사용하는 사람
- 단계별 전문 에이전트 작업을 관리하는 운영자
- 하네스 플러그인을 설치·점검하는 개발자
- 후보본과 검증 자료를 감사하거나 재현하는 검토자

하네스의 핵심 목적은 에이전트가 “완료했다”고 말하는 것과 실제 완료를 구분하는 데 있습니다. 단계 전환은 에이전트의 주장만으로 일어나지 않습니다. 미션 ID, revision, 역할, 작업 ID, 후보본 ID, 증거 상태를 하네스가 확인한 뒤에만 다음 단계로 넘어갑니다.

> **중요:** 시험 통과는 구현된 시험 범위에서 결함을 찾지 못했다는 뜻입니다. 모든 입력에서 완전한 정확성·안전성·연구 타당성을 증명하지 않습니다.

---

## 2. 가장 빠른 사용법

### 2.1 플러그인이 설치된 환경

Hermes를 새로 시작한 뒤 대화창에서 다음과 같이 입력합니다.

```text
/workflow start 이 저장소에 사용자 인증 기능을 추가한다
```

또는 자연어로 요청합니다.

```text
이 저장소에 사용자 인증 기능을 추가해 줘.
Agent Workflow Harness로 목표 점검부터 검토와 출시 판정까지 진행해.
```

자연어 요청을 받은 Hermes는 `workflow_start` 도구를 호출해야 합니다. 첫 응답에는 다음 항목이 포함됩니다.

- `mission_id`: 과업 고유 식별자
- `revision`: 사용자 지시 개정 번호
- `track`: 탐색 경로 또는 제작 경로
- `current_stage`: 현재 단계
- `stages`: 전체 단계와 단계별 역할
- `tasks`: 현재 단계에서 수행할 작업 목록
- `required_assurance_claims`: 연구 산출물에 필요한 별도 검증 항목

### 2.2 상태 조회

```text
/workflow status mis-0123456789abcdef0123456789abcdef
```

또는 Hermes가 다음 도구를 호출하게 합니다.

```text
workflow_status(mission_id="mis-...")
```

### 2.3 사용자 지시 변경

진행 중 목표·범위·우선순위를 바꾸려면 일반 결과 제출보다 먼저 새 지시를 반영해야 합니다.

```text
/workflow revise mis-... 성능보다 정확성을 우선하고 공개 API는 바꾸지 않는다
```

새 지시를 반영하면 revision이 증가하고, 이전 revision의 미완료 작업은 오래된 상태가 됩니다. 이후 도착한 이전 결과는 현재 단계 통과에 쓸 수 없습니다.

---

## 3. Python과 Hermes 플러그인의 관계

하네스는 다음 세 층으로 구성됩니다.

```text
Hermes 대화창·슬래시 명령
        ↓
Hermes 플러그인 도구와 명령
        ↓
Python 핵심 엔진
        ↓
미션 JSON·후보본·SQLite 증거 원장·출시 묶음
```

### Python 핵심 엔진

다음처럼 결과가 항상 같아야 하는 작업을 맡습니다.

- 목표 충분성 판정
- 탐색·제작 경로와 단계 구성
- 단계별 역할 배정
- 미션 ID와 revision 확인
- 작업과 결과의 역할·단계·후보본 일치 확인
- 후보본 해시 계산과 변경 감지
- 증거 원장 기록과 해시 사슬 검증
- 승인·출시 조건 확인

### Hermes 플러그인

Python 핵심 엔진을 Hermes 도구로 노출합니다.

- `workflow_start`
- `workflow_status`
- `workflow_submit_result`
- `workflow_revise`
- `workflow_freeze_candidate`
- `workflow_record_evidence`
- `workflow_approve_candidate`
- `workflow_package_release`
- `/workflow` 슬래시 명령
- `agent-workflow-harness:workflow` 내장 스킬

### 플러그인 내장 스킬

Hermes가 하네스 도구를 어떤 순서로 써야 하는지 설명합니다. 스킬은 절차 안내이며, 상태 전환과 후보본·증거 검사는 Python 코드가 수행합니다.

### 데스크톱 화면 플러그인과의 차이

이 하네스는 Hermes 실행부에 도구와 명령을 추가하는 **일반 Python 플러그인**입니다. 별도 진행 화면이나 상태 패널을 추가하는 데스크톱 화면 플러그인은 현재 범위에 포함하지 않습니다.

---

## 4. 설치와 활성화

## 4.1 요구 환경

- Windows 11 또는 Python 3.11 이상을 실행할 수 있는 환경
- Hermes Agent
- 프로젝트 저장소
- Hermes가 쓰는 Python 환경에 패키지를 설치할 권한

## 4.2 개발 환경 설치

프로젝트 루트에서 실행합니다.

```bash
py -3.11 -m venv .venv
PYTHONPATH='' .venv/Scripts/python.exe -m pip install -e '.[dev]'
```

Hermes 데스크톱에서 상속된 `PYTHONPATH`가 Hermes 자체 패키지 경로를 가리킬 수 있으므로, 프로젝트 시험과 설치 명령에서는 `PYTHONPATH`를 비웁니다.

## 4.3 Hermes 환경에 플러그인 설치

현재 Windows 설치 예시는 다음과 같습니다.

```bash
PYTHONPATH='' \
C:/Users/gimhc/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe \
-m pip install --no-deps -e C:/Users/gimhc/agent-workflow-harness
```

`--no-deps`는 플러그인 설치가 Hermes 공유 Python 환경의 다른 패키지 버전을 임의로 바꾸지 못하게 합니다. 필요한 의존성이 Hermes 환경에 없는 경우에는 먼저 충돌 가능성을 검토해야 합니다.

## 4.4 활성화

```bash
C:/Users/gimhc/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe \
plugins enable agent-workflow-harness
```

도구 덮어쓰기 권한은 필요하지 않습니다. 활성화 과정에서 해당 권한을 묻더라도 허용하지 않아도 됩니다.

활성화 뒤에는 **새 Hermes 세션을 시작하거나 Hermes를 다시 시작**해야 합니다. 이미 열린 대화의 도구 목록은 중간에 바뀌지 않습니다.

## 4.5 설치 확인

```bash
C:/Users/gimhc/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe \
plugins show agent-workflow-harness
```

정상 예:

```text
Status: enabled
Source: entrypoint
Key: agent-workflow-harness
```

프로젝트에는 실제 Hermes 도구 레지스트리를 검사하는 스크립트도 있습니다.

```bash
PYTHONPATH='' \
C:/Users/gimhc/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe \
C:/Users/gimhc/agent-workflow-harness/scripts/verify_plugin_runtime.py
```

이 검사는 다음을 확인합니다.

- 플러그인 진입점 발견
- `agent_workflow` 도구 묶음 등록
- `workflow_start` 처리 함수 호출
- 미션 생성
- 플러그인 내장 스킬 등록

### `plugins doctor` 주의 사항

현재 확인한 Hermes 설치판에서는 pip 진입점 플러그인이 `plugins list`와 실제 런타임에는 잡히지만, `plugins doctor <플러그인 ID>`가 해당 ID를 찾지 못하는 경우가 있습니다. 이때 검사기 실패만으로 플러그인이 로드되지 않았다고 단정하지 않습니다. `plugins show`와 실제 런타임 등록 검사를 함께 봅니다.

---

## 5. 목표 입력 방법

`workflow_start`는 단순한 한 줄 목표 외에 다음 정보를 받을 수 있습니다.

| 필드 | 뜻 | 예 |
|---|---|---|
| `goal` | 달성하려는 목표 | 사용자 인증 기능 추가 |
| `decision_action` | 결과를 보고 내릴 결정 | 배포 여부 결정 |
| `outcome` | 실제로 좋아져야 하는 결과 | 승인된 사용자만 로그인 |
| `population` | 대상 | 서비스 사용자 |
| `analysis_unit` | 판단 단위 | 로그인 시도 한 건 |
| `time_horizon` | 시간 범위 | 다음 출시부터 6개월 |
| `constraints` | 지켜야 할 제약 | 비밀번호 로그 기록 금지 |
| `question_type` | 질문 유형 | implementation, prediction, causal 등 |
| `data_description` | 사용할 자료 | 현재 저장소와 인수 기준 |
| `decision_threshold` | 실제 결정을 바꾸는 기준 | 치명적 보안 결함 0건 |
| `risk_level` | 운영 위험 등급 | 0~3 |
| `research_artifact` | 논문·연구 결과 산출 여부 | true 또는 false |

### 입력이 부족할 때

다음 핵심 항목 가운데 하나라도 없거나 미확인·충돌 상태이면 탐색 경로를 엽니다.

- 의사결정과 행동
- 목표 결과
- 대상
- 분석 단위
- 시간 범위
- 제약
- 질문 유형
- 자료 설명
- 결정 기준

탐색 경로에서는 목표·방법·지표·자료·편향을 검토할 전문 역할을 추가합니다. 입력이 충분한 저위험 구현 과업은 불필요한 탐색 단계를 건너뜁니다.

### 위험 등급

| 등급 | 일반적인 뜻 | 추가 통제 예 |
|---|---|---|
| 0 | 문서·예제 등 영향이 거의 없음 | 기본 검증 |
| 1 | 낮은 위험의 내부 기능 | 독립 검증 |
| 2 | 보안·자료·공개 기능에 영향 | 보안 설계와 독립 검토 강화 |
| 3 | 되돌리기 어렵거나 피해가 큰 변경 | 정형 분석 역할과 강한 승인 분리 |

위험 등급만으로 연구 검증 여부를 대신하지 않습니다. 운영 위험이 낮아도 논문의 핵심 표·그림·수치를 만드는 코드라면 `research_artifact=true`로 지정합니다.

---

## 6. 단계와 역할

입력에 따라 일부 탐색 단계가 추가되거나 전문 역할이 늘어날 수 있습니다. 기본 제작 흐름은 다음과 같습니다.

```text
scope-risk
→ requirements
→ oracle
→ design
→ implementation
→ integration-verification
→ validation
→ release
```

목표가 충분하지 않으면 다음 단계가 앞부분에 추가됩니다.

```text
goal-discovery
→ method-discovery
```

### 주요 단계

| 단계 | 목적 | 대표 역할 |
|---|---|---|
| `scope-risk` | 범위·위험·연구 산출물 여부 판정 | risk-analyst |
| `goal-discovery` | 목표·대상·결정 기준 구체화 | goal-analyst, domain-researcher |
| `method-discovery` | 방법·지표·자료·편향 대안 비교 | methodologist, metric-specialist |
| `requirements` | 원자적 요구와 금지 행위 정리 | requirements-specialist |
| `oracle` | 구현과 독립된 기대 결과 준비 | oracle-specialist |
| `design` | 구조·자료·상태·신뢰 경계 설계 | architecture-specialist 등 |
| `implementation` | 정해진 기준선에 따라 코드 작성 | implementation-specialist |
| `integration-verification` | 후보본을 대상으로 통합 검증 | verification-specialist |
| `validation` | 사용자 목표와 연구 주장의 적합성 검토 | validation-specialist 등 |
| `release` | 승인된 후보본을 출시 묶음으로 고정 | release-specialist |

### 연구 산출물의 여섯 필수 검증 항목

`research_artifact=true`이면 다음 항목이 모두 필요합니다.

1. 방법 타당성
2. 알고리즘 의미 일치
3. 평가지표 타당성
4. 실험 무결성
5. 재현성과 산출물 계보
6. 승인 범위 순수성

한 항목의 통과가 다른 항목의 실패를 상쇄하지 않습니다.

---

## 7. 작업 결과 제출

현재 단계의 `tasks`에는 다음 정보가 있습니다.

```json
{
  "task_id": "task-...",
  "role": "risk-analyst",
  "stage": "scope-risk",
  "revision": 1,
  "candidate_id": null,
  "candidate_snapshot": null,
  "status": "issued",
  "workspace": {
    "work": ".../work",
    "build": ".../build",
    "tmp": ".../tmp",
    "home": ".../home",
    "inputs": ".../inputs"
  },
  "permissions": {
    "tools": ["read-input", "write-result"],
    "writable_areas": ["tmp", "work"],
    "network_allowed": false,
    "can_execute_commands": false,
    "can_approve": false
  }
}
```

작업 응답을 만들 때 역할·revision·작업 ID별 디렉터리를 실제로 생성합니다. `required_inputs`에는 이름만 나열하지 않고 각 입력의 종류·출처·SHA-256을 담은 `input_bindings`를 함께 제공합니다. 구현·오라클·검증·출시 역할만 명령 실행 권한을 받으며, 검증 단계의 역할만 승인 권한을 받습니다. 후보본을 동결한 뒤 발급한 작업에는 `candidate_snapshot` 읽기 경로가 붙습니다.

플러그인의 권한 정보는 Hermes가 하위 작업을 실행할 때 반드시 적용해야 하는 허용 목록입니다. 이 목록을 프롬프트 설명으로만 전달해서는 안 됩니다. 하네스 실행기는 `can_execute_commands=false`인 역할의 프로세스 실행을 거부하고, 작업과 작업 공간의 미션·revision·작업 ID·역할이 모두 같은지 확인합니다. 하위 프로세스에는 부모 환경 전체가 아니라 운영체제 실행에 필요한 최소 변수와 별도 작업·임시·홈 경로만 전달합니다.

전문 에이전트의 결과는 `workflow_submit_result`로 제출합니다.

```json
{
  "mission_id": "mis-...",
  "revision": 1,
  "task_id": "task-...",
  "authority_token": "<one-use-token>",
  "candidate_id": null,
  "payload": {
    "gate": "pass",
    "claims": [
      {
        "claim_id": "claim-1",
        "claim": "위험 분석 결과가 기준을 충족한다",
        "artifact_sha256s": ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
        "observation_ids": ["observation-1"]
      }
    ],
    "expected_results": [
      {
        "expected_result_id": "expected-1",
        "description": "필수 위험 항목을 모두 판정한다",
        "owner_role": "requirements-specialist",
        "decision_rule_ids": ["rule-1"]
      }
    ],
    "decision_rules": [
      {
        "decision_rule_id": "rule-1",
        "description": "미판정 고위험 항목이 없어야 한다",
        "owner_role": "requirements-specialist"
      }
    ],
    "observations": [
      {
        "observation_id": "observation-1",
        "expected_result_id": "expected-1",
        "artifact_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "observed_value": "미판정 고위험 항목 0개",
        "outcome": "pass"
      }
    ],
    "decision": {
      "outcome": "pass",
      "applied_rule_ids": ["rule-1"],
      "rationale": "검증된 산출물의 관찰값이 독립적으로 정한 규칙을 충족한다"
    },
    "assumptions": [],
    "unresolved": [],
    "artifacts": [
      {
        "artifact_type": "scope-risk-assessment",
        "path": "scope-risk.json",
        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "media_type": "application/json"
      }
    ]
  }
}
```

### 결과가 받아들여지는 조건

- 현재 미션의 `mission_id`와 같음
- 현재 revision과 같음
- 발급된 `task_id`임
- 일회성 권한 증표가 미션·revision·작업·시도·작업자·작업 공간·역할에 모두 결속됨
- 현재 작업의 후보본 ID와 같음
- 결과 내용의 해시가 맞음
- 인계 JSON Schema에 맞음
- 기대 결과와 판정 규칙의 소유자가 결과 작성자와 분리됨
- 모든 주장에 검증된 산출물 SHA-256과 관찰 ID가 연결됨
- 모든 기대 결과에 실제 관찰이 있고 최종 판정에 사용한 규칙이 명시됨
- 산출물 경로가 해당 역할 작업 공간 안에 있고 기록한 SHA-256과 실제 파일이 같음
- 현재 단계의 `required_outputs`가 실제 산출물 종류와 SHA-256으로 모두 충족됨

### `gate` 값

- `pass`: 해당 역할 기준을 통과함
- `fail`: 기준을 통과하지 못함
- `inconclusive`: 필요한 관찰이 부족하여 통과·실패를 판정할 수 없음

현재 단계의 모든 필수 역할에서 가장 최근에 제출한 결과가 `pass`여야 다음 단계로 넘어갑니다. 하나라도 없거나 `fail`이면 현재 단계에 머뭅니다.

---

## 8. 미션과 revision

### `mission_id`

서로 다른 사용자 과업을 구분합니다. 다른 미션에서 늦게 도착한 결과는 현재 미션 상태를 바꾸지 못합니다.

### `revision`

한 미션 안에서 사용자 최신 지시를 구분합니다. 새 지시를 반영하면 revision이 증가합니다.

### 사용자 지시 우선 규칙

1. 사용자의 새 지시를 받음
2. `workflow_revise` 호출
3. 기존 미완료 작업을 오래된 상태로 표시
4. 목표와 단계 계획을 다시 계산
5. 새 revision 작업 발급
6. 이전 revision 결과를 현재 단계 통과에서 제외

사용자의 새 지시를 단순 메모로만 남기고 기존 작업을 계속 진행하면 안 됩니다.

---

## 9. 후보본·증거·출시

### 기본 원칙

- 검토 중인 후보본은 수정하지 않습니다.
- 수정하려면 부모 후보본을 남기고 새 자식 후보본을 만듭니다.
- 후보본에는 `source`, `requirements`, `design`, `build-config`, `dependencies` 입력이 모두 있어야 합니다.
- 후보본 ID는 입력 레이블·파일 목록·내용 해시·도구 체인·필수 증거 목록만으로 계산합니다. 미션 ID·revision·작성 역할은 계보 정보이며 콘텐츠 ID에는 넣지 않습니다.
- 후보본을 동결한 뒤 파일이 바뀌면 `CORRUPT`로 판정합니다.
- 증거는 정확히 하나의 미션·revision·후보본에 결속합니다.
- 추가 전용 증거 기록기가 실제 산출물 파일을 직접 읽어 SHA-256을 계산합니다. 임의의 해시 문자열만 제출할 수 없습니다.
- 증거에는 독립적으로 정한 기대 결과·판정 규칙과 실제 관찰값이 함께 있어야 하며, 관찰은 증거 파일 SHA-256에 결속됩니다.
- 오래되거나 거부된 증거는 승인에 쓸 수 없습니다.
- 같은 유형의 증거가 여러 개면 가장 최근 기록만 판정에 사용합니다. 최신 결과가 `fail`이면 과거 `pass`로 승인하거나 패키징할 수 없습니다.
- 승인 직전과 출시 묶음 생성 직전에 후보본을 다시 검산합니다.

### 출시 판정

`workflow_package_release`에는 다음 판정 가운데 하나를 명시합니다.

- `release`: 출시
- `limited-release`: 제한적 출시
- `hold`: 보류
- `prohibited`: 출시 금지

`hold`와 `prohibited`는 출시 묶음을 만들지 않습니다. `limited-release`에는 적용 범위(`scope`), 기한(`expires_at`), 되돌리기 방안(`rollback_plan`), 범위 밖 사용 차단(`out_of_scope_controls`)이 모두 있어야 합니다. 판정과 제한 조건은 `release-manifest.json`에 후보본 ID와 함께 기록됩니다.

### 현재 연결 상태

| 기능 | Python 핵심 엔진·CLI | Hermes 플러그인 도구 |
|---|---:|---:|
| 후보본 동결·해시 검산 | 사용 가능 | 사용 가능 |
| 부모·자식 후보본 | 사용 가능 | 사용 가능 |
| SQLite 증거 원장 | 사용 가능 | 사용 가능 |
| 독립 승인 | 사용 가능 | 사용 가능 |
| 출시 판정과 결정론적 ZIP 생성 | 사용 가능 | 사용 가능 |

미션 완료를 주장하려면 `completed=true`와 64자리 `release_artifact_sha256`이 모두 있어야 합니다. 출시 묶음은 승인된 활성 후보본에서만 만들 수 있습니다.

---

## 10. 자료 저장 위치

기본 저장 위치는 활성 Hermes 프로필의 홈 아래입니다.

```text
$HERMES_HOME/workflow-harness/
├── missions/
│   └── mis-....json
└── mission-data/
    └── mis-.../
        ├── candidate-store/
        ├── evidence.sqlite3
        └── release/
```

Windows 기본 프로필의 일반적인 위치는 다음과 같습니다.

```text
C:\Users\<사용자>\AppData\Local\hermes\workflow-harness\
```

`AGENT_WORKFLOW_DATA` 환경 변수를 지정하면 시험이나 격리 실행에서 다른 저장 위치를 쓸 수 있습니다.

미션 JSON은 임시 파일에 쓴 뒤 원자적으로 교체합니다. Hermes를 다시 시작해도 같은 `mission_id`로 상태를 이어 갈 수 있습니다.

역할별 작업 공간은 다음 위치에 만들어집니다.

```text
$HERMES_HOME/workflow-harness/workspaces/
└── missions/
    └── mis-.../
        └── rev-1/
            └── tasks/
                └── task-.../
                    └── <role>/
                        ├── work/
                        ├── build/
                        ├── tmp/
                        ├── home/
                        └── inputs/
```

---

## 11. 오류와 대응 방법

| 오류·상태 | 뜻 | 대응 |
|---|---|---|
| `mission not found` | 해당 미션 파일이 없음 | `mission_id`와 활성 Hermes 프로필 확인 |
| `invalid mission_id` | 형식이 틀렸거나 경로 문자열이 섞임 | `mis-`와 32자리 16진수 ID 사용 |
| `quarantined-foreign-mission` | 다른 미션 결과가 도착함 | 현재 상태에 반영하지 말고 해당 미션에서 조회 |
| `quarantined-stale-revision` | 이전 사용자 지시 기준의 결과 | 현재 revision 작업을 다시 수행 |
| `rejected-unexpected-task` | 작업·역할·단계·후보본 불일치 | `workflow_status`로 현재 작업 재확인 |
| `rejected-invalid-payload` | 결과 해시 불일치 | 원본 결과를 다시 만들고 재제출 |
| `missing passing result` | 필수 역할 결과가 없음 | 빠진 역할의 작업 수행 |
| `failed result` | 가장 최근 결과가 `fail` | 원인을 고친 뒤 같은 역할로 새 결과 제출 |
| `candidate snapshot verification failed` | 동결 뒤 후보본이 변경됨 | 기존 후보본을 승인하지 말고 자식 후보본 생성 |
| `self-approval is forbidden` | 구현 역할이 자신의 후보본을 승인함 | 독립 검토 역할에 승인 요청 |
| 플러그인이 목록에 없음 | Hermes 환경에 패키지가 설치되지 않음 | Hermes Python 환경의 설치 경로 확인 |
| 플러그인이 `not enabled` | 발견했지만 비활성 상태 | `hermes plugins enable agent-workflow-harness` 실행 |
| 새 대화에서 도구가 안 보임 | 도구 묶음이 비활성화됐을 수 있음 | Hermes 도구 설정에서 `agent_workflow` 확인 |

---

## 12. 보안과 권한의 한계

### 하네스가 코드로 막는 것

- 다른 미션·이전 revision 결과로 현재 상태 변경
- 예상하지 않은 작업·역할·후보본의 결과 수용
- 검토자의 제품 소스 쓰기 경로 사용
- 허용 작업 공간 밖으로 나가는 상대·절대 경로
- 심볼릭 링크를 이용한 후보본 경로 우회
- 명령 권한이 없는 역할의 외부 프로세스 실행
- 부모 프로세스의 토큰·자격 증명 환경 변수를 하위 실행기에 그대로 전달
- 동결한 후보본의 무단 변경
- 증거 원장 행의 수정·삭제
- 오래된 증거 재사용
- 구현자의 자가 승인
- 승인 전 출시 묶음 생성

### 하네스만으로 완전히 막을 수 없는 것

`WorkspaceBroker`는 하네스가 제공한 파일 쓰기 함수를 통제하고 검사 시점에 존재하는 심볼릭 링크를 거부합니다. 같은 Windows 계정으로 실행한 임의 외부 프로그램이 운영체제 권한으로 파일을 직접 고치거나, 검사와 쓰기 사이에 경로를 바꾸는 경합까지 막는 완전한 보안 경계는 아닙니다.

고위험 과업에서는 다음을 함께 사용합니다.

- 역할별 별도 운영체제 계정
- Windows ACL
- Docker·가상 머신·원격 실행 환경
- 읽기 전용 파일 시스템
- 네트워크 허용 목록
- 별도 빌드·임시·홈 디렉터리

스킬이나 프롬프트 준수만으로 권한 분리를 대신하지 않습니다.

---

## 13. 개발자용 CLI

CLI는 플러그인이 정상 동작하지 않을 때의 복구 수단이자 결정론적 시험 도구입니다. 일반 사용자는 대화창과 `/workflow`를 우선합니다.

### 종단 시연

```bash
PYTHONPATH='' \
.venv/Scripts/python.exe -m agent_harness.cli demo \
--root runs --json
```

시연은 낮은 위험의 비연구 과업에서 실제 파일과 SQLite 원장을 사용해 다음을 확인합니다.

1. 목표 충분성 점검과 제작 경로 계획 수립
2. 다른 미션 결과 격리
3. 역할별 작업 공간 생성과 결과 수신
4. 결과 수신 경로의 인계 스키마와 산출물 해시 검산
5. 다섯 필수 입력을 포함한 후보본 동결과 변경 검사
6. 동결 후보본에서 실제 수락 검사 한 건을 실행하고 명령·종료 코드·출력을 기록
7. 독립 검토자 승인
8. 출시 판정과 후보본 입력에 결속된 ZIP 생성

이 시연은 엔진 흐름을 확인하기 위한 것입니다. 독립 코드 검토·보안 검토·연구 산출물의 여섯 검증 항목을 수행하지 않으며, 전체 정확성의 증거가 아닙니다.

### 시험

```bash
PYTHONPATH='' .venv/Scripts/python.exe -m pytest tests -q
```

### 정적 검사

```bash
PYTHONPATH='' .venv/Scripts/ruff.exe check .
PYTHONPATH='' .venv/Scripts/python.exe -m mypy src tests
```

### 패키지 빌드

```bash
PYTHONPATH='' .venv/Scripts/python.exe -m build
```

---

## 14. 플러그인 비활성화와 제거

### 일시 비활성화

```bash
hermes plugins disable agent-workflow-harness
```

새 Hermes 세션부터 플러그인 도구와 명령이 로드되지 않습니다. 미션 자료는 지우지 않습니다.

### 패키지 제거

Hermes Python 환경에서 다음을 실행합니다.

```bash
python -m pip uninstall agent-workflow-harness
```

패키지를 제거해도 `$HERMES_HOME/workflow-harness`의 미션·증거·후보본 자료는 자동으로 삭제하지 않습니다. 감사·재현에 필요할 수 있으므로 별도 보존 방침에 따라 처리합니다.

---

## 15. 운영 점검표

### 시작 전

- [ ] 사용자 목표와 실제 의사결정이 분명한가
- [ ] 위험 등급을 과소평가하지 않았는가
- [ ] 논문·표·그림·핵심 수치를 만들면 연구 산출물로 표시했는가
- [ ] 작업 저장소와 허용 쓰기 범위가 정해졌는가
- [ ] 독립 검토 역할을 구현 역할과 분리했는가

### 단계 전환 전

- [ ] 현재 `mission_id`와 revision이 맞는가
- [ ] 현재 단계의 모든 필수 역할 결과가 있는가
- [ ] 가장 최근 결과가 모두 `pass`인가
- [ ] 결과가 같은 후보본을 참조하는가
- [ ] 사용자 새 지시가 뒤늦게 들어오지 않았는가
- [ ] 실패 조건이나 기대 결과를 임의로 완화하지 않았는가

### 출시 전

- [ ] 후보본을 다시 검산했는가
- [ ] 필수 증거가 모두 유효한가
- [ ] 서로 다른 미션·revision·후보본의 증거를 섞지 않았는가
- [ ] 구현자와 승인자가 다른가
- [ ] 연구 산출물의 여섯 항목을 각각 통과했는가
- [ ] 출시 묶음 해시를 기록했는가
- [ ] 출시·제한적 출시·보류·출시 금지 가운데 하나를 판정했는가
- [ ] 제한적 출시라면 범위·기한·되돌리기·범위 밖 차단을 모두 기록했는가
- [ ] 남은 위험과 검증하지 않은 가정을 밝혔는가

---

## 16. 현재 버전의 남은 제한

문서 작성 시점의 현재 구현에는 다음 제한이 있습니다.

1. Hermes 플러그인은 목표 점검, 단계 계획, 결과 제출, 사용자 지시 개정, 후보본 동결, 증거 기록, 독립 승인, 출시 묶음 생성을 지원합니다.
2. 플러그인은 역할별 작업 공간과 권한을 발급하지만 하위 에이전트를 자동으로 호출하지는 않습니다. 별도 `HermesCliRunner` 경로는 실제 Hermes CLI로 검증했으며, 운영 조정자가 발급된 작업과 결과 제출을 연결해야 합니다.
3. 운영체제 계정·컨테이너 수준의 완전한 격리는 제공하지 않습니다.
4. 현재 설치판의 `plugins doctor`는 `plugin.yaml` 디렉터리 형식만 검사해 Python 진입점 플러그인을 대상으로 삼지 못합니다. `plugins list/show`, 진입점 메타데이터, 실제 런타임 등록 스크립트로 별도 검증합니다.
5. 데스크톱 전용 진행 상황 화면은 없습니다.
6. 현재 열린 Hermes 대화는 중간에 플러그인 도구 목록을 다시 읽지 않으므로 활성화 뒤 새 세션이 필요합니다.

이 제한을 숨기거나 현재 보증 범위를 넘어선 완료를 주장하면 안 됩니다.
