# 구조 결정 기록

구조 결정 기록은 하네스의 중요한 설계 선택에 대해 **왜 그 결정을 했는지** 보존한다.

## 규칙

- 상태는 `proposed`, `accepted`, `rejected`, `superseded` 중 하나다.
- `accepted` 또는 `rejected` 기록의 결정 내용을 직접 바꾸지 않는다.
- 새 정보로 결정을 바꿀 때는 새 번호의 기록을 만들고 기존 기록을 `superseded`로 표시한다.
- `accepted`는 설계를 합의했다는 뜻이며 구현 완료를 뜻하지 않는다. 구현 완료는 현재 소스에 결속된 시험과 독립 검토 근거로 별도 판정한다.

## 목록

| ID | 제목 | 결정 상태 |
|---|---|---|
| [0001](0001-three-responsibility-axes.md) | 세 책임 축과 총괄 관리자 | accepted |
| [0002](0002-perspective-first-expert-generation.md) | 필수 관점 우선 전문가 생성 | accepted |
| [0003](0003-quality-and-handoff.md) | 동적 품질 프로필과 이중 인계 수락 | accepted |
| [0004](0004-evidence-backed-completion.md) | 근거 기반 완료와 중단 복구 | accepted |
