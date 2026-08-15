# Prior Work

> **This chapter explains:** which established methods inform the target architecture, where they apply, and which rules are specific to the harness.

Prior work appears after the operating model, worked mission, runtime, recovery, and trust chapters so that readers can evaluate design influence against a system they already understand. This is not a release history, a claim of direct historical lineage, or proof of conformance to any cited framework.

## 1. Authority and independent judgment

Protection principles support least privilege, complete mediation, and authority checks outside an untrusted worker.[35]

Formal inspection and independent software assurance support a stable review target, preparation before inspection, separation of correction from judgment, and documented follow-up.[33][16]

The harness applies those ideas to one-use authority grants, frozen candidates, read-only verification, and separate quality authority. The cited methods do not define this complete record and state model.

## 2. Requirements, evidence, and provenance

Systems engineering, verification and validation, and configuration baselines address the path from intended outcome through controlled configuration and observed results.[32]

Secure development life-cycle guidance addresses security work across the life cycle.[37][38]

Software supply-chain provenance addresses the identity of authorized transformations and artifacts.[39][40]

The target retains explicit links among accepted purpose, requirements, risks, design, configuration, observations, and release. It also distinguishes conformance to accepted requirements from fitness for intended use and creates new identities when decision-relevant inputs change.

The harness adds candidate-bound evidence validity, dependency-based `STALE` propagation, receiver acceptance, and a policy decision that joins these records without allowing one artifact or test result to imply completion.

## 3. Iterative feedback and risk

Risk-driven iteration and agile change responsiveness inform short feedback cycles, explicit risk review, and revision after accepted change.[34][36]

Test-driven development and continuous integration provide useful design references for executable feedback and shared integration.[43][41]

The accepted requirements and decision records do **not** make TDD or frequent mainline integration universal harness rules. The harness independently requires evidence to be bound to the active revision, attempt, and candidate, regardless of the development technique used.

## 4. Durable state and recovery

Event Sourcing supports recording state changes as an event sequence and using that history for reconstruction, temporal queries, and replay.[42]

Durable workflow systems demonstrate recovery from persisted progress and, in some cases, facilities for duplicate suppression or status lookup.[29][30][31]

The target architecture separately selects deterministic authoritative projection, a checked command-and-event boundary, duplicate handling, and explicit schema and projection versioning. It also adds stable external-operation identity, receipts, reconciliation before retry, mission-specific compensation, and a release hold when residual effects remain uncertain.

## 5. Harness-specific synthesis

No single reference model defines the following combination:

- a one-use authority grant bound to mission, revision, workflow phase, task, attempt, worker, workspace, allowed operations, candidate, expiry, and remaining uses;
- an immutable candidate that includes work products and decision-relevant inputs;
- evidence whose validity depends on the active revision, candidate, methods, tools, expected results, and decision rules;
- automatic invalidation after an accepted dependency change;
- receiver acceptance in addition to automatic handoff checks;
- independent criterion decisions followed by policy-derived completion and package eligibility;
- attempt-independent external-operation identity with receipt, reconciliation, and compensation handling.

These are the harness's target integration rules. Similarity to an earlier method does not by itself establish adoption, and adoption of one method does not imply adoption of the source's organizational process, terminology, or compliance claim.

## 6. Attribution boundaries

For every cited source, the detailed review distinguishes:

1. the problem and method directly described by the source;
2. whether the target adopts a rule or uses the source only as a design reference;
3. the change required for LLM-agent work;
4. elements intentionally not adopted;
5. the strength of the available attribution evidence.

The complete [Prior Work review](prior-work.md) contains the source-by-source analysis and references. Requirements and [architecture decision records](../adr/README.md), not the citation alone, establish which rules the target architecture adopts.

**Next:** [Reference and Next Reading](reference.md) provides the term, state, schema, code, test, and decision indexes.
