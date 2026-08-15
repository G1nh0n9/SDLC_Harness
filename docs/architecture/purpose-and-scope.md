# Purpose, Problem, and Scope

> **This chapter explains:** why LLM agents need a software development harness, which failures it prevents, and the limits of its assurance claims.

## 1. Problem statement

LLM agents can quickly produce source code, tests, reviews, plans, and explanations. The difficult question is whether a later decision can distinguish work that was actually performed from a plausible claim that the work was performed.

Consider five ordinary failures:

1. An implementation agent returns “all tests pass,” but no approved runner captured the command, environment, exit status, or test artifacts.
2. A reviewer approves a directory while the implementer continues to change files in that same directory.
3. A result from an older mission revision arrives late and is attached to the current revision because its prose still sounds relevant.
4. An agent calls itself `qa`, approves its own output, and the surrounding application treats the role field as identity.
5. A storage write succeeds, its response is lost, and an automatic retry creates a duplicate effect.

Adding more role prompts does not fix any of these problems. Ten agents can still share writable state, repeat the same error, approve their own work, or agree on an unsupported claim. A chat transcript also cannot prevent a lower-level caller from changing state directly.

The harness therefore treats model output as an untrusted proposal or observation. Models may analyze, implement, inspect, and recommend. Deterministic code establishes the acting identity, validates authority, checks files and SHA-256 values, verifies candidate and revision binding, records state decisions, and refuses prohibited transitions.

## 2. Release decision criteria

For each mission, the harness must ultimately answer a bounded question:

> Does the evidence for this exact mission revision and frozen candidate—the work product and decision-relevant inputs bound to one immutable identity—satisfy every must-pass acceptance criterion and support the declared release scope?

Answering that question requires more than a test result. The decision depends on:

- what the user intended and which assumptions were accepted;
- which acceptance criteria had to pass and how each would be observed;
- who was allowed to produce, inspect, or decide each item;
- which source, tests, dependencies, build settings, and toolchain went into the candidate;
- what commands and inspections actually ran;
- whether every result belongs to the active revision and unchanged candidate;
- whether any blocking finding, external operation with an unknown outcome, confirmed residual side effect, or invalidation remains.

A build can succeed even when the feature is wrong for the intended use. A reviewer can make a sound finding without making a release decision. A package can match its source even when the source has not been approved. The architecture keeps these facts separate, then joins them explicitly when policy makes a decision.

## 3. Assurance scope

The target architecture makes one principal assurance claim:

> Given the same active mission revision, accepted inputs, quality baseline, issued authority grant, and frozen candidate, changing the worker does not change the evidence or decision rules required to advance.

This is a process and provenance property. It does not prove total correctness. It means that a more persuasive worker cannot weaken a must-pass acceptance criterion, replace a missing artifact with prose, reuse evidence from another candidate, or give itself broader permissions or decision authority.

The claim has observable failure conditions. It is false if the harness accepts any of the following:

- an unissued or caller-supplied identity performs a protected operation;
- a state transition bypasses central policy;
- a reviewed candidate changes without a new identity;
- a required workflow-phase input or output is missing, but the workflow advances;
- submitted SHA-256 values are accepted without recalculation;
- evidence from another revision, task, attempt, mission, or candidate advances the active one;
- implementation and final quality approval are performed under the same authority when separation is required;
- an external operation with an unknown outcome is replayed before reconciliation;
- a later valid finding leaves the earlier completion decision active.

These conditions become fault-injection tests. Architecture tests measure whether the harness rejects these prohibited actions, not how many agents, documents, checks, or comments it produces.

## 4. Protected decisions and artifacts

The harness protects the identity and permitted use of:

| Protected item | Why it matters |
|---|---|
| Active user instruction and mission revision | A late or superseded instruction must not control current work |
| Mission and quality baseline | The implementer must not silently change purpose, forbidden behavior, or acceptance methods |
| Perspective and expert plan | Required expertise and independence must not disappear when work is assigned |
| Task authority | Caller text must not create identity, write permission, execution permission, or approval power |
| Role-specific workspace and execution | Work must stay within allowed paths, tools, and environment |
| Independently controlled expected results and decision rules | The implementation worker must not define or change the expected values or decision rules used to evaluate its work |
| Frozen candidate version and parent-child lineage | Review and test results need one unchanged target |
| Artifact and execution evidence | Completion needs checked bytes and observed actions, not self-report |
| Handoff acceptance | Valid files must also be usable by the receiving area of responsibility |
| Quality and release decision | Must-pass acceptance criteria, uncertainty, residual risk, and supported scope must be explicit |
| Checkpoint and external-operation state | Recovery must not duplicate accepted work or external side effects whose outcomes remain unknown |
| Completion invalidation | Later rework must withdraw the earlier decision without erasing history |

## 5. Applicable mission types

The harness is appropriate when one or more of these conditions apply:

- the output will be submitted, released, published, or used as evidence;
- implementation and final judgment must be independent;
- security, privacy, data integrity, correctness, safety, or research validity includes a criterion that must pass independently;
- work spans several agents, restarts, or external waits;
- stale results and concurrent work could be confused;
- the exact source-to-package lineage matters;
- the user needs to inspect why a release was accepted, limited, held, or later invalidated.

A low-risk local edit can use a scaled-down process: one explicit mission revision, one implementation authority, one immutable review target, one fresh check, and one recorded decision. Risk changes the required depth and independence; it does not remove identity and evidence binding.

## 6. Non-goals

The target harness does not claim:

- complete operating-system isolation when all processes share one account;
- correctness of unobserved dependencies or external services;
- exactly-once execution by another system;
- independence based solely on different role names in prompts;
- formal proof of every semantic property;
- compliance with NASA, NIST, Microsoft SDL, in-toto, SLSA, or any other framework without a separately defined profile and complete evidence;
- that passing tests prove usefulness in every intended environment;
- that LLM consensus replaces deterministic checks, domain-specific expected results and decision rules, or human risk acceptance.

High-risk deployment adds controls outside the Python package: separate operating-system accounts, read-only mounts, restricted credentials and network access, protected build environments, and independently administered release authority. This document identifies those requirements without presenting them as implemented.

## 7. Architectural approach

The target structure addresses the preceding failures with seven linked mechanisms:

1. **Three areas of responsibility** jointly define quality and remain separate where interests conflict.
2. **List perspectives before assigning experts:** Required knowledge and independence determine the number of experts; the harness does not begin with a fixed number.
3. **One-use authority grants and central policy:** The Policy and State Engine derives acting identity from a one-use authority grant and permits only operations included in that grant.
4. **Role-specific execution boundaries** restrict paths, tools, executables, and recorded effects.
5. **Immutable candidates and checked manifests** bind review to exact bytes and lineage.
6. **Evidence and quality decisions tied to the candidate** derive completion from required observations.
7. **Durable events, checkpoints, reconciliation, and invalidation** preserve meaning across interruption, retry, external uncertainty, and later rework.

The architecture guide next presents the system boundary, operating model, worked mission, runtime responsibilities, recovery behavior, trust boundaries, prior work, and role-specific reference paths for those mechanisms.
