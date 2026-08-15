# Purpose and Scope

> **Audience:** Software and systems engineers, mission designers, reviewers, and operators who need to understand the target architecture before reading schemas or implementation code.

An LLM agent can say that it wrote code, ran tests, reviewed a change, or completed a task. Those statements do not establish what ran, which files were examined, whether the reviewed material changed, or whether the result is acceptable for its intended use.

The harness addresses that gap. It treats model output as an untrusted proposal or observation and places authority, state changes, artifact identity, and release decisions behind deterministic checks.

## 1. Ordinary failure modes

Five ordinary failures define the problem:

1. A worker reports that tests passed without captured execution evidence.
2. A reviewer examines files while the producer continues to edit them.
3. A late result from an older revision is attached to the current mission.
4. A caller labels itself `qa` and approves its own output.
5. An external write may have succeeded, but a lost response causes a retry to repeat the side effect.

Another model can repeat a claim or role name. It cannot reconstruct missing observations, freeze a shared directory, derive acting identity from an issued authority grant, or reveal an external system's state.

## 2. Assurance target

For each mission, policy must answer one bounded question:

> Does the evidence for this exact mission revision and frozen candidate satisfy every must-pass acceptance criterion and support the declared release scope?

Policy keeps the accepted baseline, issued authority grant, frozen candidate, observations, and release decision distinct until all required bindings and criterion results pass. Given those same inputs, changing the worker does not change the evidence or decision rules required to advance.

## 3. Applicable use

The harness is appropriate when work will be released, published, submitted as evidence, resumed after interruption, or reviewed under separation-of-responsibility requirements. A low-risk change may use fewer experts and observations, but it still needs an explicit revision, bounded authority, an unchanged review target, fresh evidence, and a recorded decision.

## 4. Limits

This guide defines a target operating model; it does not certify the current Python implementation. The target does not claim total correctness, complete operating-system isolation, exactly-once behavior in another system, independence created only by different prompts, or conformance to a cited standard. Higher-risk deployments require external operating-system, credential, network, build, and release controls.

**Next:** [Architecture at a Glance](architecture-at-a-glance.md) gives the smallest useful picture of the system. The detailed [purpose and assurance scope](purpose-and-scope.md) preserves the protected items, observable failure conditions, mission types, and complete non-goals.
