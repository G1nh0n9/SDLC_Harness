# Prior Work

> **This chapter explains:** what the cited prior work directly supports, which principles the target architecture adopts, what the harness changes or adds for LLM-agent software development, and which elements it does not adopt.

## 1. Scope, evidence, and attribution

This chapter describes prior work relevant to the architecture. It is not a history of harness releases, proof that every cited source directly caused a design decision, or a claim that the harness originated the cited methods.

Three different relationships must remain separate:

| Relationship | Required evidence | What this chapter may claim |
|---|---|---|
| **Documented historical method** | An original publication, official standard, official handbook, or organization-maintained description | The method addressed the stated problem and used the cited practices |
| **Adopted design rule** | An accepted harness requirement or decision record that names the retained rule | The target architecture deliberately applies that rule |
| **Direct historical influence** | A dated design record showing that the source was consulted before or during the decision | The source influenced that decision at that time |

The repository currently supports the first relationship for the cited sources and the second for rules recorded in requirements and decision records. It does not consistently preserve dated evidence for the third. The defensible terms are therefore **prior work**, **adopted design rule**, and **design similarity**, not direct descent.

Each entry uses the same five-part structure:

| Subsection | Meaning |
|---|---|
| **Original problem** | The problem and method that the cited source directly supports. |
| **Retained method** or **Design reference** | A retained method is selected by an accepted harness requirement or decision record. A design reference is relevant prior work but is not presented as an adopted rule. Neither classification claims conformance with the source. |
| **Adaptation for LLM agents** | A change, extension, or generalization made for this harness. The cited prior work does not directly establish these additions unless the text says otherwise. |
| **Deliberate exclusions** | Source practices, guarantees, organizational structures, or conformance claims that the harness does not adopt. |
| **Relationship classification** | The evidence available for attribution and the permitted strength of the claim. |

Unless an entry explicitly describes observed repository behavior, statements about what “the target” does are target-architecture decisions, not current implementation claims.

The models operate at different levels. Protection principles govern authority, while inspection focuses on defect discovery and follow-up. Systems engineering and verification/validation connect intended outcomes to observations, and risk-driven iteration allocates effort under uncertainty. TDD and continuous integration provide references for short feedback cycles. Configuration management preserves baseline identity; Event Sourcing provides a replay-oriented reference for state history; secure development adds lifecycle security practices; and supply-chain provenance binds transformations to artifacts. Durable workflow systems preserve progress and support recovery. The harness separately defines how to reconcile uncertain external operations and compensate for confirmed external side effects. Software assurance and independent verification organize objective evidence and separate responsibilities. No single model supplies the whole harness.

## 2. Protection principles and capability-like authority

### Original problem

Saltzer and Schroeder addressed how a computer system should protect information when many users, programs, resources, and mechanisms interact. Their principles include least privilege, complete mediation, separation of privilege, economy of mechanism, and avoiding protection decisions based on obscurity.[35]

The historical problem was not “how to make an agent follow a prompt.” It was how to ensure that a subject could perform only the permitted operations on protected objects, even when software was fallible or hostile.

### Retained method

The target retains narrow authority and complete mediation. Every protected operation—state transition, command execution, candidate write, evidence submission, approval, and packaging—must be checked against authority issued by the harness. The check must use stored identity and scope, not a role name supplied by the caller.

Separation of privilege appears as distinct authority for production, review, quality decision, and packaging. A successful engineering task does not implicitly grant approval authority.

### Adaptation for LLM agents

An LLM message can claim any role, invent a tool result, or request an operation outside its assigned work. The target therefore binds each one-use authority grant to a mission, revision, stage, task, attempt, issued worker identity, role, workspace, candidate, allowed operations, tool set, expiry, and remaining uses. Role prose is descriptive; the authority-grant record is decisive.

Because one model process may serve several logical roles, independence cannot be inferred from model identity alone. The harness separates authority, workspace, artifacts, methods, and decision rights even when infrastructure is shared.

### Deliberate exclusions

The harness does not implement an operating-system reference monitor, a formally verified security kernel, multilevel security, or complete noninterference. OS accounts, ACLs, containers, credential brokers, network policy, and sandboxes remain external controls. The architecture claims only the operations it can actually mediate.

### Relationship classification

The target adopts least privilege, complete mediation, and separation based on a documented design analogy. The repository does not establish direct historical descent from the 1975 paper.

## 3. Fagan formal inspection

### Original problem

Fagan’s 1976 inspection method addressed expensive design and code defects that escaped informal review and surfaced late in testing or operation. It defined a managed process rather than an unstructured conversation: planning, an overview when needed, individual preparation, an inspection meeting focused on defect detection, rework by the author, and follow-up to confirm that defects were addressed. Roles, entry criteria, review rate, defect classification, and measured results made the process observable.[33]

The method distinguished **finding defects** from **correcting them**. A meeting did not silently edit the item under inspection, and follow-up was required after rework.

### Retained method

The target retains preparation guided by explicit criteria, role separation, an unchanged review object, reproducible findings, correction outside the review, and follow-up on the corrected child candidate. Findings record the inspected candidate identity, location, quality item, observation, severity, evidence, and required disposition.

A candidate under review is therefore immutable. If Engineering changes it, the object under inspection no longer exists at the old digest. The correction becomes a child candidate, and affected findings and checks are reevaluated.

### Adaptation for LLM agents

An LLM reviewer may summarize rather than inspect, favor persuasive prose, or allow the authoring context to bias judgment. The harness replaces informal preparation with a checked work order, candidate manifest, itemized quality criteria, independent execution where possible, and explicit receiver acceptance.

Receiver acceptance is a harness extension, not a claim that Fagan inspection prescribed the same mechanism. It addresses the additional risk that syntactically valid machine-generated material may still be unusable by the next expert.

### Deliberate exclusions

The complete Fagan meeting format, historical role names, fixed inspection rates, and original metrics program are not required for every mission. Meeting attendance, signatures, consensus, and defect counts are not treated as proof of correctness. The retained core is immutable inspection input, prepared defect detection, separate rework, and verified follow-up.

### Relationship classification

The cited paper supports the historical method. Candidate immutability and receiver acceptance are decisions in the target architecture that use analogous separation logic; they are not claims of causal influence or exact Fagan conformance.

## 4. Systems engineering

### Original problem

Systems engineering addresses failures caused by optimizing components without preserving the intended system outcome, operational context, interfaces, risks, and life-cycle constraints. The NASA handbook connects stakeholder expectations, technical requirements, logical and physical design, implementation, integration, verification, validation, transition, technical planning, risk, configuration, data, and technical assessment.[32]

The model is recursive and iterative across levels; it is not accurately described as one irreversible sequence.

### Retained method

The target retains an explicit path from the intended outcome through the requirement baseline, stage plan, quality profile, candidate, verification result, validation judgment, and release decision. Each relationship uses stable identifiers so that a result for one requirement revision or candidate cannot silently satisfy another.

The Mission Manager maintains the mission-wide context: whether the request is specific enough to plan and verify, dependency order, risk, assignment of the required expertise, required evidence, unresolved decisions, and release blockers. It does not replace the expert responsible for the underlying judgment.

### Adaptation for LLM agents

LLM work distributes context across calls and can rewrite assumptions without recognizing that the accepted baseline has changed. The target therefore stores the baseline, shared concepts, decisions, input digests, and impact rules outside model context. A changed acceptance condition creates a new mission revision; a candidate correction creates a child candidate.

Three areas of responsibility adapt the systems view to agent work. The Requirements and Outcomes area protects the intended result, the Engineering and Software Delivery area creates the solution, and the Verification and Quality Assurance area independently judges observed quality. They collaborate during baselining, readiness assessment, and candidate review without combining their final authority.

### Deliberate exclusions

The harness neither implements every NASA process, role, document, review gate, or technical authority nor claims NASA process compliance. Instead of imposing a single large lifecycle, it selects workflow phases and participation profiles according to mission risk and evidence needs.

### Relationship classification

NASA systems engineering is a documented reference for outcome traceability, technical processes, configuration, and recursive life-cycle thinking. The target adopts those principles selectively.

## 5. Verification and validation

### Original problem

Verification and validation answer different failure questions. Verification asks whether specified requirements and design rules were implemented correctly. Validation asks whether the resulting system satisfies intended use in the relevant operational environment. A product can conform to its written specification yet still solve the wrong problem or fail in real use.[32]

Combining the two into “testing” loses the distinction between conformance and fitness for purpose.

### Retained method

The target requires both. Verification binds deterministic checks, requirement-based tests, static analysis, artifact inspection, and reproducible execution to one frozen candidate. Validation binds scenario evidence, stakeholder intent, operational assumptions, usability, and release scope to the active mission revision.

The trace is explicit:

```text
stakeholder outcome
  → accepted requirement and quality item
  → verification or validation method
  → expected result or decision rule
  → observation tied to the candidate
  → finding for one quality item
  → release decision
```

### Adaptation for LLM agents

The expected result and implementation must not be controlled by the same authority when self-confirmation would invalidate the check. Model and tool nondeterminism are recorded with the environment, version, prompt or configuration digest, random seed where applicable, repetition policy, raw observation, and uncertainty. The Requirements and Outcomes area and relevant domain or operational experts define the intended environment; the implementer cannot infer it alone.

Verification produces observations; QA decides whether those observations satisfy a must-pass acceptance criterion. Validation may require a human or domain authority when accepted risk or intended use cannot be derived mechanically.

### Deliberate exclusions

The target does not classify every model review as independent V&V. Different role prompts on the same model do not establish independence. Neither a passing test suite nor user satisfaction alone provides complete validation or proves requirement conformance.

### Relationship classification

The target directly adopts the distinction between verification and validation. Its three areas of responsibility are specific to this harness.

## 6. Risk-driven iterative development

### Original problem

Boehm’s spiral model addressed projects where committing to a complete design or build before resolving major uncertainty created costly failure. Each cycle identifies objectives, alternatives, and constraints; evaluates and reduces risk; develops and verifies the next-level product; obtains stakeholder evaluation; and plans the next cycle.[34]

Risk is therefore a control variable for what to learn and build next, not merely a severity label attached after planning.

### Retained method

The target generates mandatory perspectives before selecting experts. It records a P0–P3 base level of involvement for each perspective, then separately records whether P4 independent assessment or P5 bounded investigation is required. High-risk unknowns can become research, a prototype, a threat model, a task that creates an independently controlled expected result, or a bounded experiment before broad implementation.

A stage plan records the risk or uncertainty retired by each task, the evidence required to retire it, and the stop or escalation condition. This structure prevents a large implementation from hiding an unresolved foundational question.

### Adaptation for LLM agents

Agents can cheaply produce many plausible alternatives, which makes unbounded exploration especially wasteful. Every research task therefore has an owner, a resource limit, a stop condition, a required output, and a decision that will consume the result. Research that exceeds the agreed resource threshold requires a new plan before it continues.

### Deliberate exclusions

The harness does not require a spiral project diagram or a fixed four-quadrant lifecycle, nor does it imply that the original method advocated endless iteration. Explicit attempt budgets and resource thresholds add concrete enforcement for autonomous execution.

### Relationship classification

Risk-directed participation and early uncertainty reduction are retained. The target architecture—not the cited spiral model—defines `P0`–`P5`, one-use authority grants, and agent research budgets.

## 7. Agile change responsiveness

### Original problem

The Agile Manifesto documents four value contrasts: individuals and interactions over processes and tools, working software over comprehensive documentation, customer collaboration over negotiated terms, and responding to change over following a plan. It explicitly retains value in the items given lower priority.[36]

This chapter uses the last two contrasts as a design reference for keeping an early plan from silently overriding later accepted need and working evidence. That is a current interpretation of the Manifesto, not a sourced causal history of why its authors wrote it.

### Retained method

The target works in bounded increments, seeks executable or inspectable results early, and allows the latest accepted user direction or observed risk to reopen work. Requirements, Engineering, and QA exchange information throughout the mission rather than handing off once and disappearing.

Change is a first-class input. Policy performs impact analysis, creates a new revision when the meaning of acceptance changes, preserves the old baseline, and reopens the earliest affected workflow phase.

### Adaptation for LLM agents

Agents can rewrite documents and code much faster than humans can review the resulting semantic drift. Responding to change therefore cannot mean silently editing the active baseline or candidate. Every accepted change has an identity, source, affected records, invalidation set, and new completion path.

Working software remains more informative than a progress narrative, but it still requires evidence of the actual artifacts, execution, quality, and scope.

### Deliberate exclusions

The harness prescribes no named agile framework, ceremony, iteration length, backlog tool, or team role. “Responding to change” cannot waive security, evidence, configuration, or independent judgment. Necessary documentation remains part of the design because durable agent work requires explicit records when model context is temporary.

### Relationship classification

The target adopts small increments, feedback across areas of responsibility, and explicit responses to change. Revision identity and automatic evidence invalidation add enforcement specific to this harness.

## 8. Test-driven development

### Original problem

TDD addresses delayed feedback between an intended behavior and the code meant to implement it. A small failing example makes the next behavior concrete; minimal implementation makes it pass; refactoring improves design while the example suite protects behavior.[43]

Its value includes executable examples, design feedback, and regression protection. It is not simply “write more tests.”

### Design reference

TDD provides a design reference for short executable feedback. When a mission plan or an accepted engineering rule selects TDD, Engineering can write a failing example, implement enough behavior to make it pass, and then refactor while preserving the observed behavior. The accepted harness requirements and decision records do not currently make this cycle a universal target rule.

A failing test first demonstrates that the test can detect the missing or incorrect behavior. Passing after implementation shows only that the observed candidate satisfies that test under the recorded environment.

### Adaptation for LLM agents

An LLM can generate both code and a weak test that restates its implementation. The target therefore distinguishes implementer tests from independently controlled expected results and decision rules for acceptance, security-specific expected results and decision rules, research-method checks, and QA decisions. Implementer-written tests remain valuable engineering evidence but cannot alone authorize release.

Generated tests preserve generator identity, prompt or specification digest, environment, fixture provenance, and raw output where those affect interpretation.

### Deliberate exclusions

Not every artifact must begin with a unit test when another verification method is more appropriate. TDD completion remains distinct from independent verification and validation, and the implementer cannot weaken an accepted expected result to make the test pass.

### Relationship classification

The cited source documents the TDD method. This architecture uses it as a design reference, not as an adopted universal rule or a claim of direct historical influence. Independently controlled acceptance is a separate harness rule, not part of ordinary TDD itself.

## 9. Continuous integration

### Original problem

Continuous integration responds to long-lived divergence and difficult integration failures discovered late. Frequent mainline integration, automated builds and tests, a visible broken-build state, and prompt repair shorten the time between introducing and discovering an integration defect.[41]

The method operates on shared integration state, not only a developer’s local success.

### Design reference

Continuous integration provides a design reference for frequent shared integration and automated feedback. A mission baseline may require integration checks, but the accepted harness requirements and decision records do not currently require frequent mainline integration as a universal development process. The harness separately preserves the exact source, dependency, toolchain, command, environment, and artifact digests used for a candidate rather than accepting “worked locally.”

A failed required integration check blocks the relevant workflow phase or release decision. A later passing result must belong to a new valid attempt and the active candidate.

### Adaptation for LLM agents

Many agents may produce overlapping results from stale revisions. The harness therefore distinguishes logical work from attempts, rejects late superseded outputs, and binds integration results to candidate identity rather than arrival order. Generated checks are not considered independent merely because CI executed them.

Nondeterministic checks require a declared repetition and uncertainty policy; retries cannot be used to conceal a reproducible failure.

### Deliberate exclusions

The target does not prescribe a particular branching strategy or hosted CI product. A passing CI pipeline does not constitute approval. Continuous execution provides observations; policy and QA decide whether the required evidence is complete and valid.

### Relationship classification

The cited source documents continuous-integration practices. This architecture uses them as a design reference, not as an adopted universal process. Candidate identity, attempt supersession, and independently evaluated must-pass acceptance criteria are harness-specific rules.

## 10. Configuration baselines

### Original problem

Configuration management addresses the loss of identity that occurs when requirements, code, tools, data, and decisions change independently. Without configuration control, teams may continue referring to “the same version” even though its inputs differ. Systems engineering uses baselines and configuration control so that teams can assess changes and identify prior states.[32]

### Retained method

The target gives accepted mission inputs a revision identity and derives the identity of every frozen candidate from the work product and decision-relevant inputs. A baseline records not only source files but also every input that can change the decision: requirement revision, stage definition, quality profile, expected results, dependency state, toolchain, fixtures, model or prompt configuration where relevant, and parent lineage.

Impact analysis determines which downstream artifacts and observations become stale after a change. Old records remain in history but cannot satisfy an active gate.

### Adaptation for LLM agents

Natural-language assumptions are especially prone to silent drift. Shared concepts therefore carry stable IDs, versions, scope, definitions, and unresolved points. Handoffs refer to those IDs rather than relying on a receiver to infer the same meaning from prose.

### Deliberate exclusions

The harness does not implement a complete enterprise configuration-management organization, change-control board, or document-management system. Its identity, baseline, impact, and lineage rules apply only to the mission material it manages.

### Relationship classification

The target directly adopts baseline identification and controlled change. Candidate identities derived from content and records for shared concepts are mechanisms specific to this harness.

## 11. Event history and deterministic state projection

### Original problem

Event Sourcing captures changes to application state as a sequence of events. That sequence can support complete rebuilds, temporal queries, and replay of corrected history.[42] An append-only audit log alone does not provide those replay capabilities.

### Retained method

The target architecture selects a stronger deterministic-projection rule for its own state model. It records state-changing decisions as immutable events and defines deterministic projections for mission, task attempt, candidate, evidence validity, external side effect, and release state. A transition request is distinct from the accepted or rejected decision event, and a duplicate event identity must not apply the same transition twice. These are harness design rules; source [42] does not establish this complete protocol.

Corrections preserve history by appending superseding or invalidating events. The projection can therefore show which facts were believed at a past point and why a later decision changed.

### Adaptation for LLM agents

Model prose is not an event merely because it is stored. Policy first validates identity, authority, artifacts, hashes, and decision rules. Only the resulting accepted fact enters the authoritative sequence. Large model outputs and artifacts remain content-addressed files referenced by events rather than being duplicated into every event.

Event schema version and projection version are preserved so that replay does not silently reinterpret old facts under new code.

### Deliberate exclusions

The deterministic-projection rule belongs to the target architecture. The current implementation has append-only evidence records but has not demonstrated that every authoritative state is produced by the target projections or that replay produces equivalent state. This is an implementation gap relative to the harness's own rule, not evidence that source [42] requires the event log to be the sole system of record. Event history also cannot establish the current state of an external service.

### Relationship classification

Event Sourcing provides a prior-work reference for recording state changes as an event sequence and obtaining replay capabilities. Deterministic authoritative projection, the transition-request and decision-event boundary, duplicate handling, and schema and projection versioning are harness-specific target rules. The project makes no Event Sourcing conformance claim.

## 12. Secure development life cycle

### Original problem

Microsoft SDL and NIST SSDF address recurring vulnerabilities caused by treating security as a final penetration test. They distribute security requirements, design practices, threat analysis, protected implementation, verification, vulnerability response, and organizational preparation across the development life cycle.[37][38]

### Retained method

The target includes security during mission baselining. Security perspectives identify protected assets, actors, trust boundaries, misuse cases, required controls, negative tests, evidence, and residual risk before implementation. Each security criterion is a must-pass acceptance criterion evaluated independently.

The same lifecycle principle applies to data integrity and research validity: critical assurance work begins before code exists and continues through operation and response.

### Adaptation for LLM agents

The threat model adds prompt injection, untrusted retrieved content, tool overreach, role impersonation, fabricated execution, secret disclosure, provider boundaries, stale context, generated dependency risk, and ambiguity about external side effects. Tool and write permissions are enforced outside the prompt.

The harness also links each security observation to a candidate and invalidates the observation after a relevant change.

### Deliberate exclusions

The project does not claim Microsoft SDL or NIST SSDF conformance, maturity, or certification. It does not implement every practice in either framework. Organization-wide training, incident response, procurement, vulnerability disclosure, and operational security remain partly or wholly outside the harness unless a mission explicitly brings them into scope.

### Relationship classification

The source supports lifecycle security and early threat analysis, both of which the target adopts. The target extends the same planning pattern to other must-pass acceptance criteria.

## 13. Supply-chain provenance

### Original problem

in-toto models a software supply chain as authorized steps whose materials and products are attested, while SLSA defines incrementally stronger provenance and build expectations. Both address substitution, unauthorized transformation, and ambiguity about how an artifact was produced.[39][40]

Provenance completeness depends on the declared supply-chain boundary and verification policy; it is not absolute.

### Retained method

The target binds the following chain:

```text
mission revision
  → accepted stage and work order
  → issued authority grant and producer identity
  → command, environment, and input digests
  → output file digests
  → frozen candidate manifest
  → verification and findings tied to the candidate
  → release decision
  → package manifest and package digest
```

Each transformation identifies its materials, products or subjects, producer or execution identity, and the policy that verifies it. Relevant model, prompt, retrieved input, fixture, dependency, and tool versions are included when they can change the result.

### Adaptation for LLM agents

A model’s narrative is not provenance. The harness captures tool execution and actual file hashes independently. Since the same model can assume several roles, authorization and producer identity come from an issued authority grant and the execution boundary, not from model self-description.

Semantic judgments remain separate records. Perfect artifact lineage can preserve software that faithfully implements the wrong requirement.

### Deliberate exclusions

The project claims no in-toto layout compatibility, SLSA level, transparency-log publication, or hermetic builds. Provenance covers only the declared mission boundary and must identify excluded transformations; it does not prove functional correctness, intended-use validity, or current external state.

### Relationship classification

The target applies similar provenance reasoning by binding artifacts to their transformations, but it does not claim conformance with the cited specifications.

## 14. Durable execution, reconciliation, and compensation

### Original problem

Contemporary durable workflow systems preserve logical progress across process crashes and machine restarts. Temporal records workflow history for replay, DBOS resumes interrupted workflows from completed steps and supports idempotent workflow IDs, and Dapr describes durable, stateful, fault-tolerant workflow execution.[29][30][31]

These products are reference implementations, not the origin of checkpoint/restart, transaction, idempotency, or saga ideas. This chapter therefore uses them as current operational references rather than claiming a complete historical lineage.

### Retained method

The target separates each stable logical task from its individual attempts. It commits progress only after output, event, and checkpoint validation. A retry creates a new attempt under the same logical task and may resume from the last valid checkpoint.

### Adaptation for LLM agents

The harness adds an external-operation protocol beyond the cited workflow descriptions. Every external write uses a stable logical operation ID and an attempt-independent deduplication key. A durable receipt records the requested external side effect, provider, request digest, returned identity, observed state, and reconciliation method. Unknown outcomes enter reconciliation before retry. If a confirmed external side effect must be reversed after a permanent downstream failure, a registered compensation runs and records any residual state.

Model and tool calls are nondeterministic activities. Replay rebuilds orchestration state from the recorded request digest and returned result rather than invoking them again. Policy must authorize each new invocation as a new attempt.

Late results from superseded attempts may be retained for diagnosis but cannot become authoritative based on arrival time. Before resuming, recovery rechecks the mission revision, authority grant, candidate identity, checkpoint artifacts, and the state of external side effects.

### Deliberate exclusions

The harness makes no exactly-once guarantee for external side effects, and a missing response is not treated as proof of failure. Services that do not support deduplication or compensation require reconciliation, an explicit residual-risk decision, or a release hold.

### Relationship classification

The cited systems support durable progress, recovery, and selected idempotency mechanisms. The external-operation reconciliation and compensation protocol, together with candidate and evidence invalidation, is harness-specific synthesis.

## 15. Software assurance and independent verification and validation

### Original problem

NASA-STD-8739.8B defines a systematic approach to software assurance, software safety, and IV&V throughout the software life cycle, from conception through operation, maintenance, and retirement.[16] It designates software-assurance and software-safety information and plans as quality records. It also requires assurance organizations to retain records, reports, metrics, analyses, trending results, and project plans.[16]

The standard does not require general assurance planning to be organizationally separate from project management: the assurance organization and project manager jointly develop the assurance and safety plans. IV&V has a distinct independence rule; the standard defines technical, managerial, and financial independence and states that IV&V personnel performing the analysis are not involved in development.[16]

The standard’s definition of confirmation requires both adequate performance of specified activities and evidence that those activities occurred. Its audit definition requires a systematic, independent, documented process that obtains evidence and evaluates it objectively against criteria.[16]

### Retained method

The target retains five ideas: assurance starts with planning; required activities and products are explicit; evidence must exist as proof rather than as self-report; objective criteria govern evaluation; and independence is a property of responsibility and method, not a reviewer title.

A quality decision record therefore identifies the quality item and required threshold, applicable requirement revision, candidate, evidence identities, observation, expected result or decision rule, uncertainty, finding, residual risk, and release consequence. Missing, stale, unrelated, or producer-controlled evidence cannot be combined with stronger evidence to produce a pass.

### Adaptation for LLM agents

The harness converts organizational independence into enforceable separation among issued authority grants, workspaces, write paths, candidate access, expected-result control, execution identities, and final decision rights. It records model and prompt provenance because agents that appear separate may share correlated failure modes.

The policy engine verifies evidence binding mechanically before QA interprets meaning. QA cannot turn a schema-valid self-assertion into execution evidence.

### Deliberate exclusions

The harness does not claim compliance with the NASA standard, adoption of NASA technical-authority roles or signature practices, or safety certification. Independence by itself does not guarantee a correct verdict. When the necessary deterministic or domain-specific expected results and decision rules are unavailable, uncertainty and disagreement remain visible and may force a hold.

### Relationship classification

NASA software assurance and IV&V provide a documented reference for systematic assurance, objective evidence, and separation of responsibilities. The exact evidence record, one-use authority grants, and candidate hash model are specific to this harness.

## 16. Evidence-based completion synthesis

No cited historical model defines the complete target rule. The design combines bounded principles:

- protection determines **who may perform and decide** an operation;
- systems engineering and configuration determine **which accepted purpose, revision, and candidate** the result belongs to;
- verification, validation, inspection, and software assurance determine **which observations and independent judgments** are required;
- TDD and continuous integration provide **design references for early executable feedback** without becoming release authority;
- provenance determines **which actual transformation and artifacts** the observation covers;
- the harness's deterministic event projection determines **which accepted facts produce current state**;
- durable workflow methods inform **progress preservation and recovery**, while the harness-specific external-operation protocol governs **retries, unknown outcomes, and compensation**.

The target then applies this rule:

```text
completion exists only when policy can derive it
from independently acceptable evidence produced under an issued authority grant
and tied to the current candidate and applicable requirement.
```

Evidence sufficiency has distinct dimensions:

| Dimension | Required question |
|---|---|
| Authenticity | Was the observation produced by the recorded execution or decision identity under a valid issued authority grant? |
| Artifact reality | Do the declared regular files exist within the permitted root and match independently calculated SHA-256 values? |
| Currency | Does the evidence still apply after every accepted requirement, candidate, toolchain, fixture, and decision-rule change? |
| Attribution | Does it name the active mission, revision, stage, task, attempt, candidate, and quality item? |
| Relevance | Does the observation address the accepted requirement or must-pass acceptance criterion rather than a convenient substitute? |
| Independence | Were production, expected-result control, observation, and final judgment separated as required by risk? |
| Negative coverage | Were declared misuse, boundary, failure, and adversarial cases observed rather than only normal success? |
| Uncertainty | Are nondeterminism, disagreement, unknown external state, waivers, and residual risk visible? |

This synthesis should not be described as historically unprecedented or “beyond” all earlier models. The defensible claim is narrower: **the target architecture combines these reference principles in one enforceable state and evidence model for software development work performed by LLM agents.**

## 17. Limits of individual reference models

Each model leaves a different gap. Protection principles can mediate authority without determining whether a feature serves its intended user, and formal inspection can find defects without showing that a command ran. A verified implementation can still satisfy the wrong requirement, while rapid tests can repeatedly apply a weak expected-result rule. Provenance can faithfully preserve semantically wrong software, durable replay can faithfully resume the wrong task, and independent reviewers can share correlated model error.

The architecture applies these traditions as independent obligations rather than combining their results into one score. A mission must independently satisfy every applicable must-pass acceptance criterion for purpose, authority, artifact integrity, required behavior, evidence validity, and residual-risk decisions. Failure in one obligation blocks the dependent transition regardless of strength elsewhere.

## Sources

[16] NASA, *NASA-STD-8739.8B Software Assurance and Software Safety Standard*. https://standards.nasa.gov/standard/NASA/NASA-STD-87398

[29] Temporal, *Temporal Workflow*. https://docs.temporal.io/workflows

[30] DBOS, *DBOS Workflows*. https://docs.dbos.dev/python/tutorials/workflow-tutorial

[31] Dapr, *Dapr Workflow Overview*. https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-overview

[32] NASA, *NASA Systems Engineering Handbook*. https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf

[33] Michael E. Fagan, *Design and Code Inspections to Reduce Errors in Program Development*. https://doi.org/10.1147/sj.153.0182

[34] Barry W. Boehm, *A Spiral Model of Software Development and Enhancement*. https://doi.org/10.1109/2.59

[35] Jerome H. Saltzer and Michael D. Schroeder, *The Protection of Information in Computer Systems*. https://doi.org/10.1109/PROC.1975.9939

[36] *Manifesto for Agile Software Development*. https://agilemanifesto.org

[37] Microsoft, *Security Development Lifecycle*. https://www.microsoft.com/en-us/securityengineering/sdl

[38] NIST, *SP 800-218 Secure Software Development Framework*. https://csrc.nist.gov/pubs/sp/800/218/final

[39] in-toto, *in-toto Specification v1.0*. https://github.com/in-toto/specification/blob/v1.0/in-toto-spec.md

[40] SLSA, *About SLSA*. https://slsa.dev/spec/v1.2/about

[41] Martin Fowler, *Continuous Integration*. https://martinfowler.com/articles/continuousIntegration.html

[42] Martin Fowler, *Event Sourcing*. https://martinfowler.com/eaaDev/EventSourcing.html

[43] Agile Alliance, *What is Test Driven Development?*. https://agilealliance.org/glossary/tdd
