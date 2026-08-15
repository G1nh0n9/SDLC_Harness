# Runtime Architecture

> **This chapter explains:** which logical components enforce the worked mission and how control records, work products, and evidence move through the system.

The components below are logical responsibilities, not a requirement to deploy separate services. The target can begin as one Python package and Hermes plugin surface, provided that lower-level calls cannot bypass the same policy checks.

## 1. Component collaboration

The **Mission Service** preserves the active instruction, creates revisions, routes late asynchronous results, and identifies records affected by steering. The **Goal and Quality Planner** decides whether the request is specific enough to plan, enumerates perspectives, assigns participation requirements, and defines required inputs, outputs, and observations.

The **Policy and State Engine** derives acting identity from an issued authority grant and rejects a mismatched mission, revision, task, attempt, workspace, tool, candidate, or operation. The **Workspace Broker** and **Task Runner** then restrict roots and executable identities, run approved work, and capture outputs, hashes, checkpoints, and external-operation records.

The **Candidate Manager** normalizes paths, rejects prohibited symbolic links, calculates the manifest identity, records lineage, and freezes the review target. The **Handoff Verifier** performs automatic structure and identity checks before the receiving expert records receiver acceptance. Authorized QA reruns required methods through the **Task Runner**, and the **Quality and Release Decision** responsibility evaluates each criterion, uncertainty, blocker, and supported release scope. Policy permits packaging only from the approved candidate and evidence set.

## 2. Control and data flow

Workers submit artifacts, observations, findings, or transition requests. They never write authoritative state directly.

Every protected request follows the same sequence:

```text
load issued authority grant
  → derive acting identity
  → compare mission, revision, workflow phase, task, attempt, workspace, candidate, and operation
  → load authoritative state and the required evidence set
  → validate required inputs, outputs, paths, files, SHA-256 values, and producer identity
  → evaluate blockers, criterion results, external-operation state, and receiver acceptance
  → append one accepted, rejected, returned, or held decision
  → derive the next state from accepted events
```

This boundary separates **control flow** from **data flow**. Control flow authorizes work and accepts or rejects state changes. Data flow carries source, manifests, fixtures, execution output, findings, receipts, and packages. A component may handle both types internally, but it must not treat receipt of data as permission to advance.

## 3. Durable record groups

Mission and state records answer what changed, under which authority, and why. Plan and quality records state what had to be true. Candidate and lineage records identify the exact material under judgment. Evidence and release records connect commands, outputs, observations, findings, handoff decisions, criterion results, package identity, and supported scope.

These records may share a data store. Their validation rules and decision meanings remain separate, so the existence of an execution record cannot imply a quality decision and a quality decision cannot imply that package bytes exist.

## 4. State ownership and invalidation

Mission intent, tasks, attempts, candidates, evidence, external side effects, and release decisions change for different reasons. The architecture therefore does not compress the entire mission into one status string.

- A retry creates a new attempt while preserving the logical task and earlier attempt history.
- Candidate correction creates a child candidate; it does not edit the frozen parent.
- Evidence becomes `INVALID` when it never passed its checks and `STALE` when a later accepted change removes its applicability.
- `QUALITY_DECIDED` means that criterion results and release scope were accepted; it does not mean that a package exists.
- `PACKAGE_ELIGIBLE` permits a package task but does not itself create package bytes.
- A later valid finding can append a completion invalidation and reopen the earliest affected workflow phase without erasing the earlier release decision.

## 5. External operations

An external operation is a stable logical request that can span several attempts. An external side effect is the actual change in the external system. The operation identity remains stable across retries; the attempt identity remains in the execution history.

If a response is lost after a possible write, policy records an unknown outcome and forbids replay until reconciliation. A confirmed partial side effect can require mission-specific compensation. An unqueryable or uncompensated residual effect remains a blocker unless the accepted baseline permits a narrower, explicit risk decision.

**Next:** [Reliability and Recovery](reliability-overview.md) applies interruptions, duplicate delivery, uncertain external changes, and invalidation to the same mission steps. The [runtime deep dive](runtime.md) contains the complete state models and transition procedure.
