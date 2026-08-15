# Trust Boundaries

> **This chapter explains:** what the target harness treats as untrusted, what it can enforce, and where stronger external controls remain necessary.

The trust model uses the same `export-ownership` path as the normal and failure narratives. A user request, planner output, source tree, fixture, execution result, reviewer finding, object-storage response, and package input cross different boundaries; none becomes authority merely because it is well formed or produced by a model.

## 1. Protected path

The accepted mission revision and quality baseline enter the Policy and State Engine as control records. Planner and Engineering output enters as untrusted proposed work. The engine resolves an issued authority grant, while the Workspace Broker and Task Runner restrict and observe the permitted operation. The Candidate Manager binds the resulting material to `C1` or `C2`. The Handoff Verifier and authorized QA attach candidate-bound observations. Finally, the Quality and Release Decision responsibility can support only the scope justified by those records.

This path protects mission intent, authority, workspaces, candidate lineage, expected results and decision rules, observations, external-operation state, and the source candidate for the package. The detailed [trust-boundary reference](trust.md) lists every protected asset and input class.

## 2. Target enforcement

Within its policy and runner boundary, the target harness enforces these rules:

- acting identity comes from an issued authority grant, not a caller-supplied role string;
- the grant is bound to mission, revision, workflow phase, task, attempt, worker, workspace, candidate when applicable, allowed operations and tools, expiry, and remaining uses;
- only the Policy and State Engine accepts authoritative state transitions;
- the Workspace Broker rejects paths outside approved roots and prohibited symbolic links;
- the Task Runner captures executable identity, arguments, bounded environment, exit status, outputs, and actual artifact hashes;
- the Candidate Manager freezes decision-relevant material and preserves parent-child lineage;
- verification and release records must match the active revision and candidate;
- Engineering cannot supply its own final QA decision or silently replace independently controlled expected results or decision rules.

Central mediation is less flexible than allowing each component to update its own status. That restriction is deliberate: a lower-level API and the Hermes plugin must reach the same decision from the same stored authority and evidence.

## 3. Operating-environment controls

A Python package cannot prevent another process under the same operating-system identity from editing files directly, reading shared credentials, attaching to a process, or exploiting an unobserved race. Higher-risk deployments therefore need separately administered controls such as operating-system identities, access-control lists, containers or virtual machines, read-only candidate mounts, restricted credentials and networks, process monitoring, and protected build and release environments.

The harness records which external controls it assumes and claims their presence only when the deployment has observed them. Prompt instructions, separate model calls, and different role labels are not security boundaries.

## 4. External systems

The harness can require a stable logical operation ID, authenticated status query, receipt, duplicate suppression, reconciliation before retry, and compensation when reversal is meaningful. It cannot guarantee exactly-once execution inside object storage, an issue tracker, a deployment service, or any other external system.

For `export-ownership`, a lost object-storage response therefore leaves the external operation's outcome unknown. Blind retry is prohibited. If the service cannot reveal the outcome, the operation remains unresolved; if it confirms a side effect that it cannot reverse, that residual side effect remains explicit. Either condition blocks release unless the accepted baseline permits a narrower decision.

## 5. Model and reviewer limits

Independent authority reduces self-approval but does not eliminate shared model bias. Producer and reviewer calls may share training data, systematic reasoning errors, or presentation preferences. The target uses deterministic expected results and decision rules where possible, independently controlled fixtures, separate quality-attribute decisions, order reversal for pairwise comparisons, different model provenance where practical, and explicit `INCONCLUSIVE` outcomes.

Consensus is supporting evidence. It does not replace execution, independently controlled expected results and decision rules, or a human decision for high-impact residual uncertainty.

## 6. Bounded claims

A statement that no forbidden effect occurred is limited to fixed source and dependency identities, enumerated entry points and tools, declared allowed and forbidden effects, the observed execution boundary, and connected build and release lineage. It does not extend to unobserved code, processes, credentials, networks, dependencies, or external services.

The target also does not claim total correctness, complete operating-system isolation, or conformance to a cited standard without a separate profile and complete evidence. Its contribution is narrower: unsupported progress can be rejected, changes invalidate dependent evidence, and release scope stays tied to what was actually observed.

**Next:** [Prior Work](prior-work-overview.md) explains which established methods inform these boundaries and which integration rules are specific to the harness.
