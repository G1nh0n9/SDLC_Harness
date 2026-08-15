# Reliability and Recovery

> **This chapter explains:** how the harness verifies completion and handles interruptions, retries, duplicate delivery, and rework discovered after completion.

This document applies failures to the stable steps from the [worked mission](worked-mission-overview.md) and [runtime overview](runtime-overview.md):

> **Example `export-ownership`:** Add an authenticated data-export feature that returns only records owned by the requesting account.

The target does not offer one undifferentiated “exactly once” guarantee. Each guarantee has its own scope, persisted boundary, and recovery obligation:

| Scope | User-visible guarantee | Retry or replay unit | Persisted boundary | Duplicate and external-side-effect rule | Required operator or developer action |
|---|---|---|---|---|---|
| Policy decision | Redelivery of the same accepted event does not repeat the state change | Event identity | Accepted decision event | A different event is evaluated separately; a superseded result cannot advance | Submit a new authorized request when the intended operation changes |
| Task progress | A new attempt resumes only from verified durable progress | Logical task operation | Checkpoint metadata and checked artifact hashes | Unverified partial output is diagnostic only | Define safe checkpoint boundaries and complete outputs |
| Candidate review | Review and findings remain bound to unchanged material | Child candidate, not in-place edit | Frozen manifest and parent-child lineage | A changed input creates a new identity and makes affected evidence `STALE` | Declare dependencies and rerun every affected check |
| External operation | An unknown outcome is not repeated before reconciliation | Stable logical operation across attempts | Start record, receipt, status observation, and compensation result | The harness does not claim exactly-once execution in another system | Provide a status query, duplicate-suppression key, compensation, or an explicit blocked state |
| Release decision | Only the active candidate and complete valid evidence set can support release | Quality and package decision | Criterion results, evidence-set identity, release scope, and package binding | Later valid rework invalidates completion without erasing history | Resolve the blocker and create fresh affected evidence |

## 1. Completion evidence requirements

The Policy and State Engine can mark a task or mission complete only when the required records establish completion. The end of a model response is not sufficient.

```text
model call ended
  ≠ attempt finished
  ≠ required artifacts submitted
  ≠ handoff accepted
  ≠ quality verified
  ≠ stage completed
  ≠ mission completed
```

Each transition requires a separate accepted event. Later levels may depend on earlier ones, but a message or status at one level does not imply the next.

The checks are:

1. Authority is valid for the mission, revision, stage, task, worker, workspace, candidate, and operation.
2. The harness captured the required execution or inspection record.
3. Required artifacts exist as regular files under approved roots.
4. Artifact hashes match the submitted manifest.
5. Required stage inputs and outputs are present.
6. Automatic handoff checks pass.
7. The receiver accepts the handoff.
8. Every must-pass acceptance criterion has a valid observation and decision.
9. No blocking finding, external operation with an unknown outcome, confirmed residual side effect, or pending compensation remains.
10. All evidence refers to the active mission revision and candidate.

When an obligation fails, policy records the reason and returns the work to the earliest affected workflow stage.

## 2. Normal completion path

For `export-ownership`, the candidate can advance only when the evidence shows at least that:

- an authenticated account can export its own records;
- an account cannot export another account's records;
- malformed or unauthorized requests fail as specified;
- the output schema and data scope match the baseline;
- the observed commands, fixtures, and artifacts belong to the frozen candidate;
- independent QA has recorded decisions for the must-pass acceptance criteria for security and data integrity.

A passing Engineering self-test is useful but cannot replace the independent negative case or quality decision.

## 3. Checkpoint interruption

Assume Engineering must produce a query change, an ownership fixture, and an execution report. The logical task is `task-export-query`; each process execution has a different attempt identity.

### 3.1 Interruption before checkpoint commit

The worker writes a partial fixture and reports that it saved its progress, but it stops before the harness durably writes and verifies the checkpoint metadata and artifact hashes.

Policy records `attempt-0001` as interrupted. The partial file is diagnostic material, not resumable progress. A new attempt receives a new authority grant for the same logical task and starts from the previous verified boundary. It may reconstruct the incomplete fixture, but it cannot present the partial bytes as an accepted stage output.

### 3.2 Interruption after checkpoint commit

The worker completes the query change and fixture and writes checkpoint metadata. The harness durably stores both files, recalculates their SHA-256 values, and records the next operation. The process then stops while producing the execution report.

Policy records `attempt-0002` as interrupted but retains the verified checkpoint. `attempt-0003` receives a new authority grant for `task-export-query`, reads only the checkpointed files, and resumes at the execution-report operation. It does not repeat the completed source mutation or claim that the new attempt produced the earlier files.

The mission and logical task retain their identities. Attempt history shows which worker produced each accepted output. A checkpoint becomes valid only after the harness durably writes and verifies its metadata and referenced artifacts; a model message saying "checkpoint saved" is insufficient.

## 4. Duplicate results

Assume the first worker's successful result is delayed and arrives after a replacement worker has already submitted the same logical task.

Policy compares mission, revision, logical task, attempt, candidate, and event identity.

- Redelivery of the same event is ignored and does not duplicate the state change.
- Results from a superseded attempt are retained for diagnosis but cannot advance state.
- Two different outputs for one logical task create a conflict that requires explicit selection or a fresh child candidate; arrival time does not make either output authoritative.

## 5. Unknown external-operation outcome

Assume the export task requests that an external storage service create a temporary encrypted object. The request times out after the service may have created the object.

Policy forbids retrying until it has reconciled the earlier outcome.

1. The action uses a stable logical operation ID.
2. The harness records that the outcome is unknown.
3. Before retrying, it queries the external system by that ID or another stable identity.
4. If the object exists and matches the expected result, the harness records the reconciled outcome.
5. If it does not exist, retry may proceed under policy.
6. If status cannot be queried, the mission remains blocked or follows a mission-specific manual reconciliation procedure.

The deduplication identity is stable across attempts:

```text
deduplication_key = SHA256(
    provider_namespace
    || mission_id
    || revision_id
    || candidate_or_stage_scope
    || logical_operation_id
    || normalized_effect_parameters_digest
)
```

`attempt_id` is deliberately excluded. It remains in the attempt and receipt history so policy can distinguish executions, but adding it to the key would turn each retry into a new external side effect. If what counts as acceptance, the target resource, or the effect parameters change, policy creates a new logical operation rather than silently reusing the old key.

The harness does not claim exactly-once external execution.

## 6. Compensation after partial external success

Assume the external storage service confirms object creation for logical operation `export-object/account-a/request-17`, but the later metadata write fails permanently. The feature cannot safely expose the object, and ordinary retry would create or reveal residual material.

The runner records the successful object receipt and the failed metadata operation separately. Policy enters a compensation-required state and invokes only the compensation action registered for this effect: delete or quarantine the exact object identified by the receipt. Completion remains blocked until policy records one of three outcomes:

1. deletion is confirmed and the external state is reconciled;
2. quarantine is confirmed and an authorized operator accepts the declared residual condition; or
3. compensation fails or cannot be observed, leaving an unresolved residual effect and a release hold.

The history retains both the original effect and the compensating action. A compensation handler is mission-specific; the harness cannot infer how to reverse an irreversible service operation.

## 7. Failed must-pass acceptance criterion

Assume QA demonstrates that Account A can export Account B's records.

- The must-pass security acceptance criterion fails.
- The candidate and finding remain unchanged.
- Engineering cannot edit the reviewed candidate.
- Policy opens a child candidate with the failed candidate as parent.
- The changed implementation and every affected check receive fresh identities.
- Unaffected evidence may be reused only when its dependencies and baseline remain unchanged.

Each must-pass acceptance criterion must pass independently. Better performance or usability cannot offset the authorization failure.

## 8. Completion invalidation after rework

Assume the mission was completed, but later independent confirmation shows that one supported storage backend bypasses the ownership filter.

The system preserves the prior decision rather than erasing or silently relabeling it.

1. A new invalidation event identifies the earlier completion decision.
2. The event records the new observation and affected baseline, candidate, and evidence.
3. Policy reopens the earliest affected stage.
4. Release status changes to hold or another explicitly supported state.
5. A corrected child candidate and fresh affected evidence are required.

Unlike an ordinary pre-completion retry, the history must show that the system withdrew an earlier completion judgment.

## 9. Failure classification

| Failure class | Detection | Required response | Automatic retry? |
|---|---|---|---|
| Transient network or service failure | Timeout or an error classified as transient | Retry the smallest unit with bounded backoff | Yes, within budget |
| Process interruption | Missing heartbeat or process exit | Resume from the last valid checkpoint | Yes, with a new attempt |
| Invalid input or permanent failure | Deterministic validation or permanent error | Return to the responsible planning stage | No |
| Formatting or schema error | Schema validation failure | Apply a bounded repair, then validate again | Yes, only within the defined repair limit |
| Unknown external side effect | Lost response after possible write | Reconcile external state before repetition | Not before reconciliation |
| Partial external success followed by permanent failure | Recorded prior effect and later failure | Run the registered compensation action or record the residual state | Only when the mission-specific compensation rule explicitly authorizes another attempt |
| Failure of a must-pass acceptance criterion | QA decision | Preserve candidate, create child, rerun affected checks | No; correction requires an authorized child candidate |
| User changes goal or constraint | Accepted steering | Create new revision; invalidate dependent work | No |
| Rework discovered after completion | New valid finding | Append completion invalidation; reopen affected stage | No |

## 10. Planned stops and unexpected termination

A planned stop differs from a crash.

During a planned stop, the runner:

1. stops accepting new work for the attempt;
2. reaches the next safe boundary;
3. writes artifacts and checkpoint metadata;
4. verifies the stored checkpoint;
5. records the resume location;
6. releases the worker.

After a crash, the harness uses only the last checkpoint that had already passed those steps.

## 11. Semantic review and verifier disagreement

The design treats presentation-order bias, verbosity preference, self-preference, and correlated model-family errors as separate threats to semantic judgment.

When no deterministic expected-result rule is available, semantic review provides evidence with uncertainty rather than an unquestionable verdict. For example, suppose reviewers compare two versions of the `export-ownership` denial and recovery guidance without an external score. Reviewer 1 prefers option A when shown `(A, B)` but prefers the same text, now labeled option B, when the order is reversed. Reviewer 2 finds the authorization explanation adequate but the operational recovery explanation inadequate. A majority vote would hide both the order effect and the disagreement about specific quality attributes.

The harness requires:

- separate evaluation of quality attributes;
- both presentation orders for pairwise comparison;
- no automatic approval after a material order reversal;
- different model provenance when practical;
- no claim of independence from the same model with different role names alone;
- escalation to insufficient evidence when confidence is low or reviewers materially disagree.

The comparison record preserves each quality-attribute score, presentation order, model and prompt provenance, confidence, and rationale. A material verdict reversal prevents automatic approval. Policy requests another independent method, a different model family where practical, a domain reviewer, or a user decision when the remaining question changes the accepted risk. Policy does not award a higher score merely because the reasoning is longer, and a reviewer cannot treat its own earlier answer as if it came from an independent source.

LLM panels cannot replace execution, checked artifacts, domain-specific expected results and decision rules, or external state reconciliation.

## 12. Release decision after recovery

Recovery does not weaken acceptance criteria. A resumed or repaired mission reaches release only when:

- every reused checkpoint is still valid for the active revision and candidate;
- retried work has a complete attempt history;
- duplicate deliveries did not produce duplicate state changes;
- external side effects are known, reconciled, or compensated;
- all affected checks have fresh evidence;
- no completion invalidation remains unresolved.

**Next:** [Trust Boundaries](trust.md) separates controls enforced by the target harness from required operating-system and external-system controls.
