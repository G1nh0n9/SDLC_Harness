# 구조도와 구조 문서 작성 조사

## 1. 조사 목적

처음 보는 사용자가 증거 중심 다중 에이전트 하네스의 목적·조직·구성 요소·실행 흐름·실패 복구를 짧은 시간에 이해하도록 구조도와 설명 문서를 어떻게 구성할지 조사했다.

이 문서는 그림의 표현 방식만 다루지 않는다. 다음을 함께 정한다.

- 독자별로 어떤 확대 수준을 보여 줄 것인가
- 정적 구성 요소와 동적 실행 흐름을 어떻게 분리할 것인가
- 각 상자의 책임·자료·신뢰 경계를 어떻게 설명할 것인가
- 목표 구조와 현재 구현 상태를 어떻게 구분할 것인가
- 구조 변경 이유와 이력을 어떻게 보존할 것인가

## 2. 조사 결과

### 2.1 한 장에 모든 것을 넣지 않는다

C4 모델은 소프트웨어 시스템·컨테이너·구성 요소·코드의 계층적 추상화와 대응하는 구조도를 사용한다.[1] 서로 다른 확대 수준은 서로 다른 독자에게 다른 이야기를 전달하며, 모든 수준을 의무적으로 그리지 않고 가치가 있는 수준만 선택한다. 대부분의 팀에는 전체 맥락도와 상위 구성 요소도가 충분하다고 설명한다.[2]

전체 맥락도는 시스템을 가운데 두고 사용자와 외부 시스템을 보여 주며, 기술·통신 방식보다 큰 목적과 관계에 집중한다. 비기술 독자도 볼 수 있어야 한다.[3] 상위 구성 요소도는 시스템 내부의 주요 실행 단위·자료 저장소·책임 분배·통신을 보여 주므로 개발자와 운영자가 주 독자다.[4] 런타임 순서도는 복잡하거나 반복되는 중요한 사용 사례에만 제한적으로 사용한다.[5]

이 하네스에는 다음 확대 수준을 사용한다.

1. 전체 맥락도: 사용자는 무엇을 요청하고 무엇을 받는가
2. 조직 책임도: 총괄 관리자와 세 책임 축은 어떻게 협력하는가
3. 상위 구성 요소도: 계획·권한·실행·후보본·증거·품질 판정 구성 요소
4. 동적 흐름도: 한 미션이 요구에서 완료까지 어떻게 진행되는가
5. 보호 흐름도: 허위 완료·중단·재시도를 어떻게 처리하는가

코드 수준 구조도는 구현이 안정된 뒤 실제 패키지 구조를 기준으로 별도 작성한다.

### 2.2 그림마다 전달할 한 문장을 먼저 정한다

Google의 기술 그림 안내서는 그림을 그리기 전에 먼저 짧은 설명 문장을 쓰고, 독자가 무엇을 기억해야 하는지 정하라고 권한다. 한 그림에 한 문단 또는 설명 항목 다섯 개보다 많은 정보를 넣지 않고, 큰 그림 뒤에 하위 구조를 별도 그림으로 확장하라고 한다.[6]

이 하네스의 각 그림에는 다음을 붙인다.

- 독자
- 그림의 한 문장 결론
- 범위
- 그림에 포함하지 않은 내용
- 색·선·상태 표기 범례
- 그림 뒤의 구성 요소 책임 표

구조도가 복잡해지면 글씨를 줄이거나 상자를 더 작게 만드는 대신 별도 그림으로 나눈다.

### 2.3 개요와 상세 자료를 점진적으로 공개한다

Google은 처음 보는 독자를 위한 개요·개념 문서를 짧게 만들고, 숙련자를 위한 상세 참고 자료와 분리하며, 문서의 범위·선행 지식·범위 밖을 서두에서 명확히 밝히라고 한다.[7] Google Cloud 구조 지침은 구조 문서가 여러 직종의 공통 언어를 만들고, 사용 사례와 결정 맥락·변경 이력을 보존해 새 참여자의 적응과 후속 결정을 돕는다고 설명한다.[8]

문서 묶음은 다음 순서로 구성한다.

1. 5분 개요
2. 구조도 모음
3. 구성 요소·자료·권한 상세
4. 실행 시나리오
5. 품질·보안·복구 규칙
6. 구조 결정 기록
7. 구현 상태와 검증 근거

### 2.4 구조도 뒤에 품질 관점과 적용 범위를 연결한다

AWS Architecture Center는 운영 우수성·보안·안정성·성능·비용·지속 가능성 관점으로 참조 구조와 사례를 분류한다.[9]

AWS는 단순하고 일관된 공식 아이콘을 사용해 설계·배포·토폴로지를 전달한다.[10]

Azure 구조 지침도 신뢰성·보안·비용·운영·성능을 사업 요구와 함께 평가하고, 조직 기준·구조 방식·설계 양식·기술 선택·참조 구조를 차례로 검토한다.[11]

Azure Architecture Center는 구조도와 기술 설명이 결합된 실제 사례를 작업 유형별로 탐색할 수 있게 한다.[12]

이 하네스의 구조도 범례는 장식 색이 아니라 의미를 고정한다.

- 청록: 사용자·Hermes 사용면
- 파랑: 계획·조정
- 초록: 실행·구현
- 보라: 후보본·증거·상태 자료
- 노랑: 품질 보증·판정
- 빨강: 권한·정책·신뢰 경계
- 회색: 외부 시스템·범위 밖

각 구성 요소 설명에는 관련 품질 관점, 실패 영향, 필수 자료와 검증 방법을 연결한다.

### 2.5 AI 에이전트 흐름은 복잡도와 사용 조건을 함께 설명한다

Azure의 AI 에이전트 조정 지침은 직접 모델 호출, 도구를 가진 단일 에이전트, 다중 에이전트를 복잡도 순으로 비교하고, 요구를 만족하는 가장 낮은 복잡도를 선택하라고 한다. 다중 에이전트는 교차 분야·독립 보안 경계·병렬 전문성이 실제로 필요할 때 사용한다.[13]

각 조정 방식을 구조도만으로 소개하지 않고 다음 순서로 설명한다.[13]

- 작동 방식
- 사용할 때
- 피할 때
- 실제 예
- 비용·지연·오류 형태
- 결과 집계와 충돌 처리

이 하네스의 동적 세부 전문가도 같은 원칙을 따른다. 필수 관점 전체를 먼저 생성하되 P0·P1 관점까지 모두 별도 LLM로 만들지 않는다. 단일 전문가가 신뢰성 있게 처리할 수 없거나 독립성·심화 지식·병렬성이 필요할 때만 별도 전문가를 만든다.

### 2.6 실제 제품 문서는 간소화 그림과 상세 그림을 분리한다

GitLab 구조 문서는 먼저 간소화된 구성 요소 그림을 제공하고, 그 뒤 완전한 구성 요소 그림·범례·환경별 지원 상태·구성 요소별 책임과 통신을 설명한다.[14] Kubernetes는 제어부·작업 노드·선택 기능으로 먼저 계층화하고 각 핵심 구성 요소의 한 줄 책임을 제시한 뒤 세부 문서로 연결한다.[15] Temporal은 네 상위 서비스의 책임을 먼저 제시하고 각 서비스의 통신·상태·확장·실패 복구 관계를 별도로 설명한다.[16]

하네스 문서도 다음 두 층을 분리한다.

- 간소화 그림: 사용자가 전체 원리를 이해하는 데 필요한 구성만 표시
- 상세 그림: 개발자가 정책 우회·자료 계보·작업 실행을 추적하는 데 필요한 구성 표시

그림 속 상자 이름은 문서의 구성 요소 표와 코드의 책임 이름에 연결한다. 구현 뒤에는 코드 경로도 연결하되, 설계 단계에서는 존재하지 않는 구현을 완료된 것처럼 표시하지 않는다.

### 2.7 구조 변경 이유는 별도 결정 기록으로 보존한다

AWS의 구조 결정 기록 방식은 중요한 결정마다 맥락·결정·결과를 남기고, 수락된 기록은 수정하지 않으며 새 정보가 생기면 새 기록이 이전 결정을 대체하도록 한다.[17][18] 결정 기록 모음은 새 참여자가 제목으로 전체 맥락을 훑고 필요할 때 상세 이유를 읽을 수 있게 한다.[18]

이 하네스는 다음 결정부터 별도 구조 결정 기록을 만든다.

- 세 책임 축과 총괄 관리자
- 필수 관점 우선 생성과 P0~P3 기본 심도, P4 독립 판정, P5 제한 조사
- 동적 품질 프로필
- 공통 지식 기반 이중 인계 수락
- 권한 증표와 정책 엔진 중심 상태 변경
- 완료 안정성·재시도·체크포인트

수락된 기록을 직접 고치지 않는다. 변경이 필요하면 새 기록이 이전 기록을 `superseded`로 대체한다.

### 2.8 구성 요소보다 독자의 첫 질문과 대표 실행을 먼저 설명한다

추가 조사에서 기존 초안의 가장 큰 문제를 확인했다. C4 확대 수준을 지키는 것만으로는 문서가 독자 중심이 되지 않는다. 무엇을 어떤 순서로 설명하느냐가 더 중요하다.

Backstage 구조 개요는 세 주요 구성 요소를 서로 다른 기여자 집단과 연결해 설명한다.[19] OpenTelemetry 개요는 구성 요소 목록보다 먼저 핵심 용어와 신호 간 공통점·독립성, 교차 관심사를 다룰 때 생기는 설계상 긴장을 설명한다.[20] Airflow는 사용자가 이해하는 Dag와 Task를 먼저 정의한 뒤 필수 구성 요소·선택 구성 요소·배포 그림으로 내려간다.[21]

Kubernetes는 control plane·node·addon의 큰 경계와 선택 여부를 짧은 정의와 전체 그림 한 장으로 설명한다.[15] Prometheus는 구성 요소보다 먼저 제품이 맞는 문제와 맞지 않는 문제를 밝힌다.[44] GitLab은 간소화 그림과 전체 그림을 분리하고 설치 환경별 지원 상태를 범례와 함께 제시한다.[14]

시각 표현도 이 문서들의 공통점을 따른다. Kubernetes와 GitLab은 흰 문서 본문, 지역 목차, 짧은 절, 단순화한 구조도를 사용하고,[15][14] Microsoft Learn의 Architecture Center는 제한된 본문 폭과 왼쪽 탐색·오른쪽 지역 목차로 긴 기술 설명의 읽기 위치를 고정한다.[11] 하네스의 시각 문서도 흰 바탕, 절제된 제목 크기, 파란색 한 가지 주색, 얇은 회색 경계, 그림 번호·캡션을 사용한다. 장식용 카드 격자와 홍보 문구형 첫 화면은 사용하지 않는다.

Rust 컴파일러 개발 안내서는 먼저 “컴파일러가 코드에 무슨 일을 하는가”를 설명하고, 그 뒤 “어떻게 구현하는가”를 별도로 다룬다.[25]

Envoy는 제품이 해결하려는 문제와 상위 기능을 먼저 밝히고,[26] 별도의 `Life of a Request`에서 용어와 네트워크 문맥을 정한 뒤 요청 하나가 내부 단계를 통과하는 순서를 따라간다.[27]

DBOS 첫 페이지는 내구성 실행의 효용을 한 문장으로 설명하고 언어별 시작 경로를 제시하며,[28] workflow 상세 문서는 짧은 실행 예시에서 중단 복구를 보여 준 직후 작업 ID·중복 억제·결정성·시간 제한으로 확장한다.[30]

반대로 Argo Workflows 구조 페이지는 배포 구성·namespace·pod 내부와 소스 경로를 곧바로 설명하므로 구현 기여자 참고 자료로는 유용하지만 처음 보는 사용자용 개요의 정보 순서로 그대로 가져오기는 어렵다.[22]

따라서 하네스의 구조 문서 묶음은 다음 독자 순서를 따른다.

1. 해결하려는 실패와 하네스의 좁은 보장 범위
2. 세 책임 축과 세 가지 핵심 산출물
3. 역사적 기반과 참조 모델
4. 구체적인 미션 하나의 종단 흐름
5. 규칙을 강제하는 논리 구성 요소
6. 완료·실패·복구 판정
7. 신뢰 경계와 역할별 다음 읽을 자료

5분 개요에는 1~4의 요약, 목표 설계라는 범위 고지, 독자별 다음 문서만 둔다. 구성 요소 이름과 완료·복구·신뢰의 상세는 별도 문서로 미룬다. 사용자는 먼저 하네스가 하는 일과 한 미션의 흐름을 이해하고, 개발자·운영자는 그다음에 구현 구조로 내려간다.

### 2.9 개요·절차·참고 자료·결정 이력을 분리한다

Diátaxis는 사용자가 배우기, 특정 과업 수행, 사실 조회, 개념 이해에서 서로 다른 문서가 필요하다고 구분한다.[23] arc42도 목표·제약·문맥·해결 전략·구성·실행·결정·품질·위험·용어를 별도 관심사로 나눈다.[24]

이 하네스에서는 `architecture.md`가 모든 자료를 흡수하지 않도록 다음처럼 나눈다.

- 5분 개요: 문제, 전체 구조, 대표 미션, 목표 설계 범위, 독자별 다음 문서
- 전체 그림: 시스템 경계, 아홉 단계 정상 경로, 권위 자료, 대표 실패와 대응
- 운영 모형: 핵심 용어, 책임 영역, 공동 품질 계획, 전문가 구성, 인계
- 대표 미션: 정상 실행과 C1 실패, C2 교정, 새 판정, 포장
- 런타임: 대표 미션 단계와 논리 구성 요소, 상태·자료 흐름의 대응
- 신뢰성: 완료 조건, 실패 주입, 재시도, 체크포인트, 중복 억제, 무효화
- 신뢰 경계: 내부 강제 범위, 외부 통제, 남은 불확실성
- 참고 자료: 용어, 기록 종류, 상태, 스키마, 코드·시험 색인
- 결정 이력: 채택 이유, 대안, 결과
- 조사 기록: 외부 방법의 원문 근거와 적용 차이

Temporal은 workflow 용어를 정의한 뒤 사건 이력과 재생을 설명하고,[29] Dapr는 workflow 개요에서 기능뿐 아니라 생명주기·제한·보안·다음 읽을 자료를 함께 제시한다.[31] 이 방식에 따라 개요에는 정상 실행과 복구의 핵심 결론만 남기고, 같은 대표 미션의 독자용 흐름은 `worked-mission-overview.md`, 구성 요소 대응은 `runtime-overview.md`, 실패 주입과 복구는 `reliability.md`에서 각각 설명한다.

### 2.10 구조의 역사적 기반을 하네스 판본 이력과 구분한다

후반부 `Prior Work` 장은 하네스 판본 연혁이 아니라 설계 철학의 계보를 설명한다. 정형 검토는 Fagan의 설계·코드 검사,[33] 권한 분리는 Saltzer와 Schroeder의 보호 원칙,[35] 위험 중심 반복은 Boehm의 나선형 모델에서 각각 핵심 원리를 가져온다.[34]

NASA 시스템공학 안내서는 이해관계자 기대·기술 요구·구현·통합·검증·유효성 확인·위험·형상 관리를 생명주기 전반의 서로 다른 활동으로 다룬다.[32]

Agile Manifesto·TDD·지속적 통합은 변경에 대한 짧은 피드백과 실행 가능한 결과를 강조한다.[36][41][43]

Event Sourcing은 상태 변경을 순서가 있는 사건으로 보존하는 발상을 제공한다.[42]

Microsoft SDL과 NIST SSDF는 보안을 마지막 별도 검사로 두지 않고 여러 개발 방식에 통합한다.[37][38]

in-toto와 SLSA는 누가 어떤 순서로 무엇을 만들었는지와 소스에서 산출물까지의 계보를 연결한다.[39][40]

Temporal·DBOS·Dapr의 내구성 실행은 사건 이력·작업 ID·체크포인트·재개·중복 억제를 장시간 에이전트 작업에 적용할 근거를 제공한다.[29][30][31]

문서에서는 이들을 단순 연표로 나열하지 않는다. 각 참조 모델이 원래 해결한 문제와 직접 뒷받침하는 방법, 하네스가 그 방법을 규칙으로 채택했는지 또는 설계 참고 자료로만 사용하는지, LLM 에이전트 환경에서 바꾼 부분, 채택하지 않은 가정을 함께 설명한다.

### 2.11 정상 흐름과 실패 흐름은 같은 예시를 재사용한다

워크플로 제품 문서를 비교한 결과, 처음부터 모든 실패 종류를 표로 나열하는 방식보다 하나의 정상 실행을 보여 준 뒤 같은 실행에 실패를 주입하는 방식이 더 명확했다. DBOS는 체크아웃 예시의 정상 처리와 결제 뒤 중단을 이어서 설명하고, 저장된 단계 결과로 어디에서 재개하는지 별도 구조 문서에서 확장한다.[46][47]

Temporal은 제품 정의 단계에서부터 충돌·네트워크 장애·중단 뒤 재개를 가치 제안과 함께 설명한다.[45] Dapr는 activity의 적어도 한 번 실행 가능성을 설명하는 자리에서 중복 실행에 안전한 동작을 함께 요구한다.[48]

Argo Workflows는 작은 실행 가능한 예를 다루는 핵심 개념 문서와 controller·pod·reconciliation을 다루는 내부 구조 문서를 분리하고, 재시도 정책도 별도 예시로 설명한다.[49][50]

이에 따라 하네스 문서는 `export-ownership` 예시를 정상 독해 경로 전체에서 재사용한다.

- 개요와 `architecture-at-a-glance.md`: 정상 흐름의 축약과 시스템 경계
- `worked-mission-overview.md`: 같은 미션의 아홉 단계, C1 보류, C2 교정, 새 판정과 포장
- `runtime-overview.md`: 같은 단계와 논리 구성 요소·권위 자료의 대응
- `reliability.md`: 프로세스 중단, 중복 결과, 불확실한 외부 효과, 품질 실패, 완료 무효화 주입
- `trust.md`: 같은 요청, 후보본, QA 자료, 외부 저장소 응답이 통과하는 신뢰 경계

예시 식별자와 후보본 관계를 유지해 독자가 정상 흐름과 복구 흐름을 서로 다른 시스템으로 오해하지 않게 한다.

### 2.12 전체 문서는 공개 기술 문서의 독자 동선을 따른다

Backstage와 Kubernetes는 구성 요소 백과보다 용어와 단순한 전체 그림을 먼저 보여 주고,[19][15] GitLab은 단순 구조도 뒤에 실제 요청 흐름을 둔다.[14]

Prometheus는 제품 정의와 구성 요소를 설명한 뒤 적합한 경우와 부적합한 경우를 분리하고,[44] OpenTelemetry는 문서 목적과 핵심 용어를 첫 문장에서 밝힌다.[20]

Airflow는 사용자 개념과 대표 실행을 런타임 상세보다 앞에 둔다.[21]

Temporal과 DBOS도 제품 약속과 대표 실행을 먼저 보여 준 뒤 런타임·재시도·복구의 상세로 내려간다.[45][46][47]

공식 엔지니어링 글도 같은 원칙을 더 압축해서 쓴다. Cloudflare의 Pingora 글은 기존 프록시 한계에서 설계 선택과 운영 결과로 진행하고,[51] GitHub의 데이터베이스 분할 글은 실제 확장 압력·대안·무중단 전환·결과를 한 흐름으로 묶는다.[52] Slack의 셀 구조 글은 실제 장애에서 설계 목표, 대안의 한계, 구조 변경, 검증 결과로 이어진다.[53]

따라서 하네스 합본의 기본 독해 순서는 `Purpose and Scope → Architecture at a Glance → Core Concepts and Operating Model → Worked Mission → Runtime Architecture → Reliability → Trust Boundaries → Prior Work → Reference and Next Reading`으로 고정한다. 첫 구조도와 대표 미션을 선행 연구나 상세 사건표보다 앞에 두고, 35개 사건·상태 기계·스키마·출처별 귀속은 연결된 심층 문서에 둔다. 본문과 심층 자료를 함께 보존하되, 처음 읽는 독자에게 후자를 선행 조건으로 요구하지 않는다.

## 3. 채택할 구조도 묶음

| ID | 질문 | 주 독자 | 주 문서 | 한 문장 결론 |
|---|---|---|---|---|
| 01 | 문제 | 모든 독자 | `architecture.md` | 문제는 에이전트 수가 아니라 실행하지 않은 완료 주장과 검증되지 않은 상태 전이다 |
| 02 | 전체 그림 | 모든 독자 | `architecture/architecture-at-a-glance.md` | 정책 경계, 논리 책임, 정상 경로와 권위 자료를 한눈에 이해한다 |
| 03 | 운영 모형 | 사용자·운영자 | `architecture/operating-model-overview.md` | 세 책임 영역은 품질을 함께 계획하고 구현과 최종 판정에서는 분리된다 |
| 04 | 하나의 미션 | 모든 독자 | `architecture/worked-mission-overview.md` | 구체적인 예를 따라 요구·구현·후보본·검증·판정·포장의 연결을 이해한다 |
| 05 | 규칙 강제 구조 | 개발자·운영자 | `architecture/runtime-overview.md` | 논리 구성 요소는 독립 배포가 아니라 규칙 강제와 내구 상태가 필요한 경계에서 나뉜다 |
| 06 | 완료와 복구 | 품질·보안·운영 담당 | `architecture/reliability.md` | 완료는 필수 근거에서 도출하며 중단 뒤에는 검증된 작업을 재사용한다 |
| 07 | 신뢰 경계 | 모든 독자 | `architecture/trust.md` | 하네스가 강제하는 범위와 운영체제·외부 서비스에 필요한 통제를 구분한다 |
| 08 | 선행 연구 | 설계자·검토자 | `architecture/prior-work-overview.md` | 직접 지원되는 방법, 규칙 채택 여부, 설계 참고 관계와 하네스 고유 확장을 구분한다 |
| 09 | 참고와 다음 읽기 | 모든 독자 | `architecture/reference.md` | 심층 문서·용어·스키마·코드·시험과 역할별 다음 경로를 찾는다 |

## 4. 문서 표기 규칙

### 4.1 목표 설계의 범위

구조 문서는 목표 설계를 설명하며, 현재 구현을 인증하거나 출시 가능 상태를 주장하지 않는다. 구현 여부와 시험 결과는 코드 검토·시험·출시 근거에서 별도로 판정한다. 구조 문서에서는 하네스가 직접 강제하는 규칙과 운영체제·외부 서비스에 맡기는 통제를 구분한다.

### 4.2 선과 경계

- 실선 화살표: 실행·자료 전달
- 점선 화살표: 검토·판정·감시
- 빨간 경계: 다른 권한·작업 공간·신뢰 수준
- 양방향 선: 단순 대화가 아니라 정형 제안·이견·결정 기록
- 번호가 있는 화살표: 중요한 런타임 순서

### 4.3 구성 요소 표

모든 상자에는 문서에서 다음 정보를 제공한다.

- 책임
- 받는 입력
- 만드는 출력
- 읽고 쓰는 자료
- 허용된 동작
- 금지된 동작
- 실패할 때 영향
- 검증 방법
- 목표 설계인지 외부 통제인지에 대한 범위

## 5. 산출물 계획

1. `docs/architecture.md`: 처음 보는 사용자를 위한 5분 구조 개요와 독자별 다음 문서
2. `docs/architecture/overview-and-scope.md`, `architecture-at-a-glance.md`: 문제·범위·전체 구조와 정상 경로
3. `docs/architecture/operating-model-overview.md`, `worked-mission-overview.md`, `runtime-overview.md`: 핵심 개념과 대표 미션의 점진적 설명
4. `docs/architecture/reliability.md`, `trust.md`: 같은 미션에 대한 실패·복구·신뢰 경계
5. `docs/architecture/prior-work-overview.md`, `reference.md`: 후반 설계 근거와 역할별 다음 읽기
6. `docs/architecture/operating-model.md`, `worked-mission.md`, `runtime.md`, `prior-work.md`: 운영 규칙·35개 사건·상태 기계·출처 귀속을 보존하는 심층 문서
7. `docs/agent-harness-architecture.html`: 아홉 장의 기본 독해 경로와 심층 문서 링크를 한 페이지에서 제공하는 구조 안내서
8. `docs/adr/README.md`와 개별 ADR: 구조 결정 목록과 대체 관계

구조 문서는 목표 설계와 보장 범위를 설명한다. 구현 여부와 출시 가능성은 코드 경로·시험·독립 검토에 결속된 별도 근거로 판정한다.

## Sources

[1] https://c4model.com
[2] https://c4model.com/diagrams
[3] https://c4model.com/diagrams/system-context
[4] https://c4model.com/diagrams/container
[5] https://c4model.com/diagrams/dynamic
[6] https://developers.google.com/tech-writing/two/illustrations
[7] https://developers.google.com/tech-writing/two/large-docs
[8] https://cloud.google.com/architecture/framework
[9] https://aws.amazon.com/architecture
[10] https://aws.amazon.com/architecture/icons
[11] https://learn.microsoft.com/en-us/azure/architecture/guide — Azure application architecture fundamentals
[12] https://learn.microsoft.com/en-us/azure/architecture/browse
[13] https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
[14] https://docs.gitlab.com/development/architecture — GitLab architecture overview
[15] https://kubernetes.io/docs/concepts/overview/components — Kubernetes Components
[16] https://docs.temporal.io/temporal-service/temporal-server
[17] https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/introduction.html
[18] https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html
[19] https://backstage.io/docs/overview/architecture-overview
[20] https://opentelemetry.io/docs/specs/otel/overview
[21] https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html
[22] https://argo-workflows.readthedocs.io/en/latest/architecture
[23] https://diataxis.fr
[24] https://docs.arc42.org/home
[25] https://rustc-dev-guide.rust-lang.org/overview.html
[26] https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy
[27] https://www.envoyproxy.io/docs/envoy/latest/intro/life_of_a_request
[28] https://docs.dbos.dev
[29] https://docs.temporal.io/workflows
[30] https://docs.dbos.dev/python/tutorials/workflow-tutorial
[31] https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-overview
[32] https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf
[33] https://doi.org/10.1147/sj.153.0182
[34] https://doi.org/10.1109/2.59
[35] https://doi.org/10.1109/PROC.1975.9939
[36] https://agilemanifesto.org
[37] https://www.microsoft.com/en-us/securityengineering/sdl
[38] https://csrc.nist.gov/pubs/sp/800/218/final
[39] https://in-toto.io
[40] https://slsa.dev/spec/v1.2/about
[41] https://martinfowler.com/articles/continuousIntegration.html
[42] https://martinfowler.com/eaaDev/EventSourcing.html
[43] https://agilealliance.org/glossary/tdd
[44] https://prometheus.io/docs/introduction/overview — Overview | Prometheus
[45] https://docs.temporal.io/temporal — What is Temporal?
[46] https://docs.dbos.dev/why-dbos — Why DBOS?
[47] https://docs.dbos.dev/architecture — DBOS Architecture
[48] https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-features-concepts — Dapr Workflow features and concepts
[49] https://argo-workflows.readthedocs.io/en/latest/workflow-concepts — Argo Workflows Core Concepts
[50] https://argo-workflows.readthedocs.io/en/latest/retries — Argo Workflows retries
[51] https://blog.cloudflare.com/how-we-built-pingora-the-proxy-that-connects-cloudflare-to-the-internet/ — How we built Pingora, the proxy that connects Cloudflare to the Internet
[52] https://github.blog/engineering/infrastructure/partitioning-githubs-relational-databases-scale/ — Partitioning GitHub’s relational databases to handle scale
[53] https://slack.engineering/slacks-migration-to-a-cellular-architecture/ — Slack’s Migration to a Cellular Architecture
