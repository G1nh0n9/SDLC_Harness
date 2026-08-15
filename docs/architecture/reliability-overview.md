# Reliability and Recovery

> **This chapter explains:** what the harness persists, what it retries, and when it stops for reconciliation or fresh evidence.

The reliability model follows the same `export-ownership` mission and the same Policy and State Engine, Task Runner, Candidate Manager, Handoff Verifier, and Quality and Release Decision responsibilities introduced earlier. It does not promise one universal form of exactly-once execution.

## 1. Scoped guarantees

| Scope | Persisted boundary | Recovery rule |
|---|---|---|
| Policy decision | Accepted event identity and derived state | Redelivery of the same accepted event does not repeat the transition. |
| Task progress | Verified checkpoint and artifact hashes | A new attempt resumes only from verified durable progress. |
| Candidate review | Frozen manifest and parent-child lineage | Changed input creates a child candidate and makes affected evidence `STALE`. |
| External operation | Stable operation ID, receipt, and reconciliation status | An unknown outcome blocks replay until the external state is known. |
| Release | Criterion decisions, evidence-set identity, and package binding | Only the active candidate with complete valid evidence can support release. |

The cost is more explicit state and more recovery records than a simple retry loop. The benefit is that a retry, completed process, or successful command cannot silently stand in for mission completion.

## 2. Normal completion

For candidate `C2`, completion remains a sequence of accepted facts: the Task Runner captures the approved execution; the Candidate Manager freezes the exact inputs; the Handoff Verifier checks the transfer and records receiver acceptance; authorized QA records observations for every must-pass acceptance criterion; the Quality and Release Decision responsibility records supported scope and residual risk; and policy derives `QUALITY_DECIDED` and then `PACKAGE_ELIGIBLE`.

A model response ending, an attempt exiting with status zero, or a file appearing in a workspace establishes only one part of that chain. Policy rejects completion when authority, required artifacts, actual SHA-256 values, candidate identity, receiver acceptance, criterion results, or external-operation status is missing or inconsistent.

## 3. Interruption and retry

A planned stop records a checkpoint only after the declared operation boundary and referenced artifacts have been verified. An unexpected termination records the attempt as interrupted; unverified partial output remains diagnostic and cannot become a checkpoint automatically.

Retry creates a new attempt under a fresh authority grant. It does not overwrite the prior attempt or reuse the prior attempt's one-use authority grant. The Policy and State Engine checks the logical task, retry budget, candidate, checkpoint, and external-operation state before allowing the Task Runner to resume.

The alternative—resuming from whichever files happen to remain in a workspace—is simpler but cannot establish whether the files are complete, durable, or produced under the active revision. The target therefore pays the checkpoint-verification cost only at declared safe boundaries.

## 4. Rework and invalidation

In `export-ownership`, QA's secondary-download-route test shows that a caller-supplied account ID bypasses the authenticated ownership filter. The harness does not modify `C1` during review. It records the failed criterion, holds release, opens Engineering correction work, and creates child candidate `C2`. Evidence that depends on changed source or tests becomes `STALE`; unaffected evidence remains historical but must still match the active candidate's declared dependency set.

If a valid finding arrives after an earlier completion decision, policy appends a completion-invalidation event and reopens the earliest affected workflow phase. It does not erase the old decision or pretend that the later observation was known earlier.

This immutable lineage costs storage and requires explicit dependency declarations. It preserves what was actually reviewed and prevents a corrected file tree from inheriting approval for different bytes.

## 5. External side effects

An external operation is the logical request; an external side effect is the change that another system actually made. If the Task Runner loses the response to an object-storage write, policy marks the outcome unknown. It forbids blind replay until a status query, duplicate-suppression key, or receipt establishes the external state.

A confirmed partial effect may require compensation. If the service cannot report status, suppress duplicates, or reverse the change, the unresolved effect remains a release blocker unless the accepted baseline explicitly permits a narrower scope and records the residual risk. The harness does not extend its event deduplication into an exactly-once claim about another system.

## 6. Failure ownership

The recovery destination depends on the failed obligation:

- missing or malformed work returns to the producing task;
- invalid handoff structure returns to the producer, while receiver rejection returns with the stated usability reason;
- failed verification returns to Engineering through a child candidate;
- verifier disagreement produces `INCONCLUSIVE` or escalation rather than an averaged pass;
- unknown external outcome returns to reconciliation, not execution;
- stale evidence returns to the earliest workflow phase that can produce fresh evidence.

Recovery never weakens a must-pass acceptance criterion. It changes the attempt, candidate, or workflow phase needed to satisfy the same accepted baseline.

The [reliability deep dive](reliability.md) defines checkpoint contents, duplicate-delivery handling, compensation, semantic-review disagreement, and the complete failure matrix.

**Next:** [Trust Boundaries](trust-overview.md) separates the controls the target harness enforces from controls that require the operating environment or an external service.
