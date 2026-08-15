from dataclasses import replace

import pytest

from agent_harness.methodology import (
    AssuranceClaim,
    DeliveryDepth,
    GoalDefinition,
    KnowledgeStatus,
    MethodologyPlanner,
    ResponsibilityArea,
    StageKind,
    Track,
)


def baseline_goal() -> GoalDefinition:
    return GoalDefinition(
        statement="명시된 변환기를 구현한다",
        decision_action="배포 여부를 결정한다",
        outcome="정확한 변환 결과",
        population="입력 파일",
        analysis_unit="파일 하나",
        time_horizon="실행 시점",
        constraints=("네트워크 사용 금지",),
        question_type="implementation",
        data_description="고정 입력과 수락 기준",
        decision_threshold="모든 수락 시험 통과",
        field_status={},
        risk_level=1,
        research_artifact=False,
    )


def test_ambiguous_goal_opens_discovery_and_assigns_method_experts() -> None:
    goal = GoalDefinition(
        statement="품질을 높일 수 있는 좋은 방법을 찾아 구현한다",
        decision_action=None,
        outcome=None,
        population="서비스 사용자",
        analysis_unit=None,
        time_horizon=None,
        constraints=(),
        question_type=None,
        data_description=None,
        decision_threshold=None,
        field_status={
            "decision_action": KnowledgeStatus.UNVERIFIED,
            "outcome": KnowledgeStatus.UNVERIFIED,
            "question_type": KnowledgeStatus.CONFLICT,
            "data_description": KnowledgeStatus.UNVERIFIED,
        },
        risk_level=1,
        research_artifact=False,
    )

    plan = MethodologyPlanner().plan(goal)

    assert plan.track is Track.EXPLORATION
    assert plan.stages[0].kind is StageKind.SCOPE_RISK
    assert StageKind.GOAL_DISCOVERY in plan.stage_kinds
    assert StageKind.METHOD_DISCOVERY in plan.stage_kinds
    method_stage = plan.stage(StageKind.METHOD_DISCOVERY)
    assert {
        "domain-researcher",
        "methodologist",
        "metric-specialist",
        "bias-reviewer",
    }.issubset(method_stage.roles)
    assert "unresolved outcome" in plan.reasons
    assert "conflicting question_type" in plan.reasons


def test_research_artifact_adds_all_noncompensating_claims_and_high_risk_roles() -> None:
    goal = GoalDefinition(
        statement="논문의 핵심 표를 생성하는 분석 파이프라인을 구현한다",
        decision_action="논문 결과를 제출할지 결정한다",
        outcome="승인된 통계 추정량과 표",
        population="연구 대상 모집단",
        analysis_unit="독립 실험 반복",
        time_horizon="평가 시점",
        constraints=("자료 누수 금지", "승인하지 않은 네트워크 효과 금지"),
        question_type="comparison",
        data_description="고정 판본의 원자료와 사전 정의 분할",
        decision_threshold="사전 정의한 허용오차 안에서 주요 결론 유지",
        field_status={},
        risk_level=3,
        research_artifact=True,
    )

    plan = MethodologyPlanner().plan(goal)

    assert plan.required_assurance_claims == frozenset(AssuranceClaim)
    assert plan.noncompensating_assurance is True
    assert {
        "security-architect",
        "domain-specialist",
        "formal-methods-specialist",
    }.issubset(plan.stage(StageKind.DESIGN).roles)
    assert {
        "independent-spec-reviewer",
        "independent-code-reviewer",
        "research-reproducibility-reviewer",
    }.issubset(plan.stage(StageKind.VALIDATION).roles)


@pytest.mark.parametrize(
    "missing_field",
    [
        "decision_action",
        "outcome",
        "population",
        "analysis_unit",
        "time_horizon",
        "constraints",
        "question_type",
        "data_description",
        "decision_threshold",
    ],
)
def test_any_missing_goal_field_opens_exploration(missing_field: str) -> None:
    complete = GoalDefinition(
        statement="변환기를 구현한다",
        decision_action="배포한다",
        outcome="정확한 변환",
        population="입력 파일",
        analysis_unit="파일 하나",
        time_horizon="실행 시점",
        constraints=("네트워크 금지",),
        question_type="implementation",
        data_description="고정 예제",
        decision_threshold="모든 시험 통과",
        field_status={},
    )
    missing_value = () if missing_field == "constraints" else None

    plan = MethodologyPlanner().plan(
        replace(complete, **{missing_field: missing_value})  # type: ignore[arg-type]
    )

    assert plan.track is Track.EXPLORATION
    assert f"unresolved {missing_field}" in plan.reasons


def test_each_stage_declares_artifacts_permissions_gate_and_return_point() -> None:
    goal = GoalDefinition(
        statement="변환기를 구현한다",
        decision_action="배포한다",
        outcome="정확한 변환",
        population="입력 파일",
        analysis_unit="파일 하나",
        time_horizon="실행 시점",
        constraints=("네트워크 금지",),
        question_type="implementation",
        data_description="고정 예제",
        decision_threshold="모든 시험 통과",
        field_status={},
    )

    plan = MethodologyPlanner().plan(goal)

    assert plan.track is Track.PRODUCTION
    for index, stage in enumerate(plan.stages):
        assert stage.required_inputs
        assert stage.required_outputs
        assert stage.gate_criteria
        assert set(stage.role_permissions) == set(stage.roles)
        for profile in stage.role_permissions.values():
            assert profile.tools
            assert profile.writable_areas
            assert profile.network_allowed is False
        if index == 0:
            assert stage.failure_return is None
        else:
            assert stage.failure_return in plan.stage_kinds[:index]


def test_each_dynamic_specialist_combines_three_knowledge_layers() -> None:
    plan = MethodologyPlanner().plan(baseline_goal())

    for stage in plan.stages:
        assert set(stage.expert_profiles) == set(stage.roles)
        shared_foundations = {
            profile.shared_foundation for profile in stage.expert_profiles.values()
        }
        assert len(shared_foundations) == 1
        for role, profile in stage.expert_profiles.items():
            assert profile.role == role
            assert profile.stage is stage.kind
            assert profile.general_practice
            assert profile.domain_depth
            assert profile.role_judgment
            assert profile.shared_foundation


def test_risk_and_research_create_needed_specialists_with_deeper_shared_knowledge() -> None:
    low = MethodologyPlanner().plan(baseline_goal())
    high_research = MethodologyPlanner().plan(
        replace(baseline_goal(), risk_level=3, research_artifact=True)
    )

    low_validation = low.stage(StageKind.VALIDATION)
    high_validation = high_research.stage(StageKind.VALIDATION)
    assert len(high_validation.expert_profiles) > len(low_validation.expert_profiles)
    assert "formal-methods-specialist" in high_research.stage(StageKind.DESIGN).expert_profiles
    for stage in high_research.stages:
        for profile in stage.expert_profiles.values():
            assert "research methodology and reproducibility" in profile.domain_depth
            assert "secure software engineering" in profile.domain_depth


def test_validator_has_independent_judgment_knowledge_not_only_execution_skills() -> None:
    plan = MethodologyPlanner().plan(baseline_goal())
    validator = plan.stage(StageKind.VALIDATION).expert_profiles["validation-specialist"]

    assert "independent evidence judgment" in validator.role_judgment
    assert "reject unsupported completion claims" in validator.role_judgment


def test_every_plan_has_the_three_exact_responsibility_areas() -> None:
    plan = MethodologyPlanner().plan(baseline_goal())

    assert {area.value for area in plan.responsibility_areas} == {
        "Requirements and Outcomes",
        "Engineering and Software Delivery",
        "Verification and Quality Assurance",
    }
    assert plan.responsibility_areas == frozenset(ResponsibilityArea)


def test_perspectives_precede_expert_grouping_and_keep_orthogonal_participation() -> None:
    plan = MethodologyPlanner().plan(baseline_goal())

    assert {
        "user-purpose",
        "computer-science",
        "functional-correctness",
        "quality-assurance",
        "baseline-security",
        "data-integrity",
        "usability-accessibility",
        "performance-resources",
        "operations-recovery",
        "maintainability-supply-chain",
        "documentation",
        "domain-knowledge",
        "research-methods-metrics",
        "external-effects",
    }.issubset(plan.perspectives)
    for perspective in plan.perspectives.values():
        assert perspective.delivery_depth in set(DeliveryDepth)
        assert isinstance(perspective.independent_assessment_required, bool)
        assert isinstance(perspective.bounded_investigation_required, bool)
        assert perspective.rationale
        assert perspective.required_outputs
        assert perspective.verification_methods
        assert perspective.responsibility_area in plan.responsibility_areas


def test_risk_changes_participation_dimensions_without_turning_them_into_a_rank() -> None:
    low = MethodologyPlanner().plan(baseline_goal())
    high = MethodologyPlanner().plan(replace(baseline_goal(), risk_level=3))

    low_security = low.perspectives["baseline-security"]
    high_security = high.perspectives["baseline-security"]
    assert low_security.delivery_depth is DeliveryDepth.P1
    assert low_security.independent_assessment_required is False
    assert high_security.delivery_depth is DeliveryDepth.P3
    assert high_security.independent_assessment_required is True
    assert high_security.bounded_investigation_required is True


def test_experts_reference_structured_shared_knowledge_and_one_responsibility_area() -> None:
    plan = MethodologyPlanner().plan(baseline_goal())

    assert plan.knowledge_base
    for concept_id, concept in plan.knowledge_base.items():
        assert concept.concept_id == concept_id
        assert concept.name
        assert concept.version
        assert concept.source
        assert concept.scope
    for stage in plan.stages:
        for role, profile in stage.expert_profiles.items():
            if role == "mission-manager":
                assert profile.responsibility_area is None
            else:
                assert profile.responsibility_area in plan.responsibility_areas
            assert set(profile.shared_foundation).issubset(plan.knowledge_base)
