# Architecture at a Glance

> **This chapter explains:** the system boundary, the normal mission path, and the few records that make later decisions reviewable.

The harness is a policy-controlled path from user intent to a release decision. Models and tools may propose work, produce artifacts, run checks, and report observations. They do not assign their own authority or change authoritative workflow state.

## 1. System boundary

Figure 1 at the start of this guide shows logical responsibilities, not a required deployment topology. The Policy and State Engine is the single transition boundary. Control, execution, and assurance responsibilities append durable records that policy checks before accepting a transition.

Three rules make the picture useful:

- **Control is distinct from work.** The Mission Service and Goal and Quality Planner prepare requests and plans; policy decides whether they may advance.
- **Execution is distinct from judgment.** The Workspace Broker and Task Runner produce captured work; Candidate, Handoff, Quality, and Release responsibilities determine what can be judged and released.
- **Records are distinct from assertions.** A worker response can point to a record, but it cannot replace the record or set its validity.

## 2. One mission path

The documentation uses one scenario throughout:

> **`export-ownership`:** Add an authenticated data-export feature that returns only records owned by the requesting account.

The normal path has nine stable steps. Later chapters add runtime components and failure handling to these same steps instead of introducing another example.

1. Record the request and create an active mission revision.
2. Accept the outcome, forbidden behavior, acceptance criteria, and required observations as the mission and quality baseline.
3. Enumerate required perspectives and assign compatible work without combining conflicting authority.
4. Issue a one-use authority grant for one task attempt, identity, workspace, and set of operations.
5. Run approved work and capture outputs, hashes, checkpoints, and external-operation records.
6. Bind every decision-relevant input to an immutable candidate with parent-child lineage.
7. Check the structured handoff and obtain receiver acceptance.
8. Rerun required checks against the frozen candidate and record criterion results.
9. Decide supported release scope and, when permitted, package only the approved candidate.

A failed must-pass acceptance criterion does not edit the reviewed candidate. Policy holds the mission, Engineering creates a child candidate, affected evidence becomes `STALE`, and QA makes a new decision from fresh affected observations.

## 3. Authoritative records

Four record groups prevent one successful action from implying that the entire mission is complete. The mission and quality baseline establish what must be true, not that implementation exists. Authority, task, attempt, and execution records establish who could act and what the runner observed, not fitness for release. Candidate, manifest, handoff, and evidence records establish the exact material and observations under judgment, not that every criterion passed. Quality, package, and release records establish the supported scope and residual risk, not correctness outside the declared and observed boundary.

## 4. Failure containment

The same structure answers the five failures from the opening chapter:

- captured execution replaces unsupported completion claims;
- a frozen candidate prevents in-place changes during review;
- revision and candidate bindings reject stale results;
- an issued authority grant replaces caller-supplied role identity;
- stable external-operation identity and reconciliation prevent automatic replay after an unknown outcome.

These mechanisms do not make models or external systems trustworthy. They make the evidence and decision boundary explicit enough to reject unsupported progress.

**Next:** [Core Concepts and Operating Model](operating-model-overview.md) defines the nouns and decision rights used by the worked mission. For deployment-neutral component and state details, use the [runtime deep dive](runtime.md).
