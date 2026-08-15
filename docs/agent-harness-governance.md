# 증거 중심 다중 에이전트 개발 하네스 기획안

> **For Hermes:** 구현 시 총괄 조정자와 단계별 전문가를 서로 다른 작업 공간·권한·문맥으로 분리하고, 상태 전이는 결정론적 정책 엔진이 통제한다.

**목표:** 담당 에이전트가 바뀌어도 같은 요구·같은 후보본·같은 시험·같은 통과 기준으로 수렴하는 개발 하네스를 만든다.

**구조:** 한 명의 총괄 페르소나가 과업 분해와 상태 전이를 지휘하되 코드·시험·리뷰·승인을 직접 수행하지 않는다. 단계별 전문가는 격리된 작업 공간에서 최소 권한으로 일하고, 모든 인계는 candidate ID·해시·근거가 포함된 정형 문서로만 이뤄진다. LLM의 지시 준수에 기대지 않고 정책 엔진·파일시스템·도구 허용 목록이 권한을 강제한다.

**기술 구성 후보:** Python 3.11+, Git worktree 또는 임시 clone, JSON Schema, SQLite append-only event ledger, SHA-256 content addressing, Hermes `delegate_task` 실행기, OS 파일 권한/컨테이너 sandbox, CI status check, in-toto/SLSA 형식과 호환 가능한 attestation.

---

## 1. 문제 정의

이번 실패의 직접 원인은 ‘리뷰 중 수정’이지만, 시스템 차원의 원인은 다음과 같다.

1. 작업 상태는 `리뷰`였으나 쓰기 도구가 계속 열려 있었다.
2. 검토 대상이 변경 가능한 공용 작업 트리였다.
3. 소스 변경이 기존 시험·리뷰·patch·보고서를 자동으로 무효화하지 않았다.
4. 구현자·시험자·검토자가 같은 절대 경로와 빌드 산출물을 공유했다.
5. 자유형 대화가 기준본·단위·가정·근거를 대신했다.
6. 총괄 에이전트가 지휘·구현·자가 검토·수정·최종 판정을 겸했다.

따라서 개선 목표는 ‘더 주의하기’가 아니라 다음 불변 조건을 하네스가 위반 불가능하게 만드는 것이다.

```text
INV-001  REVIEWING 상태의 candidate는 불변이다.
INV-002  모든 시험·리뷰·승인·산출물은 정확히 하나의 candidate_id를 참조한다.
INV-003  candidate 내용이 바뀌면 새 candidate_id가 생기고 이전 근거는 자동 STALE 처리된다.
INV-004  구현자·시험자·검토자는 작업 공간과 빌드 디렉터리를 공유하지 않는다.
INV-005  검토자는 소스·시험·문서·빌드 산출물을 수정할 권한이 없다.
INV-006  총괄은 구현·검토·승인 역할을 겸하지 않는다.
INV-007  최종 패키지는 동일 candidate_id에 속한 필수 attestation이 모두 유효할 때만 생성한다.
INV-008  역할 권한은 prompt가 아니라 하위 시스템에서 강제한다.
```

GitHub가 diff 변경 시 기존 승인을 stale로 폐기할 수 있게 하는 이유도 검토자가 승인한 변경 집합을 고정하기 위해서다.[1] 이 원칙을 PR 기능이 아니라 하네스의 기본 불변 조건으로 가져온다.

## 2. 설계 원칙

### 2.1 총괄 페르소나는 ‘지휘관’이지 ‘만능 작업자’가 아니다

총괄 페르소나의 이름을 **품질 지휘관(Quality Commander)**으로 둔다.

품질 지휘관의 책임:

- 사용자 목표·우선순위·위험 등급 확인
- 단계별 전문가 선임
- 작업 분해와 의존 관계 관리
- candidate 생성·동결 요청
- 단계 통과 조건 충족 여부 집계
- 실패 시 돌아갈 가장 이른 단계 결정
- 사람에게 필요한 결정과 잔여 위험 제시

금지:

- 제품 소스·수락 시험 직접 수정
- 자신의 구현을 직접 승인
- 검토 finding을 구현 파일에 바로 반영
- 통과 조건 완화
- candidate가 다른 근거를 합쳐 최종 승인

Anthropic이 설명하는 orchestrator–workers 구조는 중앙 조정자가 과업을 분해·위임·통합하고, evaluator–optimizer 구조는 생성자와 평가자를 분리한다.[6] 여기서는 그 역할 분리를 권한 경계까지 강화한다.

### 2.2 LLM이 아니라 정책 엔진이 상태 전이를 통제한다

품질 지휘관은 전이를 **요청**할 수만 있다. 실제 전이는 결정론적 `policy-engine`이 수행한다.

예:

```text
freeze_candidate 요청
  ├─ 작업 트리 clean 여부
  ├─ 허용 파일 범위 준수
  ├─ 요구·시험 추적 누락 여부
  ├─ source tree/diff/config/toolchain hash 생성
  └─ 조건 충족 시 CANDIDATE_FROZEN
```

OWASP는 권한 판단을 LLM에 맡기지 말고 하위 시스템이 모든 요청을 정책에 따라 검사하도록 권고한다.[7] 따라서 prompt의 “수정하지 마라”는 보조 설명일 뿐 보안 경계가 아니다.

### 2.3 각 단계에 수행자·입력·출력·권한을 명시한다

in-toto는 공급망 layout에 순서가 있는 단계, 단계 요구, 담당 수행자를 명시하고, 각 단계의 materials·products·byproducts를 연결한다.[5] 이 모델을 개발 단계 전체에 적용한다.

### 2.4 산출물은 provenance로 소스와 결속한다

SLSA의 build provenance는 빌드 출력을 그 출력을 만든 소스 코드로 추적한다.[3] 시험 결과·리뷰·patch·보고서에도 같은 결속을 적용한다.

### 2.5 최신 base와 결합된 후보만 최종 판정한다

GitHub merge queue는 PR 변경을 최신 base와 앞선 변경에 적용한 상태에서 required checks를 다시 실행한다.[2] 하네스도 최종 패키징 직전에 최신 base를 반영한 새 candidate로 검증을 반복한다.

## 3. 역할 구성

### ROLE-00 품질 지휘관

**목적:** 전체 작업 지휘와 상태 관리.

- 도구: 상태 조회, 문서 읽기, `spawn_role_task`, 전이 요청
- 파일 권한: 제품 저장소 읽기 전용
- 금지 도구: `write_file`, `patch`, 임의 shell, commit, approval 발급
- 출력: `mission-brief`, `work-order`, `transition-request`, `decision-brief`

### ROLE-10 요구·명세 전문가

**목적:** 사용자 필요를 원자적 요구와 금지 행위로 바꾼다.

- 입력: 사용자 요청, 운영 맥락, 위험 등급
- 쓰기 허용: `requirements/`, `glossary/`, `acceptance/criteria.yaml`
- 금지: 제품 코드·시험 구현 수정
- 출력: 요구 기준선, 범위 밖 항목, 인수 기준

### ROLE-20 검증·오라클 전문가

**목적:** 구현과 독립된 예상 결과·허용 오차·경계 조건을 만든다.

- 쓰기 허용: `acceptance-tests/`, `oracles/`, `test-vectors/`
- 금지: 제품 구현 수정
- 규칙: 구현자와 다른 문맥·작업 공간·모델 호출
- 출력: RED가 예상한 이유로 실패했다는 attestation

### ROLE-30 설계·영향 분석 전문가

**목적:** 상태·자료 흐름·명세·변경 영향 범위를 설계한다.

- 쓰기 허용: `design/`, `decisions/`, `impact/`
- 금지: 제품 코드 수정
- 출력: 허용 파일 목록, 인터페이스·불변 조건, 재시험 목록

### ROLE-40 구현 전문가

**목적:** 승인된 work order 범위 안에서 최소 구현을 만든다.

- 전용 쓰기 가능 worktree
- 쓰기 허용: work order의 `allowed_paths`만
- 금지: 수락 오라클·독립 시험 기대값·승인 기록 수정
- 출력: 변경 diff, 자체 단위 시험, 구현 인계서

### ROLE-50 빌드·시험 운영자

**목적:** clean candidate snapshot에서 결정론적으로 빌드·시험한다.

- 전용 임시 clone/worktree와 전용 build directory
- 제품 소스 mount: 읽기 전용
- 쓰기 허용: `evidence/<candidate_id>/build/`만
- 네트워크: dependency lock이 준비된 뒤 기본 차단
- 출력: exit code, stdout/stderr, 환경·도구 버전, 산출물 해시

### ROLE-60 명세 적합성 검토자

**목적:** 요구·설계·구현·시험 의미가 맞는지 검토한다.

- 입력: immutable review packet
- 파일시스템: candidate snapshot 읽기 전용
- 도구: 파일 읽기, 검색, read-only git 명령
- 금지: 빌드, 수정, patch 제안 자동 적용
- 출력: finding records 또는 PASS attestation

### ROLE-61 코드 품질·보안 검토자

**목적:** 논리 오류·경계·경합·권한·안전하지 않은 동작을 검토한다.

- ROLE-60과 별도 문맥
- 고위험 변경에서는 도메인 전문가 ROLE-62 추가
- 출력: finding records 또는 PASS attestation

### ROLE-62 도메인 전문가

**목적:** 수치 계산, 데이터베이스, 보안, 분산 상태 등 과업별 전문 의미 검증.

- 과업 성격에 따라 수치 계산, 트랜잭션, 보안 경계, 분산 상태, 미디어 시간축 전문가를 선임
- 출력: 독립 반례·명세 검토

### ROLE-70 수정 전문가

**목적:** REVIEW_FAIL 뒤 승인된 finding만 고친다.

- REVIEWING candidate에는 접근 불가
- 정책 엔진이 생성한 새 child candidate 작업 공간에서만 쓰기 가능
- `finding.allowed_paths` 밖 수정 금지
- 수정 뒤 직접 리뷰 요청 불가; 품질 지휘관에게 구현 인계

### ROLE-80 형상·증거 기록기

**목적:** 사람이나 LLM의 설명이 아니라 실제 해시·결과로 계보를 기록한다.

가능하면 LLM이 아니라 결정론적 프로그램으로 구현한다.

- candidate manifest 생성
- evidence ledger append
- stale 전파
- 동일 candidate 여부 검사
- attestation schema 검증
- source→build→test→review→package 해시 연결

in-toto도 metadata 생성 메커니즘과 단계 실행 메커니즘의 분리를 권고한다.[5]

### ROLE-90 패키징·출시 운영자

**목적:** 승인된 candidate에서만 patch·release·보고서를 생성한다.

- 입력: `APPROVED` candidate와 필수 attestation
- 소스 수정 권한 없음
- 패키지 생성 전에 candidate hash 재검증
- 출력: patch, checksum, provenance, release decision packet

### HUMAN-99 위험 승인자

다음은 사람만 결정한다.

- 요구 충돌
- 허용 오차·품질·비용 절충
- 외부 명세를 깨는 변경
- 남은 고위험 결함 수용
- 최종 제한적 출시 여부

## 4. 역할별 권한 행렬

| 역할 | 소스 쓰기 | 수락 시험 쓰기 | 빌드 실행 | 리뷰 판정 | 상태 전이 | 패키징 |
|---|---:|---:|---:|---:|---:|---:|
| 품질 지휘관 | ✗ | ✗ | ✗ | ✗ | 요청만 | ✗ |
| 요구 전문가 | ✗ | 명세만 | ✗ | 요구 기준선 | ✗ | ✗ |
| 오라클 전문가 | ✗ | ✓ | 시험 RED만 | 오라클 판정 | ✗ | ✗ |
| 설계 전문가 | ✗ | ✗ | ✗ | 설계 판정 | ✗ | ✗ |
| 구현 전문가 | 허용 경로만 | 독립 오라클 ✗ | 국소 단위 시험 | ✗ | ✗ | ✗ |
| 시험 운영자 | ✗ | ✗ | ✓ | 실행 결과만 | ✗ | ✗ |
| 검토 전문가 | ✗ | ✗ | 기본 ✗ | ✓ | ✗ | ✗ |
| 수정 전문가 | child candidate 허용 경로만 | 원칙상 ✗ | 국소 시험 | ✗ | ✗ | ✗ |
| 증거 기록기 | ✗ | ✗ | ✗ | schema 판정 | 정책 적용 | ✗ |
| 패키징 운영자 | ✗ | ✗ | 재현 빌드만 | ✗ | ✗ | ✓ |

‘최소 권한’은 역할 prompt가 아니라 실제 도구·OS 권한으로 강제한다. OWASP도 에이전트가 호출할 수 있는 기능과 downstream 권한을 필요한 최소 수준으로 제한하라고 권고한다.[7]

## 5. 상태 기계

```text
DISCOVERY
  → REQUIREMENTS_BASELINED
  → ORACLE_BASELINED
  → DESIGN_BASELINED
  → IMPLEMENTING
  → CANDIDATE_FROZEN
  → VERIFYING
  → REVIEWING
  → APPROVED
  → PACKAGING
  → RELEASE_READY
  → RELEASED
```

실패 전이:

```text
VERIFYING --실패--> FIX_REQUIRED
REVIEWING --finding--> REVIEW_FAILED
REVIEW_FAILED → 기존 candidate 영구 불변·승인 불가
REVIEW_FAILED → 새 child candidate 생성 → IMPLEMENTING
base 변경 → 모든 미출시 candidate REBASE_REQUIRED
candidate 내용 변경 감지 → CANDIDATE_CORRUPT
```

금지 전이:

```text
REVIEWING → 같은 candidate의 IMPLEMENTING
APPROVED → 같은 candidate 소스 수정
VERIFYING → 검증 중 기대값 수정
PACKAGING → 소스·시험 수정
```

## 6. Candidate와 증거 모델

### 6.1 candidate ID

```text
candidate_id = sha256(
    source_tree_hash
  + acceptance_baseline_hash
  + design_baseline_hash
  + build_config_hash
  + dependency_lock_hash
  + toolchain_identity
)
```

commit SHA 하나만 쓰지 않는다. untracked FATE ref·build config·toolchain이 달라지는 문제를 막기 위해 실제 검증 입력 전체를 묶는다.

### 6.2 candidate manifest 예시

```yaml
schema: candidate-manifest/v1
candidate_id: sha256:...
parent_candidate_id: sha256:...
state: CANDIDATE_FROZEN
created_at: 2026-08-14T16:59:34+09:00
source:
  repo: ...
  commit: ...
  tree_hash: ...
  diff_hash: ...
  untracked_manifest_hash: ...
baselines:
  requirements_hash: ...
  acceptance_tests_hash: ...
  design_hash: ...
build:
  config_hash: ...
  dependency_lock_hash: ...
  toolchain_hash: ...
allowed_transitions:
  - VERIFYING
```

### 6.3 증거 상태

- `VALID`: candidate와 정확히 일치
- `STALE`: 참조 입력 중 하나가 변경됨
- `REJECTED`: schema·서명·출처·권한 불일치
- `SUPERSEDED`: 새 candidate로 대체됐지만 역사 기록으로 보존

소스 한 줄이 바뀌면 같은 candidate의 결과를 갱신하지 않는다. 새 candidate를 만들고 이전 증거를 `STALE` 또는 `SUPERSEDED`로 바꾼다.

## 7. 작업 공간 격리

Git은 한 저장소에 여러 linked worktree를 둘 수 있다.[4] 그러나 linked worktree만으로 빌드 산출물까지 격리되지는 않으므로 다음 규칙을 함께 적용한다.

```text
runs/<run_id>/
  controller/                 # 상태·문서 전용, 소스 쓰기 금지
  roles/
    requirements/<task_id>/
    oracle/<task_id>/
    implementer/<task_id>/
    verifier/<task_id>/
    reviewer-spec/<task_id>/
    reviewer-code/<task_id>/
    fixer/<task_id>/
    packager/<task_id>/
  evidence/<candidate_id>/
  ledger/
```

격리 규칙:

1. 역할마다 별도 worktree 또는 clone을 만든다.
2. 역할마다 별도 `build/`, `tmp/`, `HOME`, tool cache namespace를 둔다.
3. 컴파일러·linker가 같은 출력 경로를 공유하지 못하게 한다.
4. reviewer snapshot은 OS read-only mount 또는 ACL을 사용한다.
5. implementer는 다른 역할 경로를 볼 수 없게 한다.
6. 공유 가능한 dependency cache는 content-addressed read-only로만 제공한다.
7. credential은 역할별 단기 토큰으로 발급하고 scope를 제한한다.
8. 작업 종료 시 workspace는 폐기하되 evidence와 manifest만 보존한다.
9. agent가 절대 경로로 원본 저장소에 접근하는 것을 sandbox가 차단한다.
10. 같은 candidate의 verifier 여러 명은 source snapshot을 공유할 수 있지만 build directory는 공유하지 않는다.

현재 `delegate_task`의 ‘대화·터미널 세션 격리’만으로는 충분하지 않다. 모든 자식이 같은 프로젝트 절대 경로를 사용하면 파일시스템은 공유된다. 따라서 `delegate_task` 앞에 workspace materializer가 반드시 있어야 한다.

## 8. 전문가 간 문서 통신 규약

전문가는 자유 채팅으로 기준을 넘기지 않는다. 하네스가 검증하는 문서 유형을 사용한다.

### 8.1 공통 envelope

```yaml
schema: handoff-envelope/v1
message_id: MSG-...
run_id: RUN-...
task_id: TASK-...
candidate_id: sha256:...       # 탐색 단계면 null 허용
sender_role: ROLE-40
recipient_role: ROLE-50
message_type: implementation_handoff
created_at: ...
artifact_refs:
  - uri: artifact://...
    sha256: ...
claims:
  - id: CLM-...
    statement: ...
    evidence_refs: [EVD-...]
assumptions:
  - id: ASM-...
    statement: ...
    invalidation_condition: ...
open_questions: []
requested_action: verify_candidate
```

필수 규칙:

- candidate ID 없는 구현·검증·리뷰 인계는 거부한다.
- 수치에는 단위·시간 기준·허용 오차를 쓴다.
- claim에는 evidence reference가 있어야 한다.
- 가정에는 무효화 조건을 쓴다.
- “문제없음”, “잘 됨” 같은 판정 불가능 문장은 schema 검사에서 거부한다.

### 8.2 문서 종류

#### A. Mission Brief

- 사용자 목적
- 성공·실패 정의
- 범위·범위 밖
- 위험 등급
- 사람 결정 항목

#### B. Work Order

```yaml
work_order_id: WO-...
requirements: [REQ-...]
allowed_paths: [...]
forbidden_paths: [...]
expected_red_tests: [...]
completion_conditions: [...]
max_change_size: ...
```

#### C. Design Decision Record

- 선택지
- 선택 기준
- 채택 이유
- 기각 이유
- 영향받는 요구·시험
- 되돌리기 조건

#### D. Implementation Handoff

- 변경 파일·함수
- 구현한 요구
- 변경하지 않은 명세
- 자체 시험
- 알려진 제약
- diff hash

#### E. Verification Attestation

```yaml
candidate_id: sha256:...
executor_role: ROLE-50
source_tree_hash: ...
build_config_hash: ...
commands:
  - argv: [...]
    cwd: ...
    exit_code: 0
    stdout_hash: ...
results:
  required: PASS
  regressions: PASS
artifacts:
  - path: ...
    sha256: ...
```

#### F. Finding Record

```yaml
finding_id: DEF-...
candidate_id: sha256:...
reviewer_role: ROLE-61
severity: blocking | high | medium | low
requirement_refs: [...]
location: file:line
reproduction: ...
expected: ...
observed: ...
impact: ...
allowed_fix_paths: [...]
resolution_required: true
```

검토자는 코드를 고치지 않고 Finding Record만 낸다.

#### G. Review Attestation

- 검토한 candidate ID
- 검토 범위
- 반례·경계 조건
- findings 목록
- 판정 `PASS|FAIL|INCONCLUSIVE`
- 검토자 identity

#### H. Change Impact Record

- 변경 이유
- parent candidate
- 무효화되는 요구·설계·시험·리뷰·patch
- 다시 수행할 단계
- 새 candidate 생성 근거

#### I. Release Decision Packet

- 모든 필수 attestation
- 남은 결함과 제한
- rollback 방법
- 최종 package hash
- 사람 승인 필요 여부

## 9. 통신 흐름

```text
사용자
  ↓
품질 지휘관 ── Mission Brief ──► 요구 전문가
  ↓                                │
상태 ledger ◄── Requirements ─────┘
  ↓
오라클 전문가 ── Acceptance Baseline
  ↓
설계 전문가 ─── Design + Impact + Allowed Paths
  ↓
구현 전문가 ─── Implementation Handoff
  ↓
정책 엔진 ───── candidate freeze + hash
  ↓
시험 운영자 ─── Verification Attestation
  ↓ PASS
명세 검토자 + 코드 검토자 + 선택적 도메인 검토자
  ↓
PASS 전원 → APPROVED
FAIL 1명 이상 → REVIEW_FAILED → Finding Record → 새 child candidate
  ↓
패키징 운영자 ─ package + provenance
  ↓
사람 위험 승인자 ─ release / limited release / hold
```

전문가끼리 직접 “이 한 줄만 고쳐 달라”고 대화하지 않는다. 검토 finding은 지휘관과 정책 엔진을 거쳐 수정 work order로 변환된다.

## 10. 단계별 통과 기준

### REQUIREMENTS_BASELINED

- 필수 요구가 시험 가능함
- 범위 밖·금지 행위 명시
- 미확인 가정과 사람 결정 항목 분리

### ORACLE_BASELINED

- 정상·경계·오류·상태 전이 벡터 존재
- 독립 예상 결과 존재
- RED가 예상한 원인으로 실패
- 구현자가 수락 기대값을 바꿀 수 없음

### CANDIDATE_FROZEN

- source/diff/untracked/config/toolchain hash 존재
- 작업 트리 내용이 snapshot과 동일
- 이후 쓰기 권한 폐쇄

### VERIFIED

- clean 격리 환경 빌드
- 필수·회귀·보안·문서 검사 통과
- 실행 결과가 동일 candidate ID를 참조
- 빌드 산출물 provenance 존재

### REVIEWED

- 명세 적합성·코드 품질 검토 모두 PASS
- 최신 push/candidate를 다른 사람이 승인
- finding 0 또는 승인된 비차단 finding만 존재
- 검토 중 candidate 변경 0

GitHub도 diff가 바뀌면 기존 승인을 stale로 처리하고 다시 승인을 요구할 수 있다.[1] 이 하네스에서는 선택 옵션이 아니라 항상 적용한다.

### APPROVED

- 필수 attestation의 candidate ID가 모두 같음
- base 최신성 검사 통과
- 잔여 위험 책임자 명시

### RELEASE_READY

- 승인 candidate에서만 package 생성
- package hash와 candidate provenance 결속
- rollback·재현 명령 존재

## 11. 위험별 전문가 구성

| 위험 | 필수 역할 |
|---|---|
| R0 문서·서식 | 지휘관, 구현자, 한 명의 검토자 |
| R1 국소 기능 | 요구/오라클, 구현자, 시험자, 코드 검토자 |
| R2 다중 모듈·복잡 상태 | 요구, 오라클, 설계, 구현, 시험, 명세 검토, 코드 검토, 도메인 검토 |
| R3 안전·규정·비가역 | R2 + 독립 오라클 소유자 + 보안/안전 전문가 + 사람 위험 승인자 + 재현 빌드 |

여러 모듈과 계산 규칙이 얽힌 상태 기반 과업은 R2 이상으로 다룬다.

## 12. 현재 Hermes에 적용할 때의 차이

### 현재 문제

- `delegate_task`는 대화·터미널 세션은 격리하지만, 자식에게 같은 절대 저장소 경로를 주면 파일은 공유된다.
- prompt로 ‘수정 금지’를 적어도 write 도구와 shell이 남아 있으면 강제력이 없다.
- 검토자가 빌드 명령을 실행하면 공용 빌드 산출물이나 캐시를 손상시킬 수 있다.
- 자식 결과가 어느 source hash를 검토했는지 자동 확인하지 않는다.

### 필요한 하네스 확장

```python
spawn_role_task(
    role="reviewer-code",
    candidate_id="sha256:...",
    workspace_mode="readonly-snapshot",
    tool_profile="review-readonly",
    network="off",
    artifact_output="evidence-only",
)
```

필수 구성 요소:

1. `candidate_manager`: snapshot·hash·parent lineage
2. `workspace_materializer`: 역할별 worktree/clone·권한
3. `capability_broker`: 역할별 도구 허용 목록과 경로 ACL
4. `policy_engine`: 상태 전이와 통과 조건
5. `evidence_recorder`: 실행 결과·해시·attestation
6. `handoff_bus`: schema 검증된 문서 교환
7. `stale_propagator`: 변경 영향에 따른 근거 무효화
8. `release_assembler`: 승인 candidate만 package

## 13. 구현 파일 구조 제안

재사용 가능한 별도 저장소로 먼저 만든다.

```text
C:/Users/gimhc/agent-workflow-harness/
  pyproject.toml
  src/agent_harness/
    controller.py
    state_machine.py
    policy_engine.py
    candidate.py
    workspace.py
    capabilities.py
    evidence.py
    handoff.py
    agent_runner.py
    release.py
  policies/
    standard.yaml
    research-software.yaml
    stateful-systems-r2.yaml
  roles/
    commander.yaml
    requirements.yaml
    oracle.yaml
    designer.yaml
    implementer.yaml
    verifier.yaml
    reviewer_spec.yaml
    reviewer_code.yaml
    reviewer_domain.yaml
    fixer.yaml
    evidence_recorder.yaml
    packager.yaml
  schemas/
    candidate-manifest.schema.json
    work-order.schema.json
    handoff-envelope.schema.json
    verification-attestation.schema.json
    finding.schema.json
    review-attestation.schema.json
    release-decision.schema.json
  templates/
    mission-brief.md
    decision-record.md
    implementation-handoff.md
    change-impact.md
  tests/
    test_state_machine.py
    test_candidate_invalidation.py
    test_role_capabilities.py
    test_workspace_isolation.py
    test_evidence_binding.py
    test_handoff_schema.py
    test_release_fail_closed.py
    integration/
      test_review_failure_creates_child_candidate.py
      test_concurrent_builds_do_not_share_outputs.py
      test_stale_approval_blocks_package.py
```

프로젝트에는 다음만 둔다.

```text
<project>/.hermes/workflow.yaml
<project>/.hermes/requirements/
<project>/.hermes/acceptance/
<project>/.hermes/evidence/      # 또는 외부 artifact store URI
```

## 14. 구현 단계

### Task 1: 상태 기계와 candidate schema

**목표:** 변경 중인 candidate를 리뷰할 수 없게 한다.

1. 실패하는 상태 전이 시험 작성
2. candidate manifest schema 작성
3. content hash 계산 구현
4. 변경 시 새 candidate 생성·이전 evidence stale 처리
5. 금지 전이 시험 통과

핵심 시험:

```text
REVIEWING candidate의 파일 변경 시도 → 권한 오류
candidate hash 변경 → 기존 review attestation STALE
STALE review가 하나라도 있으면 APPROVED 전이 거부
```

### Task 2: 역할 권한과 작업 공간 격리

**목표:** prompt가 아니라 OS·도구 계층에서 역할을 강제한다.

1. 역할별 tool profile 작성
2. 별도 worktree/clone materializer 구현
3. read-only reviewer snapshot 구현
4. build directory·HOME·tmp 격리
5. 절대 경로 탈출·cross-workspace 쓰기 차단 시험

### Task 3: 문서 통신 bus와 schema

**목표:** 자유형 대화 대신 검증 가능한 인계 문서를 사용한다.

1. 공통 envelope schema
2. Work Order·Finding·Attestation schema
3. 단위·candidate ID·evidence ref 필수 검사
4. 자유형 판정 문장 거부
5. append-only event ledger

### Task 4: Hermes 위임 실행기

**목표:** `delegate_task` 전에 격리·권한·candidate 결속을 자동 적용한다.

1. role→tool profile 매핑
2. workspace 생성 후 해당 경로만 child context에 전달
3. child 결과에 candidate ID·artifact hash 요구
4. 결과 schema 실패 시 fail-closed
5. child 종료 후 workspace 보존/폐기 정책

### Task 5: 검증·리뷰·수정 순환

**목표:** 리뷰 중 수정이 구조적으로 불가능하게 한다.

1. verifier attestation 검사
2. 다중 reviewer quorum
3. finding 발생 시 REVIEW_FAILED
4. 새 child candidate와 fixer work order 생성
5. 전체 검증·리뷰 재시작

### Task 6: 패키징과 provenance

**목표:** 검증한 소스와 실제 patch·release를 결속한다.

1. 승인 attestation 집계
2. 동일 candidate ID 확인
3. clean packaging workspace
4. package checksum·provenance 생성
5. 최신 base 결합 재검증

### Task 7: 결함 주입 모의 시험

다음 결함을 일부러 넣어 하네스가 막는지 확인한다.

- 리뷰 중 코드 수정
- 검토 후 새 commit push
- 다른 candidate의 시험 결과 재사용
- 두 빌드 작업자의 동일 출력 디렉터리 사용
- reviewer의 `patch` 호출
- implementer의 acceptance expected value 수정
- stale review로 package 생성
- absolute path로 원본 저장소 직접 수정
- 총괄의 self-approval
- package 생성 뒤 소스 변경

## 15. 품질 측정 기준

작업량이나 review finding 수를 품질 지표로 삼지 않는다. 다음 불변 조건 위반을 측정한다.

```text
stale_evidence_accepted = 0
cross_role_source_writes = 0
shared_build_output_collisions = 0
candidate_mismatch_in_release = 0
reviewer_write_attempts_succeeded = 0
untraced_claims_in_handoff = 0
self_approval_events = 0
```

추가 운영 지표:

- 결함 발견 뒤 올바른 단계로 복귀한 비율
- candidate 생성부터 통과 판정까지 소요 시간
- 격리·검증 비용
- 수동 예외 승인 횟수와 사유
- 재현 실행 성공률

## 16. 도입 순서와 권고

### 1차: 가장 작은 강제 장치

먼저 다음 네 가지만 구현한다.

1. candidate manifest와 hash
2. 역할별 별도 worktree/build dir
3. REVIEWING read-only 정책
4. 변경 시 모든 approval/test/package evidence stale 처리

이 네 가지가 이번 실패를 직접 막는다.

### 2차: 전문가 역할과 문서 통신

- 지휘관·오라클·구현·시험·검토·수정·패키징 역할
- Work Order, Handoff, Finding, Attestation schema
- 다중 검토자 quorum

### 3차: provenance·release 자동화

- source→build→test→review→package 계보
- 최신 base 결합 검사
- in-toto/SLSA 호환 attestation

## 17. 최종 권고안

이 워크플로의 핵심 문장은 다음과 같다.

> 에이전트에게 절차를 지키라고 요청하지 않는다. 역할별로 가능한 행동 자체를 제한하고, 모든 판단을 불변 candidate와 해시가 있는 증거에 결속한다.

권고 운영 형태:

```text
품질 지휘관 1
  ├─ 요구·명세 전문가 1
  ├─ 오라클 전문가 1
  ├─ 설계·영향 전문가 1
  ├─ 구현 전문가 N
  ├─ 시험 운영자 1+
  ├─ 명세 검토자 1
  ├─ 코드 검토자 1
  ├─ 도메인 검토자 0~N
  ├─ 수정 전문가 0~1 (실패 시에만)
  ├─ 결정론적 증거 기록기 1
  └─ 패키징 운영자 1
```

총괄의 능력을 키우는 것보다 **총괄도 위반할 수 없는 하네스 정책**을 만드는 것이 우선이다.

## 18. 외부 근거 요약

- GitHub 보호 규칙: diff 변경 시 승인 무효화와 최신 push 재승인.[1]
- GitHub merge queue: 최신 base와 결합한 상태에서 required checks 재실행.[2]
- SLSA: 빌드 산출물을 실제 소스에 연결하는 provenance.[3]
- Git worktree: 역할별 별도 working tree 구성 기반.[4]
- in-toto: 순서 있는 단계·담당 수행자·materials/products/byproducts·권한 분리.[5]
- Anthropic: orchestrator–workers와 evaluator–optimizer 역할 분리.[6]
- OWASP: 에이전트 기능·권한 최소화와 하위 시스템의 complete mediation.[7]

## Sources

[1] https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches — GitHub Docs: About protected branches
    > "Optionally, you can choose to dismiss stale pull request approvals when commits are pushed that affect the diff in the pull request."
[2] https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue — GitHub Docs: Managing a merge queue
    > "The merge queue will ensure the pull request's changes pass all required status checks when applied to the latest version of the target branch and any pull requests already in the queue."
[3] https://slsa.dev/spec/v1.2/provenance — SLSA v1.2: Provenance
    > "Build provenance - tracks the output of a build process back to the source code used to produce that output."
[4] https://git-scm.com/docs/git-worktree — Git: git-worktree Documentation
    > "A git repository can support multiple working trees, allowing you to check out more than one branch at a time."
[5] https://github.com/in-toto/docs/blob/master/in-toto-spec.md — in-toto Specification
    > "Task and privilege separation: the different steps within the supply chain can be assigned to different functionaries."
[6] https://www.anthropic.com/research/building-effective-agents — Anthropic: Building Effective AI Agents
    > "In the evaluator-optimizer workflow, one LLM call generates a response while another provides evaluation and feedback in a loop."
[7] https://genai.owasp.org/llmrisk/llm062025-excessive-agency — OWASP LLM06:2025 Excessive Agency
    > "Implement authorization in downstream systems rather than relying on an LLM to decide if an action is allowed or not."
