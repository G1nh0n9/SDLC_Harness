# Architecture Overview

> **This overview explains:** why the harness exists, how one mission moves through the system, and where to read next.

> **Scope:** This document describes the target operating model. It does not certify that the current Python package implements every control.

## 1. Purpose and scope

A language model can say that it wrote code, ran tests, reviewed a change, or completed a task. Those sentences do not prove that the work happened or that the result is fit for use.

Adding more agents does not solve the problem by itself. Agents can still share writable files, approve their own work, reuse results from an older revision, change an item under review, or agree while overlooking the same defect.

The harness therefore treats models as bounded workers and reviewers within a software process. It does not treat a role name, confidence, consensus, or fluent prose as authority.

Its narrow promise is:

> Given the same mission revision, approved inputs, quality baseline, and frozen candidate, changing the worker does not change the required evidence or the acceptance rules.

The harness is suitable when a mission needs reproducible artifacts, separation of responsibilities, reviewable quality decisions, or recovery after agent work is interrupted. It is not a substitute for operating-system isolation, a proof of total correctness, or an exactly-once guarantee for external services.

## 2. Architecture at a glance

The harness is a policy-controlled path from user intent to a release decision:

```text
request → accepted baseline → bounded authority → captured execution
        → frozen candidate → independent verification → quality decision → package
```

Three areas of responsibility define quality together, then remain separate while work is produced and evaluated:

- **Requirements and Outcomes** defines the intended result, scope, forbidden behavior, and what acceptance means.
- **Engineering and Software Delivery** designs and builds a candidate, then records what actually ran.
- **Verification and Quality Assurance** creates independent checks, examines the frozen candidate, and decides whether the observations support release.

The **Mission Manager** coordinates workflow phases and dependencies but does not implement work or approve quality. The **Policy and State Engine** derives acting identity from issued authority and is the only authority that may change authoritative workflow state.

A good plan is not a candidate. A working candidate is not an approval. An approval bound to another candidate is invalid.

Read [Architecture at a Glance](architecture/architecture-at-a-glance.md) for the system boundary and stable nine-step path. [Core Concepts and Operating Model](architecture/operating-model-overview.md) defines the terms and decision rights used below.

## 3. Representative mission

Use one scenario throughout the documentation:

> **Example `export-ownership`:** Add an authenticated data-export feature that returns only records owned by the requesting account.

1. Requirements defines ownership and prohibits cross-account access. Engineering identifies the authorization and storage boundaries. QA defines independent ownership fixtures, negative cases, and required observations.
2. Policy issues one-use authority for an Engineering task attempt. The runner captures commands, outputs, checked hashes, checkpoints, and external-operation records.
3. The Candidate Manager freezes `C1`. Automatic handoff checks and receiver acceptance both pass before independent QA begins.
4. QA finds that a secondary route bypasses the authenticated ownership filter. The security criterion fails, policy holds the mission, and `C1` remains unchanged.
5. Engineering creates child candidate `C2`. Evidence affected by the changed authorization path becomes `STALE`.
6. Handoff and independent QA run again. After every affected must-pass acceptance criterion passes, policy records `QD2=RELEASE`, makes `C2` `PACKAGE_ELIGIBLE`, and permits `PKG2` to be created from the exact `C2` and evidence set.

The [reader-oriented worked mission](architecture/worked-mission-overview.md) explains this path without record dumps. The [complete audit trace](architecture/worked-mission.md) preserves `event-0001` through `event-0035`, authority issue and consumption, candidate lineage, rejection cases, and exact state transitions.

## 4. Reading path

| Order | Document | Reader result |
|---|---|---|
| 1 | [Purpose and Scope](architecture/overview-and-scope.md) | Understand the problem, assurance target, applicability, and limits |
| 2 | [Architecture at a Glance](architecture/architecture-at-a-glance.md) | See the system boundary and normal mission path |
| 3 | [Core Concepts and Operating Model](architecture/operating-model-overview.md) | Learn the stable nouns, responsibility separation, and planning profile |
| 4 | [Worked Mission](architecture/worked-mission-overview.md) | Follow `export-ownership` from request through C1 hold, C2 correction, and package |
| 5 | [Runtime Architecture](architecture/runtime-overview.md) | Map the same steps to logical components and state checks |
| 6 | [Reliability and Recovery](architecture/reliability-overview.md) | Add interruption, duplicate delivery, uncertain external changes, compensation, and invalidation |
| 7 | [Trust Boundaries](architecture/trust-overview.md) | Separate target enforcement, external controls, and residual uncertainty |
| 8 | [Prior Work](architecture/prior-work-overview.md) | Understand adopted rules, design references, adaptations, and harness-specific synthesis |
| 9 | [Reference and Next Reading](architecture/reference-overview.md) | Find deep dives, normative material, a conclusion, and role-specific next reading |

The [HTML architecture guide](agent-harness-architecture.html) presents this sequence as one page. Detailed source documents remain separate so that audit material does not interrupt the newcomer path.

## 5. Architectural invariants

1. A caller-supplied role string is not identity.
2. Only policy changes authoritative state.
3. A candidate under review is not edited in place.
4. Changed inputs create a new revision or candidate and make affected evidence stale.
5. Completion comes from checked artifacts and evidence, not a completion message.
6. Implementation and final quality judgment remain separate.
7. Must-pass acceptance criteria must pass independently; strength in one area cannot offset failure in another.
8. Unknown external side effects are reconciled before replay.
9. Rework discovered after completion invalidates the earlier decision without erasing history.
10. Current and target capabilities are always labeled separately.

## 6. Next reading

| Reader | Next document |
|---|---|
| First-time reader | [HTML architecture guide](agent-harness-architecture.html), starting with Purpose and Scope |
| User or evaluator | [Worked Mission](architecture/worked-mission-overview.md), then [User Guide](user-guide.md) |
| Mission designer | [Core Concepts and Operating Model](architecture/operating-model-overview.md), then the [operating-model deep dive](architecture/operating-model.md) |
| Implementer | [Runtime Architecture](architecture/runtime-overview.md), then the [runtime state and transition deep dive](architecture/runtime.md) |
| QA or operator | [Reliability and recovery](architecture/reliability.md) |
| Security reviewer | [Trust boundaries](architecture/trust.md) |
| Decision reviewer | [Architecture decision records](adr/README.md) |
| Research reviewer | [Prior Work summary](architecture/prior-work-overview.md), then the [source-by-source review](architecture/prior-work.md) |
