# Runtime Architecture

> **This chapter explains:** how one mission normally runs and which logical components enforce the rules.

This logical view does not imply that every component is a separately deployed service. The current implementation consists primarily of one Python package with a Hermes plugin surface.

## 1. Representative mission

The documentation uses one scenario throughout:

> **Example `export-ownership`:** Add an authenticated data-export feature that returns only records owned by the requesting account.

The normal path below ends with a release decision. The [reliability and recovery](reliability.md) chapter applies failure scenarios to the same mission.

## 2. Normal execution

### Step 1 — Accept intent and create a revision

The Mission Service records the active user instruction and creates a mission revision. Later steering creates another revision rather than rewriting accepted history.

### Step 2 — Establish the mission and quality baseline

The areas of responsibility contribute in parallel:

| Area of responsibility | Contribution to `export-ownership` |
|---|---|
| Requirements | Authorized user, owned-record scope, output format, user-visible failure behavior, and prohibited cross-account access |
| Engineering | Ownership boundary, dependencies, implementation constraints, cost, and operational impact |
| QA | Independent ownership fixtures, negative cross-account cases, output checks, security observations, and required execution records |

Policy accepts a versioned baseline only after recording the required contributions and any unresolved disputes.

### Step 3 — Assign experts based on the required perspectives

The Goal and Quality Planner enumerates authorization, data integrity, privacy, usability, testability, and operations before grouping the work.

For example:

- format conformance may use a P0 deterministic check;
- baseline usability may require review by an assigned expert under P1;
- authorization may require a security expert with P3 participation;
- cross-account testing may require P4 independent assessment in addition to the selected P0–P3 base level of involvement.

### Step 4 — Issue a bounded authority grant

The Policy and State Engine issues one authority grant for each task attempt. The grant binds:

- mission and revision;
- stage and task;
- worker identity and responsibility;
- workspace and write roots;
- approved tools and executable identities;
- candidate, when one exists;
- expiry and remaining uses.

The worker cannot expand authority by changing a role field in submitted data.

### Step 5 — Execute and checkpoint

The Workspace Broker provides workspace, build, temporary, and home roots specific to the assigned role and task. The Task Runner invokes an approved executable in a bounded environment and captures:

- executable identity and arguments;
- start and finish times;
- timeout and exit status;
- standard output and error;
- produced files and hashes;
- tool calls and external-operation IDs;
- safe checkpoint data.

Policy completes the task only after evaluating the submitted records; the end of a model response is not sufficient.

### Step 6 — Freeze the candidate

Engineering submits the source, requirements and test baselines, design material, build configuration, dependencies, and toolchain identity.

The Candidate Manager:

1. normalizes and validates paths;
2. rejects disallowed symbolic links;
3. computes input and manifest hashes;
4. creates one candidate identity;
5. records parent-child lineage;
6. makes the candidate immutable for verification.

### Step 7 — Verify the handoff

The Handoff Verifier checks structure, lineage, required inputs and outputs, regular-file status, paths, and SHA-256 values.

The receiver then decides whether it can use the handoff without recreating the work. Both checks must pass.

### Step 8 — Rerun checks and record findings

Workers assigned to independent execution rerun the required commands against the frozen candidate. QA compares the observations with the accepted quality baseline.

A finding records:

- affected requirement or quality item;
- candidate and artifact identity;
- location;
- reproduction steps;
- observed and expected behavior;
- impact and uncertainty;
- supporting execution or inspection record.

### Step 9 — Decide release scope

QA records pass, fail, or insufficient evidence for each must-pass acceptance criterion and recommends release, limited release, hold, or do not release. Policy accepts the decision only if every must-pass acceptance criterion has a valid result for the active revision and candidate.

When policy permits it, packaging uses only the approved candidate and evidence set.

## 3. Logical components

### Control group

**Mission Service**

- creates missions and revisions;
- retains the active user instruction;
- routes late asynchronous results to the correct mission inbox;
- determines which earlier records become stale after steering.

**Goal and Quality Planner**

- determines whether the request is specific enough to plan and verify;
- enumerates perspectives and assigns the P0–P3 level of involvement, independent-assessment requirements, and bounded-investigation requirements;
- assigns experts based on compatible perspectives, workflow phases, and independence requirements;
- defines stage inputs, outputs, and verification requirements.

**Policy and State Engine**

- issues and validates authority;
- derives acting identity from issued state;
- accepts or rejects transitions;
- records attempts, retries, checkpoints, failures, recoveries, and invalidations;
- rejects stale or cross-mission reuse.

### Execution group

**Workspace Broker**

- creates role- and task-specific roots;
- validates normalized paths;
- rejects disallowed symbolic links and attempted writes outside approved roots.

**Task Runner**

- invokes approved executables;
- supplies a bounded environment;
- captures execution and external-operation records;
- emits checkpoints at safe boundaries.

### Assurance group

**Candidate Manager**

- computes candidate identity from relevant inputs;
- freezes the review target;
- verifies manifest and lineage;
- detects mutations and requires a child candidate for corrections.

**Handoff Verifier**

- runs automatic structure, path, lineage, and hash checks;
- records receiver acceptance.

**Quality and Release Decision**

- evaluates must-pass acceptance criteria before improvement targets;
- records uncertainty and residual risk;
- permits packaging only from the approved candidate and evidence set.

## 4. Durable records

| Record set | Contents | Question it answers |
|---|---|---|
| Mission and state events | Mission, revision, stage, task, attempt, transition, retry, checkpoint, recovery, invalidation | What state changed and why? |
| Plan and quality records | Perspectives, depth, thresholds, methods, decisions, disputes | What was required? |
| Candidate records | Inputs, manifests, hashes, lineage, mutation status | What exact material was judged? |
| Evidence events | Commands, outputs, artifacts, tests, findings, handoff and release decisions | What was observed and accepted? |

These records may share one database. Their meanings and validation rules remain distinct.

## 5. Authoritative state model

The target architecture does not represent the entire workflow with a single status string. Mission intent, tasks, attempts, candidates, evidence, external side effects, and release decisions change for different reasons. Separate states prevent one successful event from implying that unrelated obligations are complete.

### 5.1 Mission revision and baseline

```text
INTENT_CAPTURED
  → SUFFICIENCY_PENDING
  → QUALITY_PLANNING
  → BASELINED
  → EXECUTING
  → QUALITY_DECISION_PENDING
  ├─→ HELD → EXECUTING when an authorized child correction reopens work
  ├─→ DO_NOT_RELEASE
  └─→ QUALITY_DECIDED → RELEASED | LIMITED_RELEASE
```

`QUALITY_DECIDED` means that the results for each acceptance criterion and the release scope have been accepted; it does not mean that a package exists. Packaging has its own stage and task states. Only successful package acceptance moves the mission revision to `RELEASED` or `LIMITED_RELEASE`.

User steering that changes purpose, scope, forbidden behavior, a must-pass acceptance criterion, or an acceptance method creates a new revision. It does not edit the accepted baseline in place. Policy records which requirements, workflow stages, candidates, and evidence depend on the changed input and reopens the earliest affected workflow stage.

The system preserves later facts after a revision reaches `RELEASED`. A valid later finding can append `COMPLETION_INVALIDATED`, change the active release state to `HELD`, and require a corrected revision or child candidate.

### 5.2 Stage, task, and attempt

```text
PLANNED → READY → AUTHORIZED → RUNNING → RESULT_SUBMITTED → COMPLETED
                         ├─→ INTERRUPTED → RETRY_AUTHORIZED → RUNNING
                         ├─→ RETRYABLE_FAILURE → RETRY_AUTHORIZED
                         ├─→ PERMANENT_FAILURE → RETURNED_TO_RESPONSIBLE_STAGE
                         └─→ BLOCKED
```

A task is the logical unit in the stage plan. An attempt is one execution under one authority grant and retry budget. A retry creates a new attempt while preserving the earlier attempt in the history. `RESULT_SUBMITTED` is not `COMPLETED`: policy must first validate the output and evidence required for that workflow phase.

Only one attempt may be authoritative for a task at a time. A delayed result from a superseded attempt remains diagnostic material and cannot advance state. Duplicate delivery of the same event is idempotent at the state boundary.

### 5.3 Candidate

```text
ASSEMBLING → FROZEN → VERIFYING → QUALITY_DECIDED → PACKAGE_ELIGIBLE
                  ├─→ MUTATION_DETECTED → CORRUPT
                  └─→ MANDATORY_FAILURE → CHILD_REQUIRED
```

Candidate creation fixes the manifest and the set of mandatory evidence required for that candidate. Approval cannot reduce that set. Verification and review refer to the frozen identity. Any change to source, requirements, independent fixtures, build settings, dependencies, toolchain, or any other declared candidate input creates a child candidate and triggers dependency-based evidence reassessment.

Mutation detection does not produce a new valid candidate automatically. Policy rejects the changed target, retains the observed mismatch, and requires the authorized candidate-creation path to compute a new manifest and lineage.

### 5.4 Evidence validity

```text
DECLARED → MATERIAL_PRESENT → IDENTITY_CHECKED → VALID
                                   ├─→ INVALID
VALID + changed dependency         └─→ STALE
```

`INVALID` means the submitted item never satisfied its checks—for example, a missing file, mismatched SHA-256, wrong producer authority, prohibited path, or result for another candidate. `STALE` means an item was valid for an earlier set of inputs but a later accepted change removed its applicability.

Policy derives evidence validity from explicit dependencies; workers cannot set it:

- a baseline change can make design, expected-result, implementation, candidate, verification, and release evidence `STALE`;
- a change to an independently controlled expected result or decision rule makes every result that used the earlier input `STALE`;
- a candidate manifest change makes all execution, inspection, quality, and package evidence tied to that candidate `STALE`;
- a toolchain or build-setting change makes dependent artifacts and observations `STALE`;
- a quality-method change requires a new baseline decision before new results can replace the old method.

### 5.5 External operation and compensation

```text
PLANNED → STARTED → SUCCEEDED | FAILED | UNKNOWN
UNKNOWN → RECONCILING → CONFIRMED_SUCCEEDED | RETRY_ALLOWED | BLOCKED
SUCCEEDED + later permanent failure → COMPENSATION_REQUIRED
COMPENSATION_REQUIRED → COMPENSATED | RESIDUAL_EFFECT
```

The logical operation ID remains stable across attempts. The attempt ID is not a duplicate-suppression key because using it would give each retry a new external identity. `UNKNOWN` forbids replay until reconciliation. `RESIDUAL_EFFECT` blocks completion unless the mission has an explicit risk decision permitted for the affected quality item.

### 5.6 Quality and release

QA first records one of `PASS`, `FAIL`, or `INSUFFICIENT_EVIDENCE` for each must-pass acceptance criterion. It then evaluates the final release scope. The target release states are:

- `RELEASE`: every applicable must-pass acceptance criterion passes for the declared scope, and no blocker remains;
- `LIMITED_RELEASE`: every applicable must-pass acceptance criterion passes for a narrower, explicitly declared scope;
- `HOLD`: a required observation is insufficient, an external operation has an unknown outcome, a confirmed residual side effect exists, compensation is pending, or another resolvable required action remains;
- `DO_NOT_RELEASE`: a must-pass acceptance criterion has a confirmed failure, or the declared scope cannot be made acceptable.

`INSUFFICIENT_EVIDENCE` therefore produces `HOLD`, not approval. `LIMITED_RELEASE` cannot treat a known failure of a must-pass acceptance criterion as acceptable. It can exclude a configuration only when the accepted baseline permits a narrower scope and every must-pass acceptance criterion for that scope has valid evidence.

## 6. Central transition procedure

A worker can submit artifacts, execution results, findings, or a transition request. Only policy can change authoritative state.

For every request, policy checks:

1. issued identity and authority;
2. active mission revision and stage;
3. task and attempt status;
4. candidate identity, when required;
5. inputs and outputs required for the workflow phase;
6. valid evidence and no blocking findings;
7. receiver acceptance and quality decisions, when required.

Policy appends a decision event that advances or rejects the request, returns it to an affected stage, or holds it for more evidence.

Conceptually, every protected request follows this sequence:

```text
load issued authority grant
  → derive acting identity
  → compare mission, revision, stage, task, attempt, workspace, candidate, operation
  → load current authoritative state and required evidence set
  → validate inputs and outputs required for the workflow phase, files, paths, SHA-256, and producer identity
  → evaluate blockers, must-pass acceptance criteria, external-operation state, and receiver acceptance
  → append one decision event
  → derive the next state from accepted events
```

If any check fails, policy appends a rejection or hold with the specific reason and does not partially advance state. Lower-level objects may propose a transition, but they do not provide a second authoritative mutation path. A direct field assignment, caller-created role profile, or plugin convenience method cannot bypass this procedure.
