# Reference and Next Reading

> **Use this reference to find:** the architecture's defined terms, records, states, schemas, code paths, detailed decisions, and role-specific deep dives.

This page is a navigation reference and does not repeat the operating model.

## 1. Core terms

| Term | Meaning |
|---|---|
| **Mission** | A user-directed body of work with a stable identity. |
| **Revision** | One version of the mission intent and accepted inputs. |
| **Stage** | A planned part of the mission with required inputs, outputs, roles, and evidence. |
| **Task** | A bounded unit of work assigned to one area of responsibility under one authority grant. |
| **Attempt** | One execution of a task under a retry budget. |
| **Perspective** | A quality, domain, operational, or risk viewpoint that must be considered. |
| **Participation profile** | A P0–P3 base level of involvement with separate P4 independent-assessment and P5 bounded-investigation requirements for one perspective. It is not a rank or seniority scale. |
| **Assigned expert** | A worker or reviewer assigned to one or more compatible perspectives. The assignment states the required knowledge, workflow phases, and areas of responsibility. |
| **Baseline** | Accepted mission inputs and decision criteria for one revision. |
| **Authority grant** | One-time permission bound to an identity, task, workspace, tools, candidate, expiry, and operations. |
| **Candidate** | A work product and every decision-relevant input frozen under one identity for verification and a quality decision. In this architecture, a candidate is software material, not a person. |
| **Artifact** | A file or other persistent output with verified identity and provenance. |
| **Evidence** | A checked observation tied to execution, artifacts, external state, or review. |
| **Finding** | A reproducible quality observation with impact, uncertainty, and supporting evidence. |
| **Handoff** | Structured transfer that passes automatic checks and receiver acceptance. |
| **Checkpoint** | Verified durable progress from which a logical task can resume. |
| **External operation** | A logical request to write to or otherwise change an external system. Its identity remains stable across attempts so policy can reconcile an unknown outcome and prevent duplicate external side effects. |
| **External side effect** | A change to an external system caused by mission work, tracked under a stable logical operation ID and reconciled before retry when its outcome is unknown. |
| **Must-pass acceptance criterion** | A required quality criterion that must pass independently. |
| **Quality decision** | A judgment tied to one candidate that covers observations, uncertainty, residual risk, and release scope. |
| **Completion invalidation** | A new event withdrawing a prior completion decision without erasing history. |

## 2. Record families

| Family | Required identity | Typical content |
|---|---|---|
| Mission and state | Mission, revision, stage, task, or transition | Steering decisions, attempts, transitions, retries, checkpoints, recoveries, and invalidations |
| Plan and quality | Mission revision and baseline | Perspectives, participation profiles, thresholds, methods, disputes, and decisions |
| Candidate | Mission revision and candidate | Input manifest, hashes, parent-child lineage, and mutation status |
| Execution | Authority, task, attempt, and candidate when applicable | Executable identity, arguments, time, exit status, outputs, and operation IDs |
| Handoff | Producer and receiver tasks and candidate | Required inputs and outputs, paths, hashes, automatic checks, and receiver-acceptance decisions |
| Finding | Reviewer authority, candidate, and quality item | Location, reproduction, observed and expected behavior, impact, and uncertainty |
| Release | Candidate and complete evidence set | Release scope, residual risk, and package identity |

## 3. State reference

The target architecture uses separate state machines for:

- mission and revision;
- plan and baseline;
- stage and task;
- task attempt;
- candidate;
- evidence validity;
- quality and release decision;
- external operation and compensation.

Only the Policy and State Engine changes authoritative state. The JSON Schemas, state-machine tests, and accepted architecture decisions contain the detailed transition requirements; the overview does not.

## 4. Schema locations

Current schemas are under `src/agent_harness/schemas/`:

- `artifact-manifest.schema.json`
- `gate-result.schema.json`
- `handoff.schema.json`
- `review-finding.schema.json`
- `work-order.schema.json`

The target model requires additional schemas or equivalent validated records for authority grants, attempts, checkpoints, quality profiles, quality decisions, invalidations, and external side effects.

### 4.1 Target record shapes

The following table defines architectural field requirements. It does not claim that every named schema exists in the current package.

| Record | Required identity and control fields | Required content |
|---|---|---|
| Mission revision | `mission_id`, `revision`, parent revision, state, and accepted-at event | identity of the latest user instruction, decision that the request is specific enough to plan and verify, assumptions, and impact of changed inputs |
| Quality profile | mission revision, profile identity, and contributor authorities | must-pass acceptance criteria, improvement targets, metric or method, expected evidence, supported scope, and decision rule |
| Perspective plan | mission revision and perspective identity | applicability and reason, `delivery_depth: P0|P1|P2|P3`, `independent_assessment_required`, `bounded_investigation_required`, area of responsibility, expert group, workflow phase, required output, and completion rule |
| Stage plan | mission revision, stage identity, and dependency identities | required inputs, outputs, authorities, evidence, completion rule, failure return, and retry policy |
| Authority grant | grant, mission, revision, stage, task, attempt, worker, workspace, and candidate when applicable | allowed operations, tools and executable identities, read and write roots, expiry, remaining uses, and consumption state |
| Task attempt | task, attempt, authority, worker, and workspace | start and end times, status, executable identity, arguments, environment identity, outputs, checkpoint, and failure class |
| Checkpoint | logical task, attempt, and checkpoint sequence | completed operation boundary, artifact paths and recalculated hashes, durable-write confirmation, and resume position |
| Candidate manifest | candidate, mission revision, and parent candidate | canonically ordered inputs, normalized paths, sizes, media types, SHA-256 values, dependency and toolchain identities, and mutation state |
| Verification evidence | evidence, authority issue and consumption events, mission, revision, stage, task, attempt, candidate, issued worker, and issued role | runner identity, executable digest, arguments, bounded environment digest, input digests, start and finish times, timeout and exit status, raw output references, actual artifact SHA-256, observation, expected value or decision rule, quality item, and validity dependencies |
| Handoff | handoff, producer and receiver tasks, and candidate | shared foundation, required inputs and outputs, artifact paths and hashes, automatic decision, receiver acceptance, and limitations |
| Finding | finding, reviewer authority, candidate, and quality item | location, reproduction, expected and observed behavior, impact, uncertainty, supporting evidence, and disposition |
| Quality decision | decision, QA authority, revision, and candidate | observations for each criterion; classification as a must-pass acceptance criterion or improvement target; pass, fail, or insufficient-evidence result; uncertainty; residual risk; and supported release scope |
| Semantic comparison | comparison, reviewer authority, revision, candidate set, and quality item | model and provider, prompt or rubric digest, presentation order, per-item judgment, confidence, reversed-order result, disagreement, and final `INCONCLUSIVE` or escalation disposition |
| External operation | logical operation, attempt events, and external resource identity | start, receipt, success, failure, or unknown status; reconciliation; retry permission; compensation; and residual effect |
| Invalidation | invalidation event, affected revision or candidate, and earlier decision | new observation, changed dependency, stale evidence set, earliest reopened stage, and resulting release state |
| Release and package | release decision, candidate, and complete evidence-set identity | release, limited release, hold, or do not release; scope and exclusions; residual risk; package manifest and SHA-256; and rollback or cleanup information |

Policy accepts verification evidence as one atomic record. The stored authority grant and runner boundary determine the producer identity and role; policy never copies them from a caller-supplied role field. If authority issue or consumption, runner identity, command, environment, exit status, required raw output, or an actual file digest is absent or inconsistent, policy rejects the entire evidence event. Large outputs may be stored as content-addressed artifacts, but their hashes and references remain inside the atomic record.

Evidence validity is separate from evidence existence. An accepted record may later become `STALE` when a declared dependency changes or `INVALID` when its authenticity or artifact binding is disproved. Neither state deletes the record.

### 4.2 Validation boundary

JSON Schema defines shape, types, required fields, and allowed enumerations. It does not establish authority, file existence, path confinement, SHA-256 correctness, candidate immutability, or semantic sufficiency. Those checks require current stored state and actual files.

Policy therefore uses this processing order:

```text
parse without side effects
  → validate schema and reject unknown or malformed fields where required
  → resolve the stored authority and current state
  → validate cross-record identity and allowed operation
  → inspect paths, files, manifest, and SHA-256
  → perform the semantic checks and other checks required for the workflow phase
  → append the policy decision
```

A schema-valid payload remains untrusted until the later checks pass. Conversely, policy does not accept an otherwise plausible object by skipping schema validation.

## 5. Code index

| Concern | Current code |
|---|---|
| Mission planning and stages | `src/agent_harness/methodology.py`, `mission.py` |
| State and transition rules | `state_machine.py`, `policy.py`, `mission.py` |
| Workspaces and execution | `workspace.py`, `agent_runner.py` |
| Candidates and lineage | `candidate.py` |
| Handoff | `handoff.py` and `schemas/handoff.schema.json` |
| Evidence | `evidence.py` |
| Release | `release.py` |
| Hermes surface | `hermes_plugin.py`, `plugin_service.py`, `plugin_schemas.py` |
| Command-line interface | `cli.py` |

This index shows where code exists; it does not indicate whether a target rule is complete.

## 6. Test index

Tests are under `tests/`. The key target test groups cover:

- planning and perspective formation;
- authority spoofing and expiry;
- policy-only transitions;
- workspace and executable restrictions;
- candidate mutation, lineage, and symbolic links;
- stage input/output and artifact hash checks;
- automatic handoff checks and receiver acceptance;
- false completion and self-approval;
- interruption, checkpoint resume, duplicate delivery, and compensation;
- verifier disagreement and uncertainty;
- release binding.

## 7. Detailed architecture documents

| Question | Document |
|---|---|
| Why does the harness exist? | [`../architecture.md`](../architecture.md) |
| Where is the main architecture reading path? | [`full-architecture.md`](full-architecture.md) or [`../agent-harness-architecture.html`](../agent-harness-architecture.html) |
| Where is requested content mapped to explanatory sections? | [`content-coverage.md`](content-coverage.md) |
| What problem and assurance scope define the system? | [`purpose-and-scope.md`](purpose-and-scope.md) |
| Who decides, and how does the harness assign experts? | [`operating-model.md`](operating-model.md) |
| How does one concrete mission establish causal closure from request through package? | [`worked-mission.md`](worked-mission.md) |
| What are the complete state models and transition checks? | [`runtime.md`](runtime.md) |
| What proves completion and how does recovery work? | [`reliability.md`](reliability.md) |
| What is trusted and what needs external controls? | [`trust.md`](trust.md) |
| What prior work informs the architecture, and what does the harness add? | [`prior-work.md`](prior-work.md) |

## 8. Normative and decision material

- Testable requirements and forbidden behavior: [`../requirements.md`](../requirements.md)
- Architecture decisions: [`../adr/README.md`](../adr/README.md)
- Expert and handoff design: [`../expert-organization-design.md`](../expert-organization-design.md)
- Reliability research: [`../agent-reliability-survey.md`](../agent-reliability-survey.md)
- Governance proposal: [`../agent-harness-governance.md`](../agent-harness-governance.md)

The accepted mission requirement baseline and approved architecture decisions define the target. Versioned schemas and tests describe or evaluate a particular implementation against that target. They cannot weaken a requirement merely because the current code or a test omits it. Explanatory text must be corrected when it conflicts with the accepted baseline or decision record. An incomplete implementation artifact cannot redefine the target.

## 9. Next reading

The default next document is the [User Guide](../user-guide.md), which explains how a user starts and follows a mission. Readers who need to evaluate or implement the target architecture should use the path for their responsibility:

| Reader | Deep dive |
|---|---|
| Mission designer | [Operating Model](operating-model.md), then [Expert Organization Design](../expert-organization-design.md) |
| Implementer | [Runtime Architecture](runtime.md), schemas under `src/agent_harness/schemas/`, and the [architecture decision records](../adr/README.md) |
| QA or operator | [Complete `export-ownership` trace](worked-mission.md), then [Reliability and Recovery](reliability.md) |
| Security reviewer | [Trust Boundaries](trust.md), then the testable [Requirements](../requirements.md) |
| Research or attribution reviewer | [Prior Work](prior-work.md) and its cited primary sources |

The detailed pages are lookup and audit material. They do not form another mandatory linear reading path.
