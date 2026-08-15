from __future__ import annotations

_RESULT_PAYLOAD_SCHEMA = {
    "type": "object",
    "properties": {
        "gate": {"enum": ["pass", "fail", "inconclusive"]},
        "claims": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["claim_id", "claim", "artifact_sha256s", "observation_ids"],
            },
        },
        "expected_results": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "expected_result_id",
                    "description",
                    "owner_role",
                    "decision_rule_ids",
                ],
            },
        },
        "decision_rules": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["decision_rule_id", "description", "owner_role"],
            },
        },
        "observations": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "observation_id",
                    "expected_result_id",
                    "artifact_sha256",
                    "observed_value",
                    "outcome",
                ],
            },
        },
        "decision": {
            "type": "object",
            "required": ["outcome", "applied_rule_ids", "rationale"],
        },
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "unresolved": {"type": "array", "items": {"type": "string"}},
        "artifacts": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["artifact_type", "path", "sha256", "media_type"],
            },
        },
    },
    "required": [
        "gate",
        "claims",
        "expected_results",
        "decision_rules",
        "observations",
        "decision",
        "assumptions",
        "unresolved",
        "artifacts",
    ],
    "additionalProperties": True,
}

_GOAL_PROPERTIES = {
    "goal": {"type": "string", "minLength": 1, "description": "사용자가 달성하려는 목표"},
    "decision_action": {"type": ["string", "null"]},
    "outcome": {"type": ["string", "null"]},
    "population": {"type": ["string", "null"]},
    "analysis_unit": {"type": ["string", "null"]},
    "time_horizon": {"type": ["string", "null"]},
    "constraints": {"type": "array", "items": {"type": "string"}},
    "question_type": {"type": ["string", "null"]},
    "data_description": {"type": ["string", "null"]},
    "decision_threshold": {"type": ["string", "null"]},
    "risk_level": {"type": "integer", "minimum": 0, "maximum": 3},
    "research_artifact": {"type": "boolean"},
}

WORKFLOW_START = {
    "name": "workflow_start",
    "description": (
        "증거 중심 다중 에이전트 개발 미션을 시작한다. 목표 충분성을 점검하고 "
        "탐색·제작 경로, 단계, 전문 역할, 첫 작업 목록을 반환한다."
    ),
    "parameters": {
        "type": "object",
        "properties": _GOAL_PROPERTIES,
        "required": ["goal"],
        "additionalProperties": False,
    },
}

WORKFLOW_STATUS = {
    "name": "workflow_status",
    "description": "미션의 현재 revision, 단계, 필요한 전문 역할과 미완료 작업을 조회한다.",
    "parameters": {
        "type": "object",
        "properties": {"mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"}},
        "required": ["mission_id"],
        "additionalProperties": False,
    },
}

WORKFLOW_SUBMIT_RESULT = {
    "name": "workflow_submit_result",
    "description": (
        "전문 에이전트의 결과를 현재 미션에 제출한다. 다른 미션·오래된 revision·잘못된 "
        "권한 증표와 맞지 않는 결과를 거부하며, 모든 필수 역할이 통과한 경우에만 "
        "다음 단계로 전진한다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "candidate_id": {"type": ["string", "null"]},
            "payload": _RESULT_PAYLOAD_SCHEMA,
        },
        "required": ["mission_id", "revision", "task_id", "authority_token", "payload"],
        "additionalProperties": False,
    },
}

WORKFLOW_RECORD_CHECKPOINT = {
    "name": "workflow_record_checkpoint",
    "description": "현재 작업 시도의 재개 가능한 체크포인트 파일과 SHA-256을 기록한다.",
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "artifact_path": {"type": "string", "minLength": 1},
        },
        "required": [
            "mission_id",
            "revision",
            "task_id",
            "authority_token",
            "artifact_path",
        ],
        "additionalProperties": False,
    },
}

WORKFLOW_INTERRUPT_ATTEMPT = {
    "name": "workflow_interrupt_attempt",
    "description": "현재 작업 시도를 중단 상태로 기록하고 자동 재실행을 막는다.",
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "reason": {"type": "string", "minLength": 1},
        },
        "required": ["mission_id", "revision", "task_id", "authority_token", "reason"],
        "additionalProperties": False,
    },
}

WORKFLOW_RETRY_ATTEMPT = {
    "name": "workflow_retry_attempt",
    "description": "중단된 작업을 새 시도 ID로 다시 시작하고 이전 시도와의 관계를 기록한다.",
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "retry_class": {
                "type": "string",
                "enum": ["safe-retry", "reconcile-first", "operator-approved"],
            },
        },
        "required": [
            "mission_id",
            "revision",
            "task_id",
            "authority_token",
            "retry_class",
        ],
        "additionalProperties": False,
    },
}

WORKFLOW_REVISE = {
    "name": "workflow_revise",
    "description": (
        "사용자의 최신 지시를 미션에 적용하고 revision을 올린다. 기존 미완료 작업은 "
        "오래된 상태로 표시하고 목표 점검부터 새 계획을 만든다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "instruction": {"type": "string", "minLength": 1},
            **_GOAL_PROPERTIES,
        },
        "required": ["mission_id", "instruction"],
        "additionalProperties": False,
    },
}

WORKFLOW_FREEZE_CANDIDATE = {
    "name": "workflow_freeze_candidate",
    "description": (
        "구현 단계의 입력 파일과 도구 체인을 불변 후보본으로 동결한다. 후보본 ID와 "
        "필수 증거 목록을 반환하며, 구현 단계는 후보본 없이 통과할 수 없다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "inputs": {
                "type": "object",
                "minProperties": 1,
                "additionalProperties": {"type": "string", "minLength": 1},
            },
            "toolchain": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "parent_candidate_id": {"type": ["string", "null"]},
        },
        "required": [
            "mission_id",
            "revision",
            "task_id",
            "authority_token",
            "inputs",
            "toolchain",
        ],
        "additionalProperties": False,
    },
}

WORKFLOW_RECORD_EVIDENCE = {
    "name": "workflow_record_evidence",
    "description": (
        "후보본에 결속된 시험·검토 증거를 추가 전용 기록에 남긴다. "
        "실제 증거 파일의 SHA-256을 계산하고 기록 해시 사슬을 확인한다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "candidate_id": {"type": "string", "minLength": 1},
            "evidence_type": {"type": "string", "minLength": 1},
            "outcome": {"type": "string", "enum": ["pass", "fail"]},
            "artifact_path": {"type": "string", "minLength": 1},
            "expected_results": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "object"},
            },
            "decision_rules": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "object"},
            },
            "observations": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "object"},
            },
            "details": {"type": "object"},
        },
        "required": [
            "mission_id",
            "revision",
            "task_id",
            "authority_token",
            "candidate_id",
            "evidence_type",
            "outcome",
            "artifact_path",
            "expected_results",
            "decision_rules",
            "observations",
        ],
        "additionalProperties": False,
    },
}

WORKFLOW_APPROVE_CANDIDATE = {
    "name": "workflow_approve_candidate",
    "description": (
        "검증 단계의 후보본을 독립 검토자가 승인한다. 필수 증거, 증거 기록 해시 사슬, "
        "후보본 무결성과 자가 승인 금지를 모두 확인한다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "candidate_id": {"type": "string", "minLength": 1},
        },
        "required": [
            "mission_id",
            "revision",
            "task_id",
            "authority_token",
            "candidate_id",
        ],
        "additionalProperties": False,
    },
}

WORKFLOW_PACKAGE_RELEASE = {
    "name": "workflow_package_release",
    "description": (
        "승인된 후보본의 무결성을 다시 검사하고 결정론적 ZIP 출시 묶음을 만든다. "
        "후보본 ID와 출시 파일 SHA-256을 미션에 결속한다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mission_id": {"type": "string", "pattern": "^mis-[0-9a-f]{32}$"},
            "revision": {"type": "integer", "minimum": 1},
            "task_id": {"type": "string", "minLength": 1},
            "authority_token": {"type": "string", "minLength": 1},
            "candidate_id": {"type": "string", "minLength": 1},
            "disposition": {
                "type": "string",
                "enum": ["release", "limited-release", "hold", "prohibited"],
            },
            "reasons": {"type": "array", "items": {"type": "string"}},
            "scope": {"type": "string", "minLength": 1},
            "expires_at": {"type": "string", "minLength": 1},
            "rollback_plan": {"type": "string", "minLength": 1},
            "out_of_scope_controls": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "minLength": 1},
            },
        },
        "required": [
            "mission_id",
            "revision",
            "task_id",
            "authority_token",
            "candidate_id",
            "disposition",
        ],
        "allOf": [
            {
                "if": {
                    "properties": {"disposition": {"const": "limited-release"}},
                    "required": ["disposition"],
                },
                "then": {
                    "required": [
                        "scope",
                        "expires_at",
                        "rollback_plan",
                        "out_of_scope_controls",
                    ]
                },
            }
        ],
        "additionalProperties": False,
    },
}

TOOL_SCHEMAS = (
    WORKFLOW_START,
    WORKFLOW_STATUS,
    WORKFLOW_SUBMIT_RESULT,
    WORKFLOW_RECORD_CHECKPOINT,
    WORKFLOW_INTERRUPT_ATTEMPT,
    WORKFLOW_RETRY_ATTEMPT,
    WORKFLOW_REVISE,
    WORKFLOW_FREEZE_CANDIDATE,
    WORKFLOW_RECORD_EVIDENCE,
    WORKFLOW_APPROVE_CANDIDATE,
    WORKFLOW_PACKAGE_RELEASE,
)
