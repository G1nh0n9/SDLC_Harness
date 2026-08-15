# Trust Boundaries

> **This chapter explains:** which claims the harness can enforce, which require stronger external controls, and what uncertainty remains.

## 1. Protected assets

The target architecture protects these assets:

- active mission intent and revision identity;
- accepted requirements and quality baseline;
- task authority and worker identity;
- role-specific workspaces and tool permissions;
- frozen candidates and parent-child lineage;
- execution, handoff, finding, and release evidence;
- authoritative workflow state;
- external-operation IDs and reconciliation records;
- release material and its source candidate.

## 2. Inputs by trust level

| Input | Initial treatment | Required checks before authority or state change |
|---|---|---|
| User instruction | Authoritative intent, but not executable policy | Mission revision, scope, risk, and baseline acceptance |
| Model output | Untrusted proposal | Schema, issued identity, stage, task, artifact, and evidence checks |
| Web, file, and tool content | Untrusted data | Source identity, permitted use, path and content checks, and prompt-injection handling |
| Execution result | Observation, not approval | Runner provenance, command identity, exit status, artifact and candidate binding |
| Reviewer finding | Quality evidence with possible uncertainty | Reviewer authority, candidate identity, reproduction, impact, independence |
| External-service response | Observation of another system | Stable operation identity, authentication, consistency, and status reconciliation |

## 3. `export-ownership` trust path

The representative mission carries concrete material across the same boundaries described above:

| Material crossing the boundary | Initial risk | Required control before it affects state or release |
|---|---|---|
| User request and ownership definition | Ambiguous scope or instruction content that conflicts with policy | Create a mission revision, resolve acceptance-changing assumptions, and accept the baseline |
| Planner or Engineering model output | Invented authority, omitted perspective, unsafe command, or unsupported completion claim | Validate the issued authority, required workflow-phase material, allowed paths and tools, and captured execution |
| `C1` or `C2` bytes and manifest | Mutation, path escape, mismatched hash, or evidence for another candidate | Normalize paths, reject prohibited symbolic links, recalculate SHA-256, freeze the candidate, and verify lineage |
| Independent ownership fixture, observed export, and finding | Implementer-controlled expected result, correlated reviewer error, or incomplete method | Keep expected results and decision rules separate from implementation, use read-only QA authority, and record uncertainty |
| Object-storage request and response | Lost response, duplicate object, residual material, or unqueryable status | Use a stable logical operation ID, record receipts, reconcile before retry, and compensate or hold when needed |
| `QD2`, `ES2`, and package input | Stale evidence, missing criterion result, or package from different source | Recheck candidate and evidence-set identity, blockers, release scope, and package eligibility |

This table describes target controls. It does not assert that every boundary is already enforced by the current Python package.

## 4. Target harness enforcement

The target design enforces:

- authority bound to mission lineage, task, workspace, tools, candidate, and allowed operations;
- state changes accepted only through the Policy and State Engine;
- acting identity derived from an issued authority grant, not caller text;
- role- and task-specific write roots and approved executable identities;
- immutable candidates during verification and review;
- appended transition, decision, and invalidation events;
- evidence tied to checked artifact hashes and candidate identity;
- separation of implementation and final quality judgment;
- rejection of stale revision, cross-mission, cross-task, and cross-candidate reuse.

These are target-architecture claims, not statements that the current Python package implements every control.

## 5. Required operating-system controls

A Python package can enforce rules at its own entry points and within its workspaces. It cannot prevent another process under the same operating-system account from editing files directly, reading shared credentials, attaching to a process, or exploiting a race outside the observed execution boundary.

Higher-risk deployments require external controls such as:

- separate operating-system accounts;
- access-control lists;
- containers or virtual machines;
- read-only candidate mounts;
- restricted network access;
- separately administered credentials;
- process and filesystem monitoring;
- protected build and release environments.

The harness records its assumptions about external controls and claims that a control is present only when it was observed.

## 6. External services and side effects

The harness cannot guarantee exactly-once execution in another system.

For each external write, the harness can require:

- a stable logical operation ID;
- idempotency or duplicate suppression when the service supports it;
- a result receipt tied to the operation ID;
- status reconciliation before retry after an unknown outcome;
- a registered compensation when reversal is meaningful;
- an explicit residual state when compensation is impossible or incomplete.

If the external system cannot query or deduplicate the effect, the remaining uncertainty blocks completion unless an explicit risk decision permits it.

## 7. Model and reviewer limits

Role separation does not eliminate shared model bias. Multiple calls can share training data, reasoning errors, order effects, verbosity preferences, or self-preference.

The harness can reduce this risk through the following measures, but it cannot eliminate the risk:

- deterministic or domain-specific expected results and decision rules where available;
- independently controlled fixtures, expected results, and decision rules;
- separate review of each quality attribute;
- order reversal in pairwise comparisons;
- different model provenance where practical;
- explicit uncertainty and insufficient-evidence outcomes;
- human review or review by an external expert for high-impact residual questions.

Consensus is supporting evidence, not a substitute for execution or an expected result from an external source.

## 8. Scope-limited assurance

The harness may make a bounded claim that no forbidden effect occurred only when the observed scope is closed:

- source and dependency identities are fixed;
- entry points and allowed tools are enumerated;
- allowed and forbidden effects are declared;
- execution uses default-deny policy where practical;
- static checks and runtime observations cover the declared boundary;
- build and release lineage remain connected.

The claim does not extend to unobserved code, dependencies, processes, credentials, networks, or external services.

## 9. Residual uncertainty

Even the completed target leaves uncertainty about:

- semantic defects not covered by deterministic checks;
- correctness and availability of external systems;
- model bias shared by the producer and reviewers;
- unqueryable or irreversible external side effects;
- behavior outside the observed source, dependency, entry-point, and execution boundary;
- incorrect user intent or acceptance assumptions.

These residual risks remain explicit. Model assertions still do not constitute evidence, but observed results remain useful within their stated scope.

**Next:** [Prior Work](prior-work-overview.md) explains which established methods inform these boundaries and which integration rules belong to the harness.
