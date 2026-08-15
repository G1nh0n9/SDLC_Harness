# Reference and Next Reading

> **This chapter explains:** where to find normative rules, exhaustive records, causal traces, implementation paths, and operating guidance after the main architecture narrative.

## 1. Architecture deep dives

Use the detailed pages as references, not as another mandatory reading sequence:

- [Purpose and assurance scope](purpose-and-scope.md) defines protected items, observable failures, mission types, and non-goals.
- [Operating model](operating-model.md) defines quality planning, participation profiles, expert assignment, handoff content, and decision rights.
- [Complete `export-ownership` trace](worked-mission.md) preserves `event-0001` through `event-0035`, `C1` and `C2`, authority consumption, `STALE` propagation, and the audited causal chain.
- [Runtime reference](runtime.md) defines the full state families, transition procedure, attempt records, candidate identity, and invalidation rules.
- [Reliability reference](reliability.md) defines checkpoint, duplicate-delivery, reconciliation, compensation, and failure-class details.
- [Trust-boundary reference](trust.md) enumerates protected assets, input trust levels, environment controls, and residual uncertainty.
- [Prior Work review](prior-work.md) contains source-by-source attribution, retained rules, design references, adaptations, and deliberate exclusions.
- [Content coverage map](content-coverage.md) maps requested topics to the explanatory and authoritative sources.

## 2. Normative and implementation material

The accepted [requirements](../requirements.md) and [architecture decision records](../adr/README.md) define the target. [Expert Organization Design](../expert-organization-design.md) specifies expert formation and handoff rules, and [Agent Harness Governance](../agent-harness-governance.md) records the broader governance proposal.

Schemas under `src/agent_harness/schemas/` define record shape. Code under `src/agent_harness/` implements a particular revision of the target; tests under `tests/` evaluate only the scenarios they exercise. A schema-valid payload remains untrusted until policy resolves stored authority and state, checks cross-record identity, inspects actual files and hashes, and evaluates the semantic decision rules. Existing code or tests cannot weaken an accepted requirement merely by omitting it.

## 3. Conclusion and next steps

The architecture turns one `export-ownership` request into a reviewable release decision without treating a model's completion claim as authority. The Policy and State Engine mediates transitions; one-use authority grants limit work; the Task Runner records execution; the Candidate Manager freezes exact material; the Handoff Verifier checks transfer and receiver acceptance; independent QA decides each must-pass acceptance criterion; and release remains tied to one candidate and complete evidence set.

The same mechanisms recover from ordinary failures. Interruption creates a new attempt from a verified checkpoint. Duplicate delivery does not repeat an accepted event. A failed criterion leaves `C1` unchanged and moves correction to child candidate `C2`. Changed inputs make dependent evidence `STALE`. An external operation with an unknown outcome requires reconciliation before replay; a confirmed side effect may require compensation. Verifier disagreement produces insufficient evidence or escalation, not an automatic pass.

These controls do not prove total correctness, create operating-system isolation, or guarantee exactly-once behavior in another system. They make the supported scope and remaining uncertainty explicit.

**Default next step:** follow the [User Guide](../user-guide.md) to create and operate a mission through the Hermes-facing workflow.

Choose a secondary path only when your responsibility requires it:

- **Mission designer:** [Operating Model](operating-model.md), then [Expert Organization Design](../expert-organization-design.md).
- **Implementer:** [Runtime reference](runtime.md), the schemas, and the [architecture decision records](../adr/README.md).
- **QA or operator:** [Complete `export-ownership` trace](worked-mission.md), then [Reliability reference](reliability.md).
- **Security reviewer:** [Trust-boundary reference](trust.md), then the testable [Requirements](../requirements.md).
- **Research or attribution reviewer:** [Prior Work review](prior-work.md) and its cited primary sources.
