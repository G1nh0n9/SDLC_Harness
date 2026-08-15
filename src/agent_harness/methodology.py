from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum


class KnowledgeStatus(StrEnum):
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    UNVERIFIED = "unverified"
    CONFLICT = "conflict"


class Track(StrEnum):
    EXPLORATION = "exploration"
    PRODUCTION = "production"


class StageKind(StrEnum):
    SCOPE_RISK = "scope-risk"
    GOAL_DISCOVERY = "goal-discovery"
    METHOD_DISCOVERY = "method-discovery"
    REQUIREMENTS = "requirements"
    ORACLE = "oracle"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    INTEGRATION_VERIFICATION = "integration-verification"
    VALIDATION = "validation"
    RELEASE = "release"


class AssuranceClaim(StrEnum):
    METHOD_VALIDITY = "method-validity"
    ALGORITHM_FIDELITY = "algorithm-fidelity"
    METRIC_VALIDITY = "metric-validity"
    EXPERIMENT_INTEGRITY = "experiment-integrity"
    REPRODUCIBILITY_LINEAGE = "reproducibility-lineage"
    SCOPE_PURITY = "scope-purity"


class ResponsibilityArea(StrEnum):
    REQUIREMENTS_OUTCOMES = "Requirements and Outcomes"
    ENGINEERING_DELIVERY = "Engineering and Software Delivery"
    VERIFICATION_QA = "Verification and Quality Assurance"


class DeliveryDepth(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


@dataclass(frozen=True)
class GoalDefinition:
    statement: str
    decision_action: str | None
    outcome: str | None
    population: str | None
    analysis_unit: str | None
    time_horizon: str | None
    constraints: tuple[str, ...]
    question_type: str | None
    data_description: str | None
    decision_threshold: str | None
    field_status: Mapping[str, KnowledgeStatus] = field(default_factory=dict)
    risk_level: int = 1
    research_artifact: bool = False


@dataclass(frozen=True)
class StagePermissionProfile:
    tools: frozenset[str]
    writable_areas: frozenset[str]
    network_allowed: bool
    can_execute_commands: bool
    can_approve: bool


@dataclass(frozen=True)
class KnowledgeConcept:
    concept_id: str
    name: str
    version: str
    source: str
    scope: str


@dataclass(frozen=True)
class PerspectiveProfile:
    perspective_id: str
    responsibility_area: ResponsibilityArea
    delivery_depth: DeliveryDepth
    independent_assessment_required: bool
    bounded_investigation_required: bool
    rationale: str
    required_outputs: tuple[str, ...]
    verification_methods: tuple[str, ...]


@dataclass(frozen=True)
class ExpertProfile:
    expert_id: str
    role: str
    stage: StageKind
    general_practice: tuple[str, ...]
    domain_depth: tuple[str, ...]
    role_judgment: tuple[str, ...]
    shared_foundation: tuple[str, ...]
    responsibility_area: ResponsibilityArea | None


@dataclass(frozen=True)
class StagePlan:
    kind: StageKind
    role_permissions: Mapping[str, StagePermissionProfile]
    required_inputs: frozenset[str]
    required_outputs: frozenset[str]
    gate_criteria: tuple[str, ...]
    failure_return: StageKind | None
    expert_profiles: Mapping[str, ExpertProfile] = field(default_factory=dict)

    @property
    def roles(self) -> frozenset[str]:
        return frozenset(self.role_permissions)


@dataclass(frozen=True)
class WorkflowPlan:
    track: Track
    stages: tuple[StagePlan, ...]
    reasons: tuple[str, ...]
    required_assurance_claims: frozenset[AssuranceClaim] = frozenset()
    noncompensating_assurance: bool = False
    responsibility_areas: frozenset[ResponsibilityArea] = frozenset(ResponsibilityArea)
    perspectives: Mapping[str, PerspectiveProfile] = field(default_factory=dict)
    knowledge_base: Mapping[str, KnowledgeConcept] = field(default_factory=dict)

    @property
    def stage_kinds(self) -> tuple[StageKind, ...]:
        return tuple(stage.kind for stage in self.stages)

    def stage(self, kind: StageKind) -> StagePlan:
        for stage in self.stages:
            if stage.kind is kind:
                return stage
        raise KeyError(kind)


class MethodologyPlanner:
    _general_practice = (
        "structured technical writing",
        "evidence-based research and source evaluation",
        "critical reasoning and uncertainty reporting",
        "clear inter-specialist handoff",
    )

    _knowledge_base: Mapping[str, KnowledgeConcept] = {
        "concept:structured-writing": KnowledgeConcept(
            concept_id="concept:structured-writing",
            name="Structured technical writing",
            version="1",
            source="expert-organization-design.md#general-method-knowledge",
            scope="all workflow phases",
        ),
        "concept:evidence-reasoning": KnowledgeConcept(
            concept_id="concept:evidence-reasoning",
            name="Evidence reasoning and uncertainty",
            version="1",
            source="expert-organization-design.md#general-method-knowledge",
            scope="all workflow phases",
        ),
        "concept:software-engineering": KnowledgeConcept(
            concept_id="concept:software-engineering",
            name="Computer science and software engineering foundations",
            version="1",
            source="expert-organization-design.md#domain-knowledge",
            scope="software development work",
        ),
        "concept:structured-handoff": KnowledgeConcept(
            concept_id="concept:structured-handoff",
            name="Structured handoff and receiver acceptance",
            version="1",
            source="expert-organization-design.md#shared-knowledge-communication",
            scope="inter-specialist handoff",
        ),
        "concept:secure-engineering": KnowledgeConcept(
            concept_id="concept:secure-engineering",
            name="Secure software engineering",
            version="1",
            source="expert-organization-design.md#domain-knowledge",
            scope="risk level two and above",
        ),
        "concept:research-reproducibility": KnowledgeConcept(
            concept_id="concept:research-reproducibility",
            name="Research methodology and reproducibility",
            version="1",
            source="expert-organization-design.md#domain-knowledge",
            scope="research artifacts",
        ),
    }

    _stage_domain_depth: Mapping[StageKind, tuple[str, ...]] = {
        StageKind.SCOPE_RISK: ("systems thinking and risk analysis",),
        StageKind.GOAL_DISCOVERY: ("goal discovery and decision analysis",),
        StageKind.METHOD_DISCOVERY: ("scientific method and comparative methodology",),
        StageKind.REQUIREMENTS: ("requirements engineering and acceptance criteria",),
        StageKind.ORACLE: ("implementation-independent oracle and test design",),
        StageKind.DESIGN: ("computer science and software architecture",),
        StageKind.IMPLEMENTATION: ("computer science and software construction",),
        StageKind.INTEGRATION_VERIFICATION: ("software testing and execution analysis",),
        StageKind.VALIDATION: ("software validation and assurance review",),
        StageKind.RELEASE: ("release engineering and operational risk",),
    }

    _critical_fields = (
        "decision_action",
        "outcome",
        "population",
        "analysis_unit",
        "time_horizon",
        "constraints",
        "question_type",
        "data_description",
        "decision_threshold",
    )

    _stage_artifacts: Mapping[StageKind, tuple[frozenset[str], frozenset[str]]] = {
        StageKind.SCOPE_RISK: (
            frozenset({"goal-draft"}),
            frozenset({"scope-risk-assessment"}),
        ),
        StageKind.GOAL_DISCOVERY: (
            frozenset({"goal-draft", "scope-risk-assessment"}),
            frozenset({"goal-definition"}),
        ),
        StageKind.METHOD_DISCOVERY: (
            frozenset({"goal-definition", "scope-risk-assessment"}),
            frozenset({"method-decision"}),
        ),
        StageKind.REQUIREMENTS: (
            frozenset({"goal-definition", "method-decision"}),
            frozenset({"requirements-baseline"}),
        ),
        StageKind.ORACLE: (
            frozenset({"requirements-baseline"}),
            frozenset({"acceptance-oracle"}),
        ),
        StageKind.DESIGN: (
            frozenset({"requirements-baseline", "acceptance-oracle"}),
            frozenset({"design-baseline"}),
        ),
        StageKind.IMPLEMENTATION: (
            frozenset({"requirements-baseline", "acceptance-oracle", "design-baseline"}),
            frozenset({"implementation-artifacts"}),
        ),
        StageKind.INTEGRATION_VERIFICATION: (
            frozenset({"frozen-candidate", "acceptance-oracle"}),
            frozenset({"verification-evidence"}),
        ),
        StageKind.VALIDATION: (
            frozenset({"frozen-candidate", "verification-evidence"}),
            frozenset({"review-findings"}),
        ),
        StageKind.RELEASE: (
            frozenset({"approved-candidate", "gate-decision"}),
            frozenset({"release-decision"}),
        ),
    }

    @staticmethod
    def _permission(stage: StageKind) -> StagePermissionProfile:
        command_stages = {
            StageKind.ORACLE,
            StageKind.IMPLEMENTATION,
            StageKind.INTEGRATION_VERIFICATION,
            StageKind.RELEASE,
        }
        approval = stage is StageKind.VALIDATION
        tools = {"read-input", "write-result"}
        writable = {"work", "tmp"}
        if stage is StageKind.IMPLEMENTATION:
            tools.update({"write-file", "run-tests"})
            writable.add("build")
        elif stage is StageKind.INTEGRATION_VERIFICATION:
            tools.update({"read-candidate", "run-tests", "write-evidence"})
            writable.add("build")
        elif approval:
            tools.update({"read-candidate", "read-evidence", "write-finding", "approve"})
        elif stage is StageKind.RELEASE:
            tools.update({"read-approved-candidate", "package"})
            writable.add("build")
        return StagePermissionProfile(
            tools=frozenset(tools),
            writable_areas=frozenset(writable),
            network_allowed=False,
            can_execute_commands=stage in command_stages,
            can_approve=approval,
        )

    @staticmethod
    def _role_judgment(role: str, stage: StageKind) -> tuple[str, ...]:
        if role == "validation-specialist":
            return (
                "independent evidence judgment",
                "reject unsupported completion claims",
                "weigh residual risk without changing the reviewed candidate",
            )
        if "reviewer" in role:
            return (
                "independent critical review",
                "separate findings from remediation",
                "reject unsupported completion claims",
            )
        if role == "verification-specialist":
            return (
                "execute reproducible checks on a frozen candidate",
                "distinguish observed results from unverified claims",
            )
        if role == "implementation-specialist":
            return (
                "implement only approved requirements and design",
                "report limitations and failed checks without self-approval",
            )
        if role == "mission-manager":
            return (
                "preserve current user intent and route results",
                "coordinate specialists without self-approval",
            )
        return (
            f"apply {role} judgment at the {stage.value} stage",
            "state assumptions, evidence, and unresolved questions",
        )

    @staticmethod
    def _responsibility_area(role: str, stage: StageKind) -> ResponsibilityArea | None:
        if role == "mission-manager":
            return None
        if stage in {StageKind.SCOPE_RISK, StageKind.GOAL_DISCOVERY, StageKind.REQUIREMENTS}:
            return ResponsibilityArea.REQUIREMENTS_OUTCOMES
        if stage in {
            StageKind.DESIGN,
            StageKind.IMPLEMENTATION,
            StageKind.RELEASE,
        }:
            return ResponsibilityArea.ENGINEERING_DELIVERY
        return ResponsibilityArea.VERIFICATION_QA

    @classmethod
    def _expert_profile(
        cls, role: str, stage: StageKind, goal: GoalDefinition
    ) -> ExpertProfile:
        domain_depth = [
            "computer science and software engineering foundations",
            *cls._stage_domain_depth[stage],
        ]
        if goal.risk_level >= 2:
            domain_depth.append("secure software engineering")
        if goal.research_artifact:
            domain_depth.append("research methodology and reproducibility")
        if goal.question_type:
            domain_depth.append(f"{goal.question_type} problem framing")
        domain = tuple(dict.fromkeys(domain_depth))
        shared_ids = [
            "concept:structured-writing",
            "concept:evidence-reasoning",
            "concept:software-engineering",
            "concept:structured-handoff",
        ]
        if goal.risk_level >= 2:
            shared_ids.append("concept:secure-engineering")
        if goal.research_artifact:
            shared_ids.append("concept:research-reproducibility")
        return ExpertProfile(
            expert_id=f"expert:{stage.value}:{role}",
            role=role,
            stage=stage,
            general_practice=cls._general_practice,
            domain_depth=domain,
            role_judgment=cls._role_judgment(role, stage),
            shared_foundation=tuple(shared_ids),
            responsibility_area=cls._responsibility_area(role, stage),
        )

    @staticmethod
    def _perspectives(goal: GoalDefinition) -> Mapping[str, PerspectiveProfile]:
        definitions = {
            "user-purpose": (
                ResponsibilityArea.REQUIREMENTS_OUTCOMES,
                DeliveryDepth.P3,
                "preserve the user's intended outcome and scope",
                ("goal-definition",),
                ("goal completeness review",),
            ),
            "computer-science": (
                ResponsibilityArea.ENGINEERING_DELIVERY,
                DeliveryDepth.P3,
                "apply general computer science and software engineering",
                ("design-baseline", "frozen-candidate"),
                ("design and implementation review",),
            ),
            "functional-correctness": (
                ResponsibilityArea.VERIFICATION_QA,
                DeliveryDepth.P3,
                "establish required behavior independently of implementation claims",
                ("acceptance-oracle", "verification-evidence"),
                ("independent acceptance execution",),
            ),
            "quality-assurance": (
                ResponsibilityArea.VERIFICATION_QA,
                DeliveryDepth.P3,
                "judge noncompensating quality floors and remaining uncertainty",
                ("gate-decision",),
                ("quality profile review",),
            ),
            "baseline-security": (
                ResponsibilityArea.VERIFICATION_QA,
                DeliveryDepth.P3 if goal.risk_level >= 3 else DeliveryDepth.P1,
                "cover permissions, secrets, hostile inputs, and bypasses",
                ("security-assessment",),
                ("threat and misuse review",),
            ),
            "data-integrity": (
                ResponsibilityArea.VERIFICATION_QA,
                DeliveryDepth.P1,
                "preserve data meaning, provenance, and privacy obligations",
                ("data-integrity-assessment",),
                ("lineage and data-boundary review",),
            ),
            "usability-accessibility": (
                ResponsibilityArea.REQUIREMENTS_OUTCOMES,
                DeliveryDepth.P1,
                "represent user interaction and accessibility needs",
                ("usability-criteria",),
                ("scenario review",),
            ),
            "performance-resources": (
                ResponsibilityArea.ENGINEERING_DELIVERY,
                DeliveryDepth.P1,
                "bound performance and resource use",
                ("resource-assessment",),
                ("resource measurement",),
            ),
            "operations-recovery": (
                ResponsibilityArea.ENGINEERING_DELIVERY,
                DeliveryDepth.P1,
                "define monitoring, interruption, retry, and recovery behavior",
                ("recovery-plan",),
                ("fault injection",),
            ),
            "maintainability-supply-chain": (
                ResponsibilityArea.ENGINEERING_DELIVERY,
                DeliveryDepth.P1,
                "control maintenance cost, dependencies, and supply-chain identity",
                ("dependency-record",),
                ("dependency and maintainability review",),
            ),
            "documentation": (
                ResponsibilityArea.REQUIREMENTS_OUTCOMES,
                DeliveryDepth.P1,
                "provide user, technical, and operating documentation",
                ("documentation-set",),
                ("reader task review",),
            ),
            "domain-knowledge": (
                ResponsibilityArea.REQUIREMENTS_OUTCOMES,
                DeliveryDepth.P2 if goal.risk_level >= 2 else DeliveryDepth.P1,
                "apply task-specific domain obligations",
                ("domain-assessment",),
                ("domain review",),
            ),
            "research-methods-metrics": (
                ResponsibilityArea.VERIFICATION_QA,
                DeliveryDepth.P3 if goal.research_artifact else DeliveryDepth.P0,
                "preserve method, metric, experiment, and reproducibility validity",
                ("research-assurance",),
                ("method and metric review",),
            ),
            "external-effects": (
                ResponsibilityArea.ENGINEERING_DELIVERY,
                DeliveryDepth.P1,
                "enumerate, observe, reconcile, and compensate external effects",
                ("external-effect-plan",),
                ("effect-boundary fault injection",),
            ),
        }
        perspectives: dict[str, PerspectiveProfile] = {}
        for perspective_id, definition in definitions.items():
            area, depth, rationale, outputs, methods = definition
            independent = perspective_id in {"functional-correctness", "quality-assurance"}
            if perspective_id == "baseline-security" and goal.risk_level >= 2:
                independent = True
            bounded = perspective_id == "baseline-security" and goal.risk_level >= 3
            if perspective_id == "research-methods-metrics" and goal.research_artifact:
                independent = True
                bounded = True
            perspectives[perspective_id] = PerspectiveProfile(
                perspective_id=perspective_id,
                responsibility_area=area,
                delivery_depth=depth,
                independent_assessment_required=independent,
                bounded_investigation_required=bounded,
                rationale=rationale,
                required_outputs=outputs,
                verification_methods=methods,
            )
        return perspectives

    @classmethod
    def _with_experts(cls, stage: StagePlan, goal: GoalDefinition) -> StagePlan:
        return replace(
            stage,
            expert_profiles={
                role: cls._expert_profile(role, stage.kind, goal)
                for role in sorted(stage.roles)
            },
        )

    @classmethod
    def _stage(
        cls,
        kind: StageKind,
        roles: set[str],
        failure_return: StageKind | None,
    ) -> StagePlan:
        required_inputs, required_outputs = cls._stage_artifacts[kind]
        criteria = ["all-required-roles-pass"]
        if kind is StageKind.IMPLEMENTATION:
            criteria.append("frozen-candidate-bound")
        elif kind is StageKind.VALIDATION:
            criteria.append("candidate-approved-with-fresh-evidence")
        elif kind is StageKind.RELEASE:
            criteria.append("release-decision-and-package-bound")
        return StagePlan(
            kind=kind,
            role_permissions={role: cls._permission(kind) for role in sorted(roles)},
            required_inputs=required_inputs,
            required_outputs=required_outputs,
            gate_criteria=tuple(criteria),
            failure_return=failure_return,
        )

    def plan(self, goal: GoalDefinition) -> WorkflowPlan:
        reasons: list[str] = []
        for name in self._critical_fields:
            status = goal.field_status.get(name)
            value = getattr(goal, name)
            if status is KnowledgeStatus.CONFLICT:
                reasons.append(f"conflicting {name}")
            elif status is KnowledgeStatus.UNVERIFIED or value is None or value == ():
                reasons.append(f"unresolved {name}")

        exploration = bool(reasons)
        stages = [
            self._stage(
                StageKind.SCOPE_RISK,
                {"mission-manager", "risk-analyst"},
                None,
            )
        ]
        if exploration:
            stages.extend(
                [
                    self._stage(
                        StageKind.GOAL_DISCOVERY,
                        {"goal-analyst", "domain-researcher", "data-analyst"},
                        StageKind.SCOPE_RISK,
                    ),
                    self._stage(
                        StageKind.METHOD_DISCOVERY,
                        {
                            "domain-researcher",
                            "methodologist",
                            "metric-specialist",
                            "bias-reviewer",
                        },
                        StageKind.GOAL_DISCOVERY,
                    ),
                ]
            )
        design_roles = {"architecture-specialist"}
        validation_roles = {"validation-specialist"}
        if goal.risk_level >= 2:
            design_roles.update({"security-architect", "domain-specialist"})
            validation_roles.update(
                {"independent-spec-reviewer", "independent-code-reviewer"}
            )
        if goal.risk_level >= 3:
            design_roles.add("formal-methods-specialist")
        if goal.research_artifact:
            validation_roles.add("research-reproducibility-reviewer")

        stages.extend(
            [
                self._stage(
                    StageKind.REQUIREMENTS,
                    {"requirements-specialist"},
                    StageKind.METHOD_DISCOVERY if exploration else StageKind.SCOPE_RISK,
                ),
                self._stage(
                    StageKind.ORACLE,
                    {"oracle-specialist"},
                    StageKind.REQUIREMENTS,
                ),
                self._stage(StageKind.DESIGN, design_roles, StageKind.REQUIREMENTS),
                self._stage(
                    StageKind.IMPLEMENTATION,
                    {"implementation-specialist"},
                    StageKind.DESIGN,
                ),
                self._stage(
                    StageKind.INTEGRATION_VERIFICATION,
                    {"verification-specialist"},
                    StageKind.IMPLEMENTATION,
                ),
                self._stage(
                    StageKind.VALIDATION,
                    validation_roles,
                    StageKind.INTEGRATION_VERIFICATION,
                ),
                self._stage(
                    StageKind.RELEASE,
                    {"release-specialist"},
                    StageKind.VALIDATION,
                ),
            ]
        )
        return WorkflowPlan(
            track=Track.EXPLORATION if exploration else Track.PRODUCTION,
            stages=tuple(self._with_experts(stage, goal) for stage in stages),
            reasons=tuple(reasons),
            required_assurance_claims=(
                frozenset(AssuranceClaim) if goal.research_artifact else frozenset()
            ),
            noncompensating_assurance=goal.research_artifact,
            responsibility_areas=frozenset(ResponsibilityArea),
            perspectives=self._perspectives(goal),
            knowledge_base=self._knowledge_base,
        )
