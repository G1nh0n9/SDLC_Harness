# 워크플로 프로젝트 인계서

## 1. 원래 요청

> 전체 지휘할 페르소나를 두고 각 단계별 전문가를 구성하며, 전문가 사이의 의사소통을 위한 문서 지침을 설계한다.

## 2. 인계 범위

이 환경에는 위 요청과 직접 관련된 워크플로 자료만 인계한다.

- 전체 하네스 기획안
- 기획안의 인용 근거 원장
- 조사 당시 보존한 원문 발췌 자료
- 현재 작업 상태와 다음 구현 시작점
- 새 세션에서도 자동으로 적용할 프로젝트 규칙

다른 소프트웨어 수정 작업의 코드, 패치, 보고서, 시험 결과는 인계 범위에서 제외한다.

## 3. 확정된 설계 결정

### 3.1 총괄 역할

`품질 지휘관`은 사용자 목표, 위험 등급, 과업 분해, 의존 관계, 단계 통과 조건을 관리한다. 제품 코드 작성, 수락 시험 수정, 자가 검토, 자가 승인, 패키징은 직접 수행하지 않는다.

### 3.2 단계별 전문가

- 요구·명세 전문가
- 검증·오라클 전문가
- 설계·영향 분석 전문가
- 구현 전문가
- 빌드·시험 운영자
- 명세 적합성 검토자
- 코드 품질·보안 검토자
- 필요 시 도메인 전문가
- 검토 실패 뒤에만 투입되는 수정 전문가
- 결정론적 형상·증거 기록기
- 패키징·출시 운영자
- 고위험 결정을 맡는 사람 승인자

### 3.3 강제해야 할 불변 조건

1. `REVIEWING` 상태의 후보본은 불변이다.
2. 모든 시험·검토·승인·산출물은 하나의 `candidate_id`를 참조한다.
3. 후보본 입력이 바뀌면 새 ID를 만들고 기존 근거를 `STALE` 처리한다.
4. 구현자·시험자·검토자는 작업 공간과 빌드 디렉터리를 공유하지 않는다.
5. 검토자는 소스·시험·문서·빌드 산출물을 수정할 수 없다.
6. 총괄은 구현·검토·승인을 겸하지 않는다.
7. 같은 후보본의 필수 증거가 모두 유효할 때만 패키지를 만든다.
8. 권한은 프롬프트가 아니라 파일시스템, 도구 허용 목록, 정책 엔진으로 강제한다.

### 3.4 후보본과 증거

후보본 ID는 소스 트리뿐 아니라 수락 기준선, 설계 기준선, 빌드 설정, 의존성 잠금 파일, 도구 체인을 함께 해시해 만든다. 증거 상태는 `VALID`, `STALE`, `REJECTED`, `SUPERSEDED`로 관리한다.

### 3.5 인계 문서

- Mission Brief
- Work Order
- Design Decision Record
- Implementation Handoff
- Verification Attestation
- Finding Record
- Review Attestation
- Change Impact Record
- Release Decision Packet

구현·검증·검토 단계의 인계에는 후보본 ID, 산출물 해시, 주장과 근거, 가정과 무효화 조건이 있어야 한다.

### 3.6 상태 흐름

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

검증이나 검토가 실패하면 기존 후보본을 수정하지 않는다. 실패한 후보본을 불변으로 남기고 새 자식 후보본을 생성해 구현 단계로 돌아간다.

## 4. 구현 순서

1. 상태 기계와 candidate schema
2. 역할 권한과 작업 공간 격리
3. 정형 인계 문서와 스키마 검사
4. Hermes `delegate_task` 실행기
5. 검증·검토·수정 순환
6. 패키징과 provenance
7. 결함 주입 모의 시험

## 5. 현재 완료 상태

구현 완료:

- Python 3.11 패키지와 개발·복구용 `agent-harness` CLI
- 목표의 9개 핵심 항목 충분성 점검과 탐색·제작 경로 구성
- 단계별 필수 입력·출력·권한·통과 기준·실패 복귀 지점
- 위험·연구 산출물 여부에 따른 전문 역할 구성
- 미션 revision·비동기 결과 수신함·사용자 지시 우선 처리
- 역할별 작업 공간·쓰기 경로·명령·승인 권한
- 실행기의 작업 공간 결속 확인과 최소 환경 변수 전달
- 결과 수신 경로에 결합된 인계 JSON Schema와 산출물 SHA-256 검산
- 다섯 필수 입력을 묶는 콘텐츠 기반 불변 후보본·부모 자식 계보·변조 탐지
- 실제 증거 파일을 해시하는 SQLite append-only 증거 원장과 해시 사슬
- 최신 증거 우선, 오래된 증거·자가 승인·상태 건너뛰기 차단
- 출시·제한적 출시·보류·출시 금지 판정
- 승인된 현재 revision 후보본만 받는 결정론적 출시 묶음
- Hermes CLI 실행기와 기록형 시험 실행기
- Hermes Python 진입점 플러그인, 8개 `workflow_*` 도구, `/workflow` 명령, 내장 스킬
- 미션 JSON 저장과 Hermes 재시작 뒤 상태 복원
- 한국어 사용자 설명서

현재 판본에서 실행해 통과한 검증:

- `pytest tests -q`: 49개 통과
- `ruff check src tests scripts`: 통과
- `mypy src tests`: 29개 파일, 오류 0건
- wheel·sdist 빌드: 통과
- wheel SHA-256: `0a3e082ea6c6f8c76dbebcc769816b58f29aabcf42ff0f3d176284594a8a3726`
- sdist SHA-256: `a71a81bb2ed84662f69f5d624d3ed575ea90fe72bd046642ce13ccb52e5c140b`
- wheel 필수 내용 27개 항목 확인, 필수 플러그인·스킬·스키마 누락 0건
- 별도 가상환경에 wheel 무의존성 재설치, 설치된 `agent-harness` 시연, Hermes 진입점 메타데이터 조회: 통과
- Hermes 플러그인 실제 registry 등록과 8개 도구 호출: 통과
- Hermes CLI 실행기 실제 안전 모드·도구 없음 실행과 구조화 결과 회수: 통과
- CLI 시연: 동결 후보본의 실제 수락 검사 종료 코드·출력 기록과 출시 ZIP 해시 검산
- 금지 용어 `adapter`, `contract`, `계약`, `어댑터`: 0건

독립 검토 상태:

- 첫 독립 검토는 SEC-001~003과 LOG-001~010을 보고해 실패 판정했다.
- 경로 탈출, 실행기 권한·환경, 심볼릭 링크, 상태 우회, 조작 증거, 최신 `fail`, 단계 실행, revision, 정형 인계, 목표 충분성, 실행 가능한 단계 계획, 후보본 필수 입력·ID, 출시 판정, 가짜 시연 증거를 각각 회귀 시험과 구현으로 보강했다.
- 최신 작업 트리에 대한 두 번째 독립 검토는 실행 중이며, 그 결과 전에는 독립 검토 통과를 주장하지 않는다.

현재 제한:

- `WorkspaceBroker`는 하네스가 제공하는 쓰기 경로와 검사 시점의 심볼릭 링크를 통제한다. 같은 운영체제 계정의 외부 프로세스가 직접 파일을 바꾸거나 검사와 쓰기 사이에 경로를 교체하는 경합까지 막는 완전한 보안 경계는 아니다.
- 현재 Hermes `plugins doctor`는 `plugin.yaml` 디렉터리만 검사하므로 Python 진입점 플러그인을 대상으로 삼지 못한다. `plugins list/show`, 진입점 메타데이터, 실제 registry 등록 스크립트로 보완 검증한다.
- 플러그인은 작업과 역할별 공간을 발급하지만 하위 에이전트를 자동 호출하지 않는다. 운영 조정자가 작업 실행과 결과 제출을 연결해야 한다.
- CLI `demo`는 수락 검사 한 건을 실행하는 엔진 시연이다. 독립 코드·보안 검토, 연구 타당성, 전체 정확성의 증거가 아니다.
- 시험 통과는 구현한 시나리오 범위의 근거이며 모든 입력에서 완전한 정확성을 증명하지 않는다.

## 6. 검증 명령

```bash
PYTHONPATH='' .venv/Scripts/python.exe -m pytest tests -q
PYTHONPATH='' .venv/Scripts/python.exe -m ruff check src tests scripts
PYTHONPATH='' .venv/Scripts/python.exe -m mypy src tests
PYTHONPATH='' .venv/Scripts/python.exe -m build

PYTHONPATH='C:/Users/gimhc/agent-workflow-harness/src' \
  C:/Users/gimhc/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe \
  C:/Users/gimhc/agent-workflow-harness/scripts/verify_plugin_runtime.py

PYTHONPATH='' \
  C:/Users/gimhc/agent-workflow-harness/.venv/Scripts/python.exe \
  C:/Users/gimhc/agent-workflow-harness/scripts/verify_hermes_runner.py

PYTHONPATH='' .venv/Scripts/python.exe -m agent_harness.cli demo \
  --root C:/Users/gimhc/agent-workflow-harness/runs --json
```

구조와 사용법은 `README.md`와 `docs/user-guide.md`, 실행 요구는 `docs/requirements.md`, 상세 설계 근거는 `docs/agent-harness-governance.md`에서 확인한다.
