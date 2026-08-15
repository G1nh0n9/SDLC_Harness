# Worked Mission: `export-ownership`

> **This chapter explains:** which records, identities, checks, and decisions take one software development mission from a user request to a release decision.

> **Reading note:** This is an illustrative execution of the target architecture, not a claim that the current Python package has completed this mission. Symbolic SHA-256 expressions show what bytes are bound; they are not fabricated run results.

## 1. Initial request and readiness gap

The user asks:

> Add an authenticated data-export feature that returns only records owned by the requesting account.

That sentence establishes intent but leaves open several decisions that could change the implementation or its acceptance criteria. Requirements and Outcomes must resolve or explicitly record them before Engineering receives write authority:

- What qualifies as the requesting account: the authenticated principal, an organization selected in the session, or an account ID supplied in the request?
- Which record types are included, and which linked records must be excluded?
- Is the export synchronous, or does it create an external object for later download?
- What output formats and schema versions are supported?
- What response should a user receive for an unauthorized, malformed, canceled, or duplicate request?
- How long may generated material exist, and who may retrieve it?
- Which storage backends, deployment modes, and migration states are supported?

The Mission Service records the request as `mission-export-ownership`. The first accepted interpretation becomes `revision-0001`; the original message remains attached to the mission. A later change does not overwrite this revision.

## 2. Request readiness assessment

The Goal and Quality Planner determines whether the request is specific enough to support a testable baseline.

| Planning question | Decision for `revision-0001` | Consequence |
|---|---|---|
| Decision to be made | Whether the feature may be released for the supported account and storage configurations | Defines the final quality decision |
| Intended outcome | An authenticated account obtains only its own exportable records | Defines the positive scenario |
| Analysis unit | One export request and the material it produces | Establishes what the observations cover |
| Population and scope | Supported authenticated accounts, record classes, formats, and storage backends | Prevents claims beyond the supported scope |
| Forbidden behavior | Cross-account disclosure, unauthenticated export, an untracked external object, and reuse of stale approval | Defines criteria that must pass independently |
| Time horizon | Request, generation, retrieval, expiry, and cleanup | Adds operational checks and checks for external side effects |
| Decision threshold | Every must-pass acceptance criterion passes independently for the same frozen candidate, and no external side effects remain unresolved | Makes release acceptance explicit |
| Open assumptions | Identity source, storage query support, retention policy, and large-account limit | Must be resolved or tracked as blockers |

If any unresolved item could change acceptance, policy keeps the mission in goal definition. An implementation proposal cannot bypass that state, regardless of how polished it is.

The Goal and Quality Planner produces the planning-readiness decision and quality proposal. The Mission Manager checks that every required area of responsibility contributed, every applicable perspective has an accountable area or a documented rationale for nonapplicability, every stage has a gate, and every blocker has a disposition. It then requests policy acceptance rather than changing mission state to approve its own plan.

For this example, the accepted plan record is `plan-export-ownership-revision-0001`. It binds the planning-readiness table above, the quality profile below, the stage graph, expert assignments, risk items `risk-authz-bypass`, `risk-ownership-race`, and `risk-external-object`, the required evidence matrix, and the rule that the required evidence set is frozen when a candidate is created. The Mission Manager may schedule and route this material but is not authorized to implement, inspect the candidate, perform QA, approve its own work, or package a release.

## 3. Joint quality baseline

The baseline is a joint work product, not a Requirements document passed unchanged to the other areas.

### 3.1 Requirements and Outcomes contribution

The Requirements and Outcomes area defines ownership, supported records, successful and failed user-visible behavior, retention, and explicitly forbidden disclosure. It records examples of valid requests, cross-account requests, missing identity, revoked access, and records whose ownership changes while an export is running.

### 3.2 Engineering and Software Delivery contribution

The Engineering and Software Delivery area identifies the actual ownership boundary in the data model, authorization decision points, database and object-storage effects, supported deployment modes, likely race conditions, cost and performance constraints, and implementation surfaces that can bypass the intended filter. It may determine that a proposed requirement cannot be implemented safely on an existing backend, but it cannot lower the requirement itself.

### 3.3 Verification and Quality Assurance contribution

The Verification and Quality Assurance area defines fixtures whose expected ownership is independently controlled from the implementation query, negative cases for every bypass route, output-schema and completeness checks, required command records, supported-backend coverage, uncertainty treatment, and the evidence needed to judge release. Engineering may assess feasibility but cannot rewrite the independently controlled expected results or decision rules.

### 3.4 Baseline quality profile

| Quality item | Kind | Minimum observation | Decision rule |
|---|---|---|---|
| Authorization isolation | Must-pass acceptance criterion | Independent fixtures show that Account A's export contains no records owned solely by Account B, across every supported entry point | Any cross-account record is a failure |
| Authentication | Must-pass acceptance criterion | Requests with missing, expired, or mismatched principals fail before export material is created | Any unauthenticated success is a failure |
| Data integrity | Must-pass acceptance criterion | Every expected owned record appears exactly once, while excluded classes and duplicate rows do not appear | Missing, foreign, or duplicate required data is a failure |
| Required functionality | Must-pass acceptance criterion | The feature completes with the specified result for every supported account size, format, and backend | Any advertised configuration that cannot complete is a failure |
| Privacy and retention | Must-pass acceptance criterion | Retrieval and expiry follow the accepted retention rule, and sensitive fields remain within the declared scope | Undeclared retention or field disclosure is a failure |
| Recovery and cleanup | Must-pass acceptance criterion when asynchronous export is enabled | After an interruption, the operation has a queryable status and leaves no orphaned external object | Unknown or untracked residual effects block release |
| Performance margin | Improvement target unless the baseline makes it a must-pass criterion | Completion time and resource use are measured for the declared account-size bands | Considered only after all must-pass criteria pass independently |
| Usability and diagnostics | Improvement target | Authorized and denied users receive the specified status without leaking information | Cannot compensate for a failed must-pass criterion |

The accepted baseline record binds the mission revision, requirement set, quality profile, verification methods, required perspectives, stage plan, unresolved assumptions, and the identities of the contributors whose authority was checked.

## 4. Perspective inventory and expert assignment

The planner enumerates perspectives before deciding how many workers to create. For this mission, the baseline inventory includes outcome, general software engineering, authorization, data integrity, privacy, usability, performance, operations, recovery, maintainability, supply-chain identity, documentation, testability, and external side effects.

Every perspective remains in the record. If synchronous-only export makes compensation inapplicable, the planner records either a reasoned `not-applicable` decision or a lower P0–P3 base level of involvement for the perspective covering external side effects for that revision.

### 4.1 Participation profile for this mission

| Perspective | Profile | What that requires here |
|---|---|---|
| Output schema conformance | `P0` | The accepted schema and row-level checker determine conformance; Requirements remains accountable for the rule and responds when the check fails |
| Baseline usability | `P1` | The assigned Requirements expert reviews the messages and flow as routine baseline work and records the decision |
| Storage-backend behavior | `P2` | A storage expert answers a bounded question about query and consistency behavior and returns a cited recommendation |
| Authorization design | `P3` | A security expert participates throughout design, implementation decisions, and Engineering handoff but cannot approve their own work |
| Cross-account verification | `P3+P4` | A QA security expert participates throughout the verification workflow phase and uses separate authority and a read-only workspace to judge the candidate independently |
| Unknown object-storage semantics | `P2+P5`, with `+P4` when it affects a must-pass acceptance criterion | A bounded review of official documentation or an experiment begins only when status-query or duplicate-suppression behavior is unresolved; a separate assessor judges any release-critical conclusion |

Risk can change the base level of involvement, add independent assessment, or require investigation. Agent count is determined only after those decisions are made.

### 4.2 Expert team and knowledge assignments

Compatible perspectives are grouped only after the complete participation profile has been assigned.

| Assigned expert | Perspectives | General methods | Domain expertise | Role-specific decisions |
|---|---|---|---|---|
| Outcome and scenario expert | outcome, usability, privacy scope | precise technical writing, scenario analysis, uncertainty recording | account and export domain | Decides whether the baseline expresses the user's intended result |
| Export engineering expert | general engineering, data integrity, performance, maintainability | decomposition, design comparison, reproducible handoff | application, database, streaming or batch export | Chooses an implementable design within the baseline |
| Continuously participating authorization expert | authorization and misuse paths | threat reasoning, counterexample search | authentication, authorization, data-boundary design | Identifies and prevents bypass routes without granting final approval |
| Independent export verifier | schema, negative ownership cases, supported backends | design of independently controlled expected results, reproducible execution, finding records | test systems and export semantics | Determines what the candidate actually demonstrates |
| Operations expert when asynchronous effects exist | recovery, retention, cleanup, external side effects | failure analysis and state reconciliation | object storage and operations | Determines whether uncertain or residual effects block completion |

The authorization expert may work continuously with Engineering, but the independent verifier remains separate. Giving another call to the same model a different name does not by itself create independence.

## 5. Revision and stage plan

Policy accepts the following plan only after each stage has explicit inputs, outputs, evidence, and forbidden transitions.

| Stage | Required inputs | Required outputs | Evidence before advance | Failure return point | Main forbidden shortcut |
|---|---|---|---|---|---|
| Goal definition | User request and domain constraints | A record showing that the request is specific enough to plan and verify, plus open assumptions | Contributor identities and the planning-readiness decision | Remain in goal definition until gaps that could change acceptance are closed | Starting implementation before the meaning of acceptance is defined |
| Quality planning | A request specific enough to plan and verify | Accepted requirements, quality profile, perspectives, and methods | Joint contributions from all three areas of responsibility and the policy decision | Return to the missing contribution or to goal definition | One area lowering a must-pass criterion by itself |
| Design and independent expected-result preparation | Accepted baseline | Design, independent fixtures and expected results, and work breakdown | Design review and the identity of each independently controlled expected result or decision rule | Return to design or quality planning, depending on which assumption failed | The implementer editing independent expectations |
| Implementation | Accepted work order and authority | Source, self-tests, generated records, and declared limitations | Captured execution and artifact hashes | Retry from the last verified implementation checkpoint or issue a corrected task | Caller-supplied role text expanding authority |
| Candidate freeze | All candidate inputs | Manifest and immutable candidate identity | Normalized paths, regular files, SHA-256, and lineage | Remain in the assembling state; no candidate identity is issued | Editing the candidate after it is frozen |
| Independent verification | Frozen candidate and independent methods | Execution records and findings | Independent execution identity, candidate binding, and receiver acceptance | Correct an invalid method or require a child candidate for a product defect | Approving a result for a different candidate |
| Quality decision | Complete required observations | A pass, fail, or insufficient-evidence result for each criterion, plus a release, limited-release, hold, or do-not-release scope | Independent evaluation of every must-pass acceptance criterion and residual risk | Hold for missing evidence or require a child candidate for a failed criterion | Offsetting a failed must-pass acceptance criterion with strong performance against an improvement target |
| Packaging | Approved candidate and evidence set | Package identity and source-candidate binding | Rechecked manifest and package SHA-256 | Fail only the package attempt unless the source identity changed | Packaging from modified or unapproved source |

Each accepted stage definition belongs to `revision-0001`. Reusing it after an acceptance-changing user instruction requires an explicit impact decision.

## 6. Authority grants and acting identity

When implementation begins, policy issues one authority grant for one attempt. An illustrative grant contains:

```json
{
  "mission_id": "mission-export-ownership",
  "revision": "revision-0001",
  "stage_id": "implementation",
  "task_id": "task-export-query",
  "attempt_id": "attempt-0001",
  "worker_id": "worker-export-engineering-01",
  "responsibility": "engineering-delivery",
  "workspace_id": "workspace-task-export-query-attempt-0001",
  "allowed_write_roots": ["work/source", "work/self-test", "out/execution"],
  "allowed_operations": ["read-baseline", "edit-source", "run-approved-test", "submit-result"],
  "candidate_id": null,
  "expires_at": "policy-defined",
  "remaining_uses": 1
}
```

The example intentionally omits a fabricated signature or secret. In a real run, the stored grant and its validation material establish the identity. The worker's submitted `role` field is never the identity source.

The central check rejects the request when any binding differs, the grant is expired or consumed, the operation is absent, or the request targets another workspace, task, revision, or candidate. The Mission Manager cannot bypass this check to save time.

## 7. Workspace isolation and captured execution

The Workspace Broker creates separate source, build, temporary, home, and output roots for the task attempt. The runner supplies only the approved environment and resolves an approved executable identity rather than relying on an unrestricted `PATH` search or a caller-provided command prefix.

The implementation worker may write the assigned source and self-test paths. It cannot write the independently controlled expected results or decision rules, QA findings, policy state, another role's workspace, or release output.

The execution record contains at least:

- authority, task, attempt, workspace, and active revision identity;
- executable identity, arguments, bounded environment, start and finish times;
- timeout, exit status, standard output, and standard error;
- every declared output path and its independently calculated SHA-256;
- external logical operation IDs and observed receipts;
- the last verified checkpoint, when the task supports resumption.

A zero exit status is one observation; it does not decide whether the stage advances.

## 8. Candidate freeze and manifest identity

Engineering submits every input that can affect judgment: source, accepted requirements, independent test baseline, design material, dependency and toolchain identities, build configuration, and generated artifacts required by the workflow phase.

For each regular file `f`, the harness calculates:

```text
artifact_hash(f) = SHA256(exact file bytes)
```

The Candidate Manager first creates a canonical identity payload that excludes every derived identity field:

```text
manifest_identity_payload = {
    mission_id,
    revision_id,
    parent_candidate_id,
    canonical_ordered_entries,
    accepted_build_and_toolchain_identity
}
manifest_digest = SHA256(JCS(manifest_identity_payload))
candidate_id = "candidate:" || manifest_digest
manifest_record = {
    identity_payload: manifest_identity_payload,
    manifest_digest: manifest_digest,
    candidate_id: candidate_id
}
```

`JCS` is the accepted canonical JSON serialization. The identity payload stores normalized relative paths, media types, sizes, SHA-256 values, the required stage role, and provenance references. Because the payload does not contain `manifest_digest` or `candidate_id`, its digest is not self-referential.

The Candidate Manager rejects any manifest with one or more of the following conditions:

- an absolute path that escapes the approved root;
- `..` path traversal;
- a top-level or nested symbolic link that leaves the approved root;
- a missing file;
- a non-regular file where a regular file is required;
- a duplicate normalized path;
- a hash that no longer matches the manifest's identity payload.

The first review target uses the human-readable alias `candidate-0001`. Its authoritative identity is `C1=candidate:SHA256(JCS(manifest-identity-c1))`, and the alias is never accepted in place of `C1`. Once verification begins, the bytes identified by `manifest-record-c1` do not change under either reference.

## 9. Handoff checks and receiver acceptance

Engineering sends the frozen candidate and implementation record to the independent verifier.

### 9.1 Automatic checks

The Handoff Verifier checks the schema, producer authority, mission, revision, stage, task, candidate, required input and output types, normalized paths, regular-file status, SHA-256, manifest lineage, and prohibited symbolic links.

### 9.2 Receiver acceptance

The independent verifier then records whether the material is understandable and usable without recreating Engineering's work. The receiver confirms that the accepted baseline, independent fixtures, build instructions, candidate identity, limitations, unresolved assumptions, and requested QA action are present.

Neither a structurally valid but unusable handoff nor a persuasive narrative with missing files or incorrect hashes advances. Receiver acceptance permits the next workflow phase to begin; it is not a quality pass.

## 10. Independent verification and quality decision

Verification materializes or mounts the frozen candidate in a separate workspace. The verifier reproduces the declared build and required checks, runs the independent positive and negative ownership cases, inspects every supported entry point, and records findings against `C1`, using `candidate-0001` only as a readability alias.

For each must-pass acceptance criterion, the quality decision points to the exact observations that support it. For example:

- the authorization decision cites the negative-case execution and result artifact;
- the data-integrity decision cites the expected fixture identity, produced export, comparison output, and candidate;
- the operations decision cites the logical external operation, receipt or reconciliation result, and cleanup observation;
- the required-functionality decision lists the supported configurations actually exercised.

QA records `pass`, `fail`, or `insufficient-evidence` for each must-pass acceptance criterion and then recommends `release`, `limited-release`, `hold`, or `do-not-release`. Insufficient evidence requires a hold. A limited release can narrow the supported scope only to the portion for which every applicable criterion passed independently; it cannot declare a known cross-account disclosure acceptable. Policy accepts the decision only if every required observation, finding, receiver acceptance, and residual-risk record is bound to `R` and `C1`.

Packaging then rechecks the candidate identity and creates a package whose manifest points back to the same accepted candidate and evidence set. The packager cannot edit source or tests.

## 11. Child candidate and stale evidence

Suppose QA finds that a secondary download route accepts an account ID from the request and bypasses the authenticated ownership filter.

1. QA records a reproducible security finding for `C1`.
2. The security acceptance criterion fails; policy records `hold`.
3. `C1` remains unchanged.
4. Engineering receives new authority to create child candidate `C2`.
5. The child identity payload records `C1` as parent and the changed source and self-test identities.
6. Evidence whose dependency includes the changed authorization path becomes `STALE`.
7. Policy evaluates whether any unaffected evidence can remain valid; neither arrival time nor reviewer convenience justifies reuse.
8. Automatic checks and receiver acceptance run again for `C2`.
9. Independent QA reruns every affected case and makes a new decision for `C2`.

The original user request, ownership definition, and accepted quality criteria remain valid because the correction did not change the meaning of acceptance. Implementation, handoff, execution, security, data-integrity, and release records for `C1` cannot be reused for `C2` unless their declared dependency set excludes every changed input and policy explicitly accepts that analysis. In this example, the authorization code and Engineering self-test changed, so all observations that exercise or depend on either changed input become `STALE`.

After the repeated negative-route check and every other affected must-pass acceptance criterion pass for `C2` and after the receiver accepts the new handoff, QA records a new decision for each criterion. Policy may then record `RELEASE`, and packaging may produce a package bound only to `C2`; the prior hold and stale decisions remain visible.

If the user changes the meaning of ownership—for example, from individual ownership to organization-wide export—the change creates `revision-0002`, not merely a child implementation candidate. Requirements, quality methods, fixtures, design, and all dependent evidence are reassessed from the earliest affected workflow phase.

## 12. Instantiated records and causal event trace

This is an illustrative run of the target architecture, not a claim that the current package executed the feature. To avoid fabricated hexadecimal values, hashes are written as expressions over exact bytes or canonical records. The expression is the authoritative identity rule; aliases exist only for readability.

### 12.1 Stable identities used below

| Kind | Identity |
|---|---|
| Mission and revision | `M = mission-export-ownership`; `R = revision-0001` |
| Accepted plan | `P = plan-export-ownership-revision-0001` |
| Stage definitions | `S1=goal`, `S2=quality-plan`, `S3=design-oracle`, `S4=implementation`, `S5=freeze`, `S6=independent-verification`, `S7=quality-decision`, `S8=packaging` |
| Stage instances | `S1R=stage-goal-r1`; `S2R=stage-quality-r1`; `S3R=stage-design-r1`; `S4C1`, `S5C1`, `S6C1`, and `S7C1` for `C1`; `S4C2`, `S5C2`, `S6C2`, `S7C2`, and `S8C2` for `C2` |
| Engineering work | `T1=task-export-query-c1`; `A1=attempt-eng-c1`; `G1=grant-eng-c1`; `W1=workspace-eng-c1` |
| First candidate | Readability alias `candidate-0001`; authoritative identity `C1=candidate:SHA256(JCS(manifest-identity-c1))` |
| First QA work | `TQ1=task-qa-c1`; `AQ1=attempt-qa-c1`; `GR1=grant-receive-handoff-c1`; `GQ1=grant-qa-execute-c1`; `GD1=grant-quality-decide-c1`; `WQ1=workspace-qa-c1-readonly` |
| Correction work | `T2=task-correct-authz-c2`; `A2=attempt-eng-c2`; `G2=grant-eng-c2`; `W2=workspace-eng-c2` |
| Child candidate | Readability alias `candidate-0002`; authoritative identity `C2=candidate:SHA256(JCS(manifest-identity-c2))`; parent `C1` |
| Second QA work | `TQ2=task-qa-c2`; `AQ2=attempt-qa-c2`; `GR2=grant-receive-handoff-c2`; `GQ2=grant-qa-execute-c2`; `GD2=grant-quality-decide-c2`; `WQ2=workspace-qa-c2-readonly` |
| Final decision and package | `QD2=quality-decision-c2`; `ES2=evidence-set-c2`; `GP2=grant-package-c2`; `PKG2=package-export-ownership-c2` |

Every record below carries `M` and `R`. Stage, task, attempt, grant, workspace, candidate, handoff, evidence, and decision identities are added when applicable. Omitting an applicable binding is a schema failure; the binding cannot be inferred from prose.

### 12.2 Revision-bound stage gates

| Gate result | Object and authoritative prior state | Required records checked | Accepted result and next state | Failure return |
|---|---|---|---|---|
| `gate-goal-r1-pass` | mission revision `M/R:SUFFICIENCY_PENDING`; stage `S1R:READY` | Exact request digest, planning-readiness table, open-assumption disposition, and Requirements authority | `goal-r1`; mission revision `M/R:QUALITY_PLANNING`; `S1R:COMPLETED`; `S2R:READY` | `SUFFICIENCY_PENDING` |
| `gate-quality-r1-pass` | mission revision `M/R:QUALITY_PLANNING`; stage `S2R:READY` | `goal-r1`, contributions from all three areas of responsibility, `quality-r1`, `perspectives-r1`, and the risk list | `baseline-r1`; mission revision `M/R:BASELINED`; `S2R:COMPLETED`; `S3R:READY` | The missing contribution or goal definition |
| `gate-design-r1-pass` | mission revision `M/R:BASELINED`; stage `S3R:READY` | `design-export-r1`, `fixture-ownership-r1`, `expected-ownership-r1`, work breakdown, design authority, and independent expected-result authority | `work-order-c1`; mission revision `M/R:EXECUTING`; `S3R:COMPLETED`; `S4C1:READY`; `T1:READY` | Design or quality planning |
| `gate-implementation-c1-pass` | task `T1:RESULT_SUBMITTED`; stage `S4C1:RUNNING` | Consumed `G1`, `exec-eng-c1`, required source and self-test artifacts, and limitations | `result-eng-c1`; `T1:COMPLETED`; `S4C1:COMPLETED`; `S5C1:READY`; `assembly-c1:ASSEMBLING` | The last verified implementation checkpoint |
| `gate-freeze-c1-pass` | `assembly-c1:ASSEMBLING`; stage `S5C1:READY` | `result-eng-c1`, baseline, design, fixtures, toolchain, `manifest-identity-c1`, path and regular-file checks | `manifest-record-c1`; `C1:FROZEN`; `S5C1:COMPLETED`; `S6C1:READY`; submitted handoff and planned QA records | `ASSEMBLING` with no candidate issued |
| `gate-verification-c1-fail` | task `TQ1:RESULT_SUBMITTED`; candidate `C1:VERIFYING`; stage `S6C1:RUNNING` | Accepted handoff, consumed `GQ1`, valid QA observation, fixture, expected result, and finding | `TQ1:COMPLETED`; quality item `authorization-isolation:FAIL`; `S6C1:COMPLETED`; `S7C1:READY`; `GD1:ISSUED` | Correct the invalid QA method or require a child candidate |
| `gate-quality-c1-hold` | candidate `C1:VERIFYING`; quality decision `quality-c1:PENDING`; grant `GD1:ISSUED` | All required `C1` item records, `finding-authz-c1`, and residual risk | `GD1:CONSUMED`; `quality-decision-c1=HOLD`; `C1:MANDATORY_FAILURE`; mission revision `M/R:HELD` | Collect missing evidence or plan a child candidate |
| `gate-correction-c2-pass` | task `T2:RESULT_SUBMITTED`; stage `S4C2:RUNNING` | consumed `G2`, `exec-eng-c2`, both changed artifacts, parent `C1`, changed-input declaration | `result-eng-c2`; `T2:COMPLETED`; `S4C2:COMPLETED`; `S5C2:READY`; `assembly-c2:ASSEMBLING` | correction checkpoint |
| `gate-freeze-c2-pass` | `assembly-c2:ASSEMBLING`; stage `S5C2:READY` | `result-eng-c2`, parent `C1`, `manifest-identity-c2`, and all required candidate inputs | `manifest-record-c2`; `C2:FROZEN`; `S5C2:COMPLETED`; `S6C2:READY`; submitted handoff and planned QA records | Child remains `ASSEMBLING` |
| `gate-verification-c2-pass` | task `TQ2:RESULT_SUBMITTED`; candidate `C2:VERIFYING`; stage `S6C2:RUNNING` | Fresh accepted handoff, consumed `GQ2`, valid repeated observations, and accepted dependency decisions for unaffected evidence | `TQ2:COMPLETED`; affected items `PASS`; `S6C2:COMPLETED`; `S7C2:READY`; `GD2:ISSUED` | Correct the invalid method or require another child candidate |
| `gate-quality-c2-release` | quality decision `QD2:PENDING`; candidate `C2:VERIFYING`; grant `GD2:ISSUED` | Complete `ES2`; no stale required evidence and no outstanding blocker or compensation | `GD2:CONSUMED`; `QD2=RELEASE`; `C2:QUALITY_DECIDED`; mission revision `M/R:QUALITY_DECIDED`; `S7C2:COMPLETED` | `HOLD` or `DO_NOT_RELEASE` |
| `gate-package-eligibility-c2-pass` | candidate `C2:QUALITY_DECIDED`; `QD2:RELEASE` | Exact `C2`, `QD2`, `ES2`, and release scope | `C2:PACKAGE_ELIGIBLE`; `S8C2:READY`; `package-task-c2:READY` | Remain `QUALITY_DECIDED` |
| `gate-package-c2-pass` | package task `package-task-c2:RESULT_SUBMITTED`; stage `S8C2:RUNNING`; grant `GP2:CONSUMED` | Exact `C2`, `QD2`, `ES2`, the package manifest payload, and the produced package bytes | `package-task-c2:COMPLETED`; `S8C2:COMPLETED`; package `PKG2:CREATED`; mission revision `M/R:RELEASED` | The package task fails; the candidate remains unchanged |

### 12.3 Compact execution, manifest, handoff, QA, and package records

The candidate example defines these exact byte sequences:

```text
B_SRC_C1 = UTF8("primary_owner=principal.account_id\nsecondary_owner=request.account_id\n")
B_SRC_C2 = UTF8("primary_owner=principal.account_id\nsecondary_owner=principal.account_id\n")
B_SELFTEST_C1 = UTF8("self-test=primary-owner-only\nstatus=pass\n")
B_SELFTEST_C2 = UTF8("self-test=primary-and-secondary-owner\nstatus=pass\n")
B_FIXTURE = UTF8("requester=A\nowned=A:a1\nforeign=B:b1\n")
B_EXPECTED = UTF8("A:a1\n")
B_OBSERVED_C1 = UTF8("A:a1\nB:b1\n")
B_OBSERVED_C2 = UTF8("A:a1\n")
```

`exec-eng-c1` is a single atomic execution record:

```yaml
execution_id: exec-eng-c1
bindings: [M, R, S4C1, T1, A1, G1, W1]
issued_worker: worker-export-engineering-01
derived_role: engineering-delivery
executable: python@approved-digest
arguments: ["-m", "pytest", "self_tests/export"]
bounded_environment: env-export-r1
exit_status: 0
stdout_ref: artifact:stdout-eng-c1
outputs:
  - path: src/export_ownership.rules
    size: len(B_SRC_C1)
    sha256: SHA256(B_SRC_C1)
  - path: self_tests/export_ownership.txt
    size: len(B_SELFTEST_C1)
    sha256: SHA256(B_SELFTEST_C1)
authority_consumption: G1:CONSUMED
```

`exec-eng-c2` uses the same record shape with bindings `M,R,S4C2,T2,A2,G2,W2,C1`; the parent binding is explicit because this attempt corrects `C1`. The execution exits `0`, produces `src/export_ownership.rules` as `B_SRC_C2` and `self_tests/export_ownership.txt` as `B_SELFTEST_C2`, records both sizes and hashes, and consumes `G2`. The independent QA fixture is not an Engineering output in either attempt.

The first canonical manifest abbreviates unchanged baseline and toolchain entries but does not omit them from the actual record:

| `manifest-identity-c1` entry | Size | SHA-256 | Producer/source |
|---|---|---|---|
| `src/export_ownership.rules` | `len(B_SRC_C1)` | `SHA256(B_SRC_C1)` | `exec-eng-c1` |
| `self_tests/export_ownership.txt` | `len(B_SELFTEST_C1)` | `SHA256(B_SELFTEST_C1)` | `exec-eng-c1` |
| `qa/fixture-ownership.txt` | `len(B_FIXTURE)` | `SHA256(B_FIXTURE)` | `fixture-ownership-r1` under independent expected-result authority |
| `qa/expected-ownership.txt` | `len(B_EXPECTED)` | `SHA256(B_EXPECTED)` | `expected-ownership-r1` under independent expected-result authority |
| `baseline/requirements.json` | `len(JCS(baseline-r1))` | `SHA256(JCS(baseline-r1))` | `gate-quality-r1-pass` |
| `build/toolchain.json` | `len(JCS(toolchain-r1))` | `SHA256(JCS(toolchain-r1))` | accepted toolchain record |

`manifest-identity-c1` contains the table entries above, accepted build and toolchain identity, `M`, `R`, and `parent_candidate_id=null`. The outer `manifest-record-c1` contains that payload plus `manifest_digest=SHA256(JCS(manifest-identity-c1))` and `candidate_id=C1`; neither derived field is inside the hashed payload. `manifest-identity-c2` replaces the source and Engineering self-test entries with `B_SRC_C2` and `B_SELFTEST_C2`, keeps the independent fixture and expected result unchanged, and sets `parent_candidate_id=C1`. The outer `manifest-record-c2` adds `manifest_digest=SHA256(JCS(manifest-identity-c2))` and `candidate_id=C2`.

The handoff records identify both acceptance checks:

| Record | Bound identities | Decision and reason |
|---|---|---|
| `handoff-c1` | `M,R,S6C1,T1,TQ1,C1,manifest-record-c1,result-eng-c1` | Engineering requests independent verification using `fixture-ownership-r1` |
| `handoff-auto-c1-pass` | `handoff-c1`, producer authority `G1`, `C1` | Schema, required types, normalized paths, regular files, hashes, and lineage all pass |
| `handoff-receiver-c1-pass` | `handoff-c1`, receiver authority `GR1`, receiver `worker-export-qa-01` | The receiver accepts the baseline, fixture, expected result, build instruction, limitation, and QA action as complete and usable |
| `handoff-c2` / `handoff-auto-c2-pass` / `handoff-receiver-c2-pass` | `M,R,S6C2,T2,TQ2,C2,manifest-record-c2,result-eng-c2,G2,GR2` | Both decisions are repeated for the child; acceptance of `C1` is not substituted |

The failing QA evidence is a single atomic record:

```yaml
evidence_id: evidence-authz-c1-fail
bindings: [M, R, S6C1, TQ1, AQ1, GQ1, WQ1, C1, handoff-receiver-c1-pass]
runner: runner-qa-01
command: ["verify-export", "--route", "secondary", "--fixture", "fixture-ownership-r1"]
fixture_sha256: SHA256(B_FIXTURE)
expected_sha256: SHA256(B_EXPECTED)
observed_path: qa-out/secondary-account-a.txt
observed_size: len(B_OBSERVED_C1)
observed_sha256: SHA256(B_OBSERVED_C1)
exit_status: 1
quality_item: authorization-isolation
finding_id: finding-authz-c1
decision: FAIL
authority_consumption: GQ1:CONSUMED
```

The corresponding child evidence, `evidence-authz-c2-pass`, binds `M,R,S6C2,TQ2,AQ2,GQ2,WQ2,C2,handoff-receiver-c2-pass`, uses the same fixture and expected bytes, and records `B_OBSERVED_C2`, exit status `0`, and decision `PASS`. `ES2` is the canonical ordered set of all required `C2` evidence IDs plus the accepted dependency-reuse decisions. `QD2` identifies `ES2` and the release scope. The final package record is:

```yaml
package_id: PKG2
bindings: [M, R, S8C2, package-task-c2, GP2, C2, QD2, ES2]
package_manifest_payload: package-manifest-identity-c2
package_manifest_digest: SHA256(JCS(package-manifest-identity-c2))
package_bytes: exact bytes produced from C2 by the approved packager
package_sha256: SHA256(package_bytes)
state: CREATED
```

### 12.4 State-changing event trace

Every prior and next state names its state-machine object. All rows bind `M` and `R`; the bindings column gives every additional identity required for that event.

| Event | Authoritative object state before | Additional bindings | Checked authority and result | Produced record | Authoritative object state after |
|---|---|---|---|---|---|
| `event-0001-request` | mission `M:ABSENT`; revision `R:ABSENT` | exact request bytes | Mission Service authority to create the mission: pass | request digest, `M`, `R`, `S1R`, `S2R` | mission revision `M/R:SUFFICIENCY_PENDING`; `S1R:READY`; `S2R:PLANNED` |
| `event-0002-goal` | mission revision `M/R:SUFFICIENCY_PENDING`; `S1R:READY`; `S2R:PLANNED` | Requirements authority and planning-readiness table | `gate-goal-r1-pass` | `goal-r1` | mission revision `M/R:QUALITY_PLANNING`; `S1R:COMPLETED`; `S2R:READY` |
| `event-0003-quality` | mission revision `M/R:QUALITY_PLANNING`; `S2R:READY` | contribution IDs from all three areas of responsibility, `quality-r1`, `perspectives-r1`, `P` | `gate-quality-r1-pass` | `baseline-r1` | mission revision `M/R:BASELINED`; `S2R:COMPLETED`; `S3R:READY` |
| `event-0004-design-oracle` | mission revision `M/R:BASELINED`; `S3R:READY` | `design-export-r1`, `fixture-ownership-r1`, `expected-ownership-r1` | `gate-design-r1-pass` | `work-order-c1`, `T1`, `A1`, `W1` | mission revision `M/R:EXECUTING`; `S3R:COMPLETED`; `S4C1:READY`; `T1:READY`; `A1:READY`; `W1:ALLOCATED` |
| `event-0005-authorize-c1` | `S4C1:READY`; `T1:READY`; `A1:READY`; `W1:ALLOCATED` | Engineering assignment and bounded operations | one-use authority grant issuance: pass | `G1:ISSUED` | `T1:AUTHORIZED`; `A1:AUTHORIZED`; other named states unchanged |
| `event-0006-start-c1` | `S4C1:READY`; `T1:AUTHORIZED`; `A1:AUTHORIZED`; `G1:ISSUED` | `W1`, approved executable and inputs | runner identity and grant checks at task start: pass | start event | `S4C1:RUNNING`; `T1:RUNNING`; `A1:RUNNING`; `G1:ISSUED` |
| `event-0007-result-c1` | `S4C1:RUNNING`; `T1:RUNNING`; `A1:RUNNING`; `G1:ISSUED` | `W1,B_SRC_C1,B_SELFTEST_C1` | exit and output checks: pass; `G1` consumed | `exec-eng-c1`, `result-eng-c1` | `T1:RESULT_SUBMITTED`; `A1:RESULT_SUBMITTED`; `G1:CONSUMED`; `S4C1:RUNNING` |
| `event-0008-implementation-gate-c1` | `S4C1:RUNNING`; `T1:RESULT_SUBMITTED`; `A1:RESULT_SUBMITTED`; `G1:CONSUMED` | `exec-eng-c1`, all required outputs | `gate-implementation-c1-pass` | accepted Engineering result, `assembly-c1` | `T1:COMPLETED`; `A1:COMPLETED`; `S4C1:COMPLETED`; `S5C1:READY`; `assembly-c1:ASSEMBLING` |
| `event-0009-freeze-c1` | mission revision `M/R:EXECUTING`; `S5C1:READY`; `assembly-c1:ASSEMBLING` | `manifest-identity-c1`, baseline, design, fixtures, toolchain | `gate-freeze-c1-pass` | `manifest-record-c1`, `C1`, `handoff-c1`, `TQ1`, `AQ1`, `WQ1`, and `C1` quality records | `assembly-c1:FROZEN`; `C1:FROZEN`; `S5C1:COMPLETED`; `S6C1:READY`; `handoff-c1:SUBMITTED`; `TQ1:PLANNED`; `AQ1:PLANNED`; `WQ1:ALLOCATED`; `authorization-isolation-c1:PENDING`; `quality-c1:PENDING` |
| `event-0010-handoff-auto-c1` | `C1:FROZEN`; `handoff-c1:SUBMITTED`; `TQ1:PLANNED` | `manifest-record-c1,T1,TQ1,C1,G1` | automatic handoff checks: pass | `handoff-auto-c1-pass`, `GR1:ISSUED` | `handoff-c1:AWAITING_RECEIVER`; other named states unchanged |
| `event-0011-handoff-receiver-c1` | `handoff-c1:AWAITING_RECEIVER`; `TQ1:PLANNED`; `AQ1:PLANNED`; `GR1:ISSUED` | `C1,worker-export-qa-01` | receiver acceptance: pass; `GR1` consumed | `handoff-receiver-c1-pass` | `handoff-c1:ACCEPTED`; `TQ1:READY`; `AQ1:READY`; `GR1:CONSUMED` |
| `event-0012-authorize-qa-c1` | `S6C1:READY`; `TQ1:READY`; `AQ1:READY`; `WQ1:ALLOCATED`; `C1:FROZEN` | accepted handoff and QA assignment | read-only QA authority issuance: pass | `GQ1:ISSUED` | `TQ1:AUTHORIZED`; `AQ1:AUTHORIZED`; other named states unchanged |
| `event-0013-start-qa-c1` | `S6C1:READY`; `TQ1:AUTHORIZED`; `AQ1:AUTHORIZED`; `GQ1:ISSUED`; `C1:FROZEN` | `WQ1,handoff-receiver-c1-pass` | QA runner and read-only candidate checks: pass | QA start event | `S6C1:RUNNING`; `TQ1:RUNNING`; `AQ1:RUNNING`; `C1:VERIFYING`; `GQ1:ISSUED` |
| `event-0014-result-qa-c1` | `S6C1:RUNNING`; `TQ1:RUNNING`; `AQ1:RUNNING`; `C1:VERIFYING`; `GQ1:ISSUED` | fixture, expected result, `B_OBSERVED_C1` | observation accepted; expected comparison fails; `GQ1` consumed | `exec-qa-c1`, `evidence-authz-c1-fail:VALID`, `finding-authz-c1` | `TQ1:RESULT_SUBMITTED`; `AQ1:RESULT_SUBMITTED`; `GQ1:CONSUMED`; `authorization-isolation-c1:PENDING`; `C1:VERIFYING` |
| `event-0015-verification-gate-c1` | `S6C1:RUNNING`; `TQ1:RESULT_SUBMITTED`; `AQ1:RESULT_SUBMITTED`; `C1:VERIFYING`; `evidence-authz-c1-fail:VALID` | accepted handoff, execution, finding, and required `C1` observations | `gate-verification-c1-fail` | `GD1:ISSUED` | `TQ1:COMPLETED`; `AQ1:COMPLETED`; `S6C1:COMPLETED`; `S7C1:READY`; `authorization-isolation-c1:FAIL`; `C1:VERIFYING` |
| `event-0016-hold-c1` | mission revision `M/R:EXECUTING`; `S7C1:READY`; `quality-c1:PENDING`; `authorization-isolation-c1:FAIL`; `C1:VERIFYING`; `GD1:ISSUED` | complete `C1` quality records | `gate-quality-c1-hold`; `GD1` consumed | `quality-decision-c1=HOLD` | mission revision `M/R:HELD`; `S7C1:COMPLETED`; `quality-c1:HOLD`; `C1:MANDATORY_FAILURE`; `GD1:CONSUMED` |
| `event-0017-plan-child-c2` | mission revision `M/R:HELD`; `C1:MANDATORY_FAILURE`; `quality-c1:HOLD` | `finding-authz-c1`, authorized correction plan | child-candidate planning and reopening of the earliest affected workflow phase: pass | correction work order, `T2`, `A2`, `W2`, `assembly-c2`, `S4C2` | mission revision `M/R:EXECUTING`; `C1:CHILD_REQUIRED`; `S4C2:READY`; `T2:READY`; `A2:READY`; `W2:ALLOCATED`; `assembly-c2:PLANNED` |
| `event-0018-authorize-correction` | `S4C2:READY`; `T2:READY`; `A2:READY`; `W2:ALLOCATED`; `C1:CHILD_REQUIRED` | correction-only operations | one-use authority grant issuance: pass | `G2:ISSUED` | `T2:AUTHORIZED`; `A2:AUTHORIZED`; other named states unchanged |
| `event-0019-start-correction` | `S4C2:READY`; `T2:AUTHORIZED`; `A2:AUTHORIZED`; `G2:ISSUED` | `W2,C1` | runner identity and grant checks at correction start: pass | correction start event | `S4C2:RUNNING`; `T2:RUNNING`; `A2:RUNNING`; `G2:ISSUED` |
| `event-0020-result-correction` | `S4C2:RUNNING`; `T2:RUNNING`; `A2:RUNNING`; `G2:ISSUED` | `C1`, source change `B_SRC_C1→B_SRC_C2`, self-test change `B_SELFTEST_C1→B_SELFTEST_C2` | exit and both output checks: pass; `G2` consumed | `exec-eng-c2`, `result-eng-c2`, changed-input declaration | `T2:RESULT_SUBMITTED`; `A2:RESULT_SUBMITTED`; `G2:CONSUMED`; `S4C2:RUNNING` |
| `event-0021-correction-gate` | `S4C2:RUNNING`; `T2:RESULT_SUBMITTED`; `A2:RESULT_SUBMITTED`; `G2:CONSUMED`; `assembly-c2:PLANNED` | `exec-eng-c2`, both changed artifacts, parent `C1` | `gate-correction-c2-pass` | accepted correction result | `T2:COMPLETED`; `A2:COMPLETED`; `S4C2:COMPLETED`; `S5C2:READY`; `assembly-c2:ASSEMBLING` |
| `event-0022-freeze-c2` | mission revision `M/R:EXECUTING`; `S5C2:READY`; `assembly-c2:ASSEMBLING` | `manifest-identity-c2`, parent `C1`, baseline and toolchain | `gate-freeze-c2-pass` | `manifest-record-c2`, `C2`, `handoff-c2`, `TQ2`, `AQ2`, `WQ2`, and `C2` quality records | `assembly-c2:FROZEN`; `C2:FROZEN`; `S5C2:COMPLETED`; `S6C2:READY`; `handoff-c2:SUBMITTED`; `TQ2:PLANNED`; `AQ2:PLANNED`; `WQ2:ALLOCATED`; `authorization-isolation-c2:PENDING`; `QD2:PENDING` |
| `event-0023-invalidate-c1-evidence` | `evidence-authz-c1-fail:VALID`; `quality-c1:HOLD`; `C2:FROZEN`; `authorization-isolation-c2:PENDING` | source dependency `SHA256(B_SRC_C1)→SHA256(B_SRC_C2)`, self-test dependency `SHA256(B_SELFTEST_C1)→SHA256(B_SELFTEST_C2)`, `C1,C2` | dependency analysis: affected | `stale-authz-c1`, `stale-quality-c1`; replacement requirements for `C2` | `evidence-authz-c1-fail:STALE`; `quality-c1:STALE`; `authorization-isolation-c2:PENDING`; `C2:FROZEN` |
| `event-0024-handoff-auto-c2` | `C2:FROZEN`; `handoff-c2:SUBMITTED`; `TQ2:PLANNED` | `manifest-record-c2,T2,TQ2,C2,G2` | automatic handoff checks: pass | `handoff-auto-c2-pass`, `GR2:ISSUED` | `handoff-c2:AWAITING_RECEIVER`; other named states unchanged |
| `event-0025-handoff-receiver-c2` | `handoff-c2:AWAITING_RECEIVER`; `TQ2:PLANNED`; `AQ2:PLANNED`; `GR2:ISSUED` | `C2,worker-export-qa-02` | receiver acceptance: pass; `GR2` consumed | `handoff-receiver-c2-pass` | `handoff-c2:ACCEPTED`; `TQ2:READY`; `AQ2:READY`; `GR2:CONSUMED` |
| `event-0026-authorize-qa-c2` | `S6C2:READY`; `TQ2:READY`; `AQ2:READY`; `WQ2:ALLOCATED`; `C2:FROZEN` | accepted handoff and QA assignment | read-only QA authority issuance: pass | `GQ2:ISSUED` | `TQ2:AUTHORIZED`; `AQ2:AUTHORIZED`; other named states unchanged |
| `event-0027-start-qa-c2` | `S6C2:READY`; `TQ2:AUTHORIZED`; `AQ2:AUTHORIZED`; `GQ2:ISSUED`; `C2:FROZEN` | `WQ2,handoff-receiver-c2-pass` | QA runner and read-only candidate checks: pass | QA start event | `S6C2:RUNNING`; `TQ2:RUNNING`; `AQ2:RUNNING`; `C2:VERIFYING`; `GQ2:ISSUED` |
| `event-0028-result-qa-c2` | `S6C2:RUNNING`; `TQ2:RUNNING`; `AQ2:RUNNING`; `C2:VERIFYING`; `GQ2:ISSUED` | fixture, expected result, `B_OBSERVED_C2` | observation accepted; expected comparison passes; `GQ2` consumed | `exec-qa-c2`, `evidence-authz-c2-pass:VALID` | `TQ2:RESULT_SUBMITTED`; `AQ2:RESULT_SUBMITTED`; `GQ2:CONSUMED`; `authorization-isolation-c2:PENDING`; `C2:VERIFYING` |
| `event-0029-verification-gate-c2` | mission revision `M/R:EXECUTING`; `S6C2:RUNNING`; `TQ2:RESULT_SUBMITTED`; `AQ2:RESULT_SUBMITTED`; `C2:VERIFYING`; `evidence-authz-c2-pass:VALID` | newly accepted handoff, repeated observations for affected items, and accepted dependency decisions for every unaffected item | `gate-verification-c2-pass` | complete `C2` evidence set `ES2`, `GD2:ISSUED` | mission revision `M/R:QUALITY_DECISION_PENDING`; `TQ2:COMPLETED`; `AQ2:COMPLETED`; `S6C2:COMPLETED`; `S7C2:READY`; all required `C2` items `PASS`; `C2:VERIFYING` |
| `event-0030-quality-release-c2` | mission revision `M/R:QUALITY_DECISION_PENDING`; `S7C2:READY`; `QD2:PENDING`; all required `C2` items `PASS`; `C2:VERIFYING`; `GD2:ISSUED` | `ES2`; no stale required evidence and no outstanding blocker or compensation | `gate-quality-c2-release`; `GD2` consumed | `QD2=RELEASE`, `package-task-c2:PLANNED` | mission revision `M/R:QUALITY_DECIDED`; `S7C2:COMPLETED`; `QD2:RELEASE`; `C2:QUALITY_DECIDED`; `GD2:CONSUMED`; `package-task-c2:PLANNED` |
| `event-0031-package-eligibility` | mission revision `M/R:QUALITY_DECIDED`; `C2:QUALITY_DECIDED`; `QD2:RELEASE`; `package-task-c2:PLANNED` | exact `C2,QD2,ES2` and release scope | `gate-package-eligibility-c2-pass` | package work order | `C2:PACKAGE_ELIGIBLE`; `S8C2:READY`; `package-task-c2:READY` |
| `event-0032-authorize-package` | `C2:PACKAGE_ELIGIBLE`; `S8C2:READY`; `package-task-c2:READY` | package-only operations, `QD2,ES2` | one-use package authority issuance: pass | `GP2:ISSUED` | `package-task-c2:AUTHORIZED`; other named states unchanged |
| `event-0033-start-package` | `S8C2:READY`; `package-task-c2:AUTHORIZED`; `GP2:ISSUED`; `C2:PACKAGE_ELIGIBLE` | approved packager and output root | packager identity and grant start checks: pass | package start event | `S8C2:RUNNING`; `package-task-c2:RUNNING`; `GP2:ISSUED` |
| `event-0034-package-result` | `S8C2:RUNNING`; `package-task-c2:RUNNING`; `GP2:ISSUED`; `C2:PACKAGE_ELIGIBLE` | `C2,QD2,ES2,package-manifest-identity-c2` | package production and output capture: pass; `GP2` consumed | `package-result-c2:SUBMITTED`, package bytes and digest | `package-task-c2:RESULT_SUBMITTED`; `GP2:CONSUMED`; `S8C2:RUNNING` |
| `event-0035-package-gate` | mission revision `M/R:QUALITY_DECIDED`; `C2:PACKAGE_ELIGIBLE`; `S8C2:RUNNING`; `package-task-c2:RESULT_SUBMITTED`; `GP2:CONSUMED`; `package-result-c2:SUBMITTED` | exact `C2,QD2,ES2`, package manifest payload and package bytes | `gate-package-c2-pass` | accepted `PKG2` | mission revision `M/R:RELEASED`; `S8C2:COMPLETED`; `package-task-c2:COMPLETED`; `PKG2:CREATED` |

No event is accepted solely because submitted data names the expected role or state. A rejected transition appends a rejection reason but leaves every named authoritative object in its prior state.

## 13. False-completion rejection

| Submitted input | Rejection reason | Authoritative state after rejection | Appended decision and permitted follow-up |
|---|---|---|---|
| Caller data says `role = "qa"` without an issued QA grant | Caller-supplied text does not establish identity or authority | Candidate and quality states remain unchanged | Append an unauthorized-operation rejection; obtain a properly issued authority grant instead of retrying the same payload |
| An Engineering payload says `"pass": true` without execution evidence | A self-report is not an independent observation or quality decision | The Engineering result may remain untrusted; no task, stage, or release advances | Append an invalid-evidence rejection; run the required method under captured execution |
| A test result belongs to `revision-0000` | The meaning of acceptance or the inputs may differ | Active `revision-0001` remains pending | Append an identity-mismatch rejection; rerun the test or justify reuse through explicit dependency analysis |
| Candidate bytes change after their hashes were recorded | The reviewed bytes are no longer the identified candidate | The old candidate becomes `CORRUPT` or remains rejected; the old approval cannot advance | Append mutation and `STALE` decisions; create and verify a child candidate |
| The implementer submits final approval | Implementation and final quality judgment require separate authority | The candidate continues to await an independent decision | Append a self-approval rejection; route the frozen candidate to authorized QA |
| A required export artifact is missing | The output cannot be inspected or hashed | The handoff remains unaccepted, and the stage remains incomplete | Append a missing-output rejection; the producer may submit a complete result under a remaining valid authority grant or a newly issued authority grant |
| A manifest path escapes the root through a symbolic link | The bytes are not confined to the approved candidate | No candidate identity is issued | Append a path-confinement rejection; remove the prohibited link and assemble a new candidate input set |
| A test exits zero, but the required negative fixture did not run | Exit status does not satisfy the evidence requirements for that workflow phase | The required item remains `PENDING` or `INSUFFICIENT`; the release remains held | Append an incomplete-method rejection; execute the omitted fixture under valid QA authority |
| A result is for another mission or an inactive candidate | Evidence is not transferable across identities | The active mission and candidate remain unchanged | Append an identity-mismatch decision and retain the payload only for diagnosis; execute against the active identity |
| A checkpoint message exists, but its metadata or artifacts were not durably verified | No safe resume point has been established | The last verified checkpoint remains authoritative | Append an invalid-checkpoint rejection; resume from the earlier point or restart the affected unit |

These are ordinary transition checks, not exceptional manual-review rules. Under this architecture, every one of these violations is rejected.

## 14. Worked-mission scope

The example demonstrates how the target structure connects intent, revision, areas of responsibility, authority, execution, candidate bytes, evidence, quality, and release. It does not prove that the current repository enforces the full path, that the feature itself exists, or that all defects would be found.
