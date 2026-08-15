import hashlib
from pathlib import Path

import pytest

from agent_harness.expert_handoff import (
    ExpertHandoff,
    ExpertHandoffValidator,
    HandoffKnowledgeError,
    ReceiverAcceptance,
)
from agent_harness.methodology import GoalDefinition, MethodologyPlanner


def baseline_goal() -> GoalDefinition:
    return GoalDefinition(
        statement="implement a traceable software workflow",
        decision_action="decide whether to release it",
        outcome="a verified package and evidence bundle",
        population="candidate source trees",
        analysis_unit="one frozen candidate",
        time_horizon="one mission revision",
        constraints=("Python 3.11",),
        question_type="implementation",
        data_description="fixed candidate inputs and acceptance criteria",
        decision_threshold="all applicable must-pass criteria pass",
        field_status={},
        risk_level=1,
        research_artifact=False,
    )


def test_common_knowledge_handoff_is_schema_checked_and_artifact_verified(
    tmp_path: Path,
) -> None:
    plan = MethodologyPlanner().plan(baseline_goal())
    sender = plan.stages[0].expert_profiles["risk-analyst"]
    receiver = plan.stage_kinds[1]
    receiver_profile = plan.stages[1].expert_profiles[
        next(role for role in plan.stages[1].roles if role != "mission-manager")
    ]
    artifact = tmp_path / "risk.json"
    artifact.write_text('{"risk":"bounded"}\n', encoding="utf-8")
    shared = tuple(sorted(set(sender.shared_foundation) & set(receiver_profile.shared_foundation)))
    assert shared

    handoff = ExpertHandoff.create(
        mission_id="mis-knowledge",
        revision=1,
        task_id="task-risk",
        stage=sender.stage,
        candidate_id=None,
        sender=sender,
        receiver=receiver_profile,
        shared_foundation=shared,
        artifacts=(
            {
                "path": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "media_type": "application/json",
            },
        ),
        work_performed=("classified mission risk",),
        decisions=("continue with production plan",),
        assumptions=(),
        unresolved=(),
        next_actions=(f"continue at {receiver.value}",),
        receiver_acceptance=ReceiverAcceptance(
            receiver_expert_id=receiver_profile.expert_id,
            usable_without_rework=True,
            reasons=(),
        ),
    )

    ExpertHandoffValidator().validate_and_verify(
        handoff.document(), tmp_path, plan.knowledge_base
    )


def test_handoff_rejects_unknown_or_unshared_concept(tmp_path: Path) -> None:
    plan = MethodologyPlanner().plan(baseline_goal())
    sender = plan.stages[0].expert_profiles["risk-analyst"]
    receiver = plan.stages[1].expert_profiles[
        next(role for role in plan.stages[1].roles if role != "mission-manager")
    ]
    artifact = tmp_path / "risk.json"
    artifact.write_text("{}\n", encoding="utf-8")
    handoff = ExpertHandoff.create(
        mission_id="mis-knowledge",
        revision=1,
        task_id="task-risk",
        stage=sender.stage,
        candidate_id=None,
        sender=sender,
        receiver=receiver,
        shared_foundation=("concept:structured-handoff",),
        artifacts=(
            {
                "path": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "media_type": "application/json",
            },
        ),
        work_performed=("classified mission risk",),
        decisions=("continue",),
        assumptions=(),
        unresolved=(),
        next_actions=("continue",),
        receiver_acceptance=ReceiverAcceptance(
            receiver_expert_id=receiver.expert_id,
            usable_without_rework=True,
            reasons=(),
        ),
    )

    document = handoff.document()
    document["shared_foundation"] = ["concept:not-issued"]
    with pytest.raises(HandoffKnowledgeError, match="shared foundation"):
        ExpertHandoffValidator().validate_and_verify(
            document, tmp_path, plan.knowledge_base
        )


def test_handoff_creation_rejects_concept_not_shared_by_both_experts() -> None:
    plan = MethodologyPlanner().plan(baseline_goal())
    sender = plan.stages[0].expert_profiles["risk-analyst"]
    receiver = plan.stages[1].expert_profiles[
        next(role for role in plan.stages[1].roles if role != "mission-manager")
    ]
    receiver_only = receiver.__class__(
        **{
            **receiver.__dict__,
            "shared_foundation": ("concept:structured-handoff",),
        }
    )

    with pytest.raises(HandoffKnowledgeError, match="sender and receiver"):
        ExpertHandoff.create(
            mission_id="mis-knowledge",
            revision=1,
            task_id="task-risk",
            stage=sender.stage,
            candidate_id=None,
            sender=sender,
            receiver=receiver_only,
            shared_foundation=("concept:evidence-reasoning",),
            artifacts=(
                {
                    "path": "risk.json",
                    "sha256": "0" * 64,
                    "media_type": "application/json",
                },
            ),
            work_performed=("classified mission risk",),
            decisions=("continue",),
            assumptions=(),
            unresolved=(),
            next_actions=("continue",),
            receiver_acceptance=ReceiverAcceptance(
                receiver_expert_id=receiver_only.expert_id,
                usable_without_rework=True,
                reasons=(),
            ),
        )