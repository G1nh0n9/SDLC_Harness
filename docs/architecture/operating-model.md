# Operating Model

> **This chapter explains:** who defines, builds, verifies, and decides, and how the harness assigns the experts needed for a mission.

## 1. Three areas of responsibility

### Requirements and Outcomes

**Purpose:** Define the result that would satisfy the user’s actual objective.

**Inputs:** user intent, domain context, legal and operational constraints, risk, prior decisions.

**Outputs:** desired outcomes, scope, forbidden behavior, scenarios, quality contributions, unresolved assumptions.

**Cannot:** declare its own requirements satisfied or lower an accepted quality baseline alone.

### Engineering and Software Delivery

**Purpose:** Turn the accepted baseline into a reproducible candidate.

**Inputs:** baseline, design constraints, accepted handoffs, allowed tools and write paths.

**Outputs:** design decisions, source, self-tests, build records, candidate material, known limitations.

**Cannot:** modify independently controlled expected results or decision rules, approve the candidate, or edit a candidate under review.

### Verification and Quality Assurance

**Purpose:** Determine what the candidate actually demonstrates and whether that supports the intended use.

**Inputs:** baseline, immutable candidate, independent fixtures and methods, execution records.

**Outputs:** verified observations, reproducible findings, quality decisions, uncertainty, residual risk, release scope.

**Cannot:** modify the candidate, invent missing execution evidence, or treat reviewer consensus as a deterministic expected-result rule.

## 2. Mission management

The Mission Manager coordinates workflow phases and their dependencies, disputes, resource escalation, and transition requests.

For each revision, the manager is responsible for making six planning decisions explicit:

1. whether the request is specific enough to choose a development path and verify the result;
2. which workflow phases and dependencies the mission needs;
3. which perspectives must be covered, what P0–P3 level of involvement each needs, and whether P4 independence or P5 investigation is required;
4. which perspectives can share an expert and which require independent authority;
5. which inputs, outputs, observations, and quality decisions are required in each workflow phase;
6. which risk, time, or resource condition pauses autonomous work and requires another decision.

The manager can reject an incomplete plan, request a missing contribution, route a technical disagreement to research, and request a policy transition. It cannot substitute for the substantive judgment that belongs to an area of responsibility.

It does not:

- implement product code;
- create independently controlled expected results or decision rules;
- approve its own output;
- alter a reviewed candidate;
- package a release.

The manager also cannot remove required evidence after a candidate is created, convert a failed must-pass acceptance criterion into an improvement target, choose between conflicting implementation outputs by arrival order, or treat a worker's completion message as a transition instruction.

When experts disagree, the manager records the disagreement and routes the question. It cannot erase a failed must-pass acceptance criterion by averaging opinions.

## 3. Quality planning

The three areas collaborate before the mission baseline is accepted. Together, they establish:

- intended outcome and scope;
- forbidden behavior and misuse cases;
- must-pass acceptance criteria;
- improvement targets;
- required perspectives and participation profiles;
- verification methods and independently controlled expected results;
- workflow-phase inputs, outputs, and evidence;
- assumptions that would reopen the baseline.

The Mission Manager checks completeness and internal consistency. It does not substitute for expert judgment.

The three areas reconvene at three defined points without combining their authority:

1. **Mission and quality baseline:** agree on the intended outcome, required perspectives, must-pass acceptance criteria, methods, and unresolved assumptions.
2. **Design readiness:** confirm implementation feasibility, independent expected-result readiness, measurement feasibility, and remaining disputes before broad implementation.
3. **Input to the quality decision:** compare the frozen candidate and the observations tied to it with the accepted outcome, quality profile, uncertainty, and proposed release scope. QA retains authority over the final quality judgment; the meeting itself does not constitute approval.

Each joint review records its identity, participants and verified authorities, input artifacts and hashes, each area's contribution, agreements and disagreements, the accepted rationale, the owner responsible for follow-up, and the next completion rule. A meeting note saying “looks good” cannot replace those records.

### Must-pass acceptance criteria

Correctness, security, data integrity, required functionality, and mission-specific research validity are must-pass acceptance criteria. Each criterion must pass independently; strength in one area cannot offset failure in another.

When software produces research claims, research validity requires six separate acceptance criteria:

1. The method is suitable for the research question and data.
2. The method described in the paper, the algorithm description, and the executable implementation have the same meaning.
3. Evaluation metrics, aggregation rules, and boundary handling have been independently validated.
4. Data selection, experiments, and statistical analysis preserve research integrity.
5. The path from raw data to reported tables and figures is reproducible and records provenance.
6. Bounded evidence shows that no effects occurred outside the approved research scope.

Each criterion must pass independently.

After all must-pass criteria have passed, QA may weigh improvement targets such as usability, maintainability, performance margin, documentation quality, and operational convenience against the intended outcome.

### Quality profiles by intended use

The quality profile follows the declared use, not a universal checklist.

A disposable prototype may support one path using synthetic data, exclude external writes, and require only enough performance and documentation to answer a bounded feasibility question. An operational feature may require every supported backend, real authorization boundaries, migration behavior, monitoring, recovery, retention, rollback, user documentation, and release operations.

This scaling changes the supported scope, participation profiles, evidence volume, and improvement targets. It does not allow a prototype to fail a must-pass acceptance criterion within its claimed scope. A prototype that handles real credentials or personal data still has to meet the applicable security and privacy criteria; otherwise, the baseline must exclude those inputs and policy must prevent their use.

## 4. Perspective-based expert assignment

The harness does not start by choosing a fixed number of agents. It follows four steps.

### 4.1 Perspective inventory

Every mission considers a baseline set:

- outcome and scope;
- general software engineering;
- correctness and required functionality;
- security;
- data integrity;
- privacy and law;
- usability and accessibility;
- performance;
- operations and recovery;
- maintainability and supply chain;
- documentation;
- domain knowledge;
- research method;
- external side effects.

A perspective may be marked not applicable only with a reason. It does not silently disappear.

### 4.2 Participation profiles

`P0` through `P5` are planning codes, not ranks or indicators of professional seniority, and they do not form a single scale. `P0` through `P3` describe the base level of involvement for one perspective. `P4` and `P5` add requirements that can be combined with that base level.

| Code | Planning question | Required arrangement |
|---|---|---|
| **P0 — enforced automatically** | Can an accepted deterministic rule or automated check handle this perspective completely? | Name the rule, the input it checks, the expected result, and the action taken on failure. No additional human expert performs the check. The relevant area of responsibility remains accountable for the rule and responds when the check fails. |
| **P1 — covered by an assigned expert** | Is this routine work already within the declared expertise of someone assigned to Requirements, Engineering, or QA? | Name the assigned expert, the artifact or decision for which they are responsible, and the method they will use. P1 does not mean that the perspective may be assumed or omitted. |
| **P2 — expert consulted at defined points** | Does the work require deeper domain knowledge to answer a specific question? | State the question, input, deliverable, and deadline; assign a domain expert; and identify who will use the expert's answer. That expert does not participate continuously throughout the workflow phase and does not gain final approval authority. |
| **P3 — expert participates throughout a workflow phase** | Does the work require an expert's judgment at multiple points in one workflow phase? | Keep the assigned expert involved in planning, intermediate decisions, artifact production or review, and handoff for the named workflow phase. That expert cannot independently approve work they produced. |
| **P4 — independent assessment required** | Must a result be assessed by someone who did not produce it? | Add a separate assessor with independent authority, an isolated or read-only workspace, fixed criteria, and no permission to edit the candidate or expected result. Attach P4 to the relevant base level, for example `P3+P4`. |
| **P5 — bounded investigation or R&D required** | Is a decision blocked because accepted knowledge or evidence is missing? | Open a time- and resource-bounded investigation of a stated research question through a review of authoritative sources, a prototype, or an experiment. Define stop conditions and a deliverable that supports the named decision. P5 does not confer approval authority; add P4 when the resulting claim also needs independent assessment, for example `P2+P5+P4`. |

The perspective plan therefore stores `delivery_depth: P0|P1|P2|P3`, `independent_assessment_required: true|false`, and `bounded_investigation_required: true|false`, plus the reason, workflow phase, owner, output, and completion rule. The `delivery_depth` value means the base level of involvement in the work; it does not refer to software shipping, rank, or seniority. Display forms such as `P3+P4` are shorthand for that structured profile.

Risk may increase the base level of involvement, require independent assessment, or open an investigation. Those are separate decisions, and none of them automatically determines the number of agents.

### 4.3 Knowledge requirements

1. **General methods:** how to conduct research, write technical material, decompose problems, construct and evaluate arguments, assess uncertainty, and prepare a structured handoff.
2. **Domain expertise:** general software engineering plus the mission-specific technical knowledge needed for the assignment.
3. **Role-specific decision knowledge:** which decisions the Requirements, Engineering, QA, Research, or Release function assigns to that expert.

Expertise adds depth but does not replace the common foundation needed for an effective handoff and review.

### 4.4 Expert grouping and separation

Perspectives may be assigned to the same expert when their area of responsibility, workflow phase, knowledge, and quality objectives are compatible.

They remain separate when grouping would combine:

- implementation with final judgment;
- expected-result design with implementation;
- evidence production with final validity assessment;
- materially different domain expertise;
- a high-risk decision with its own approval.

## 5. Handoff validation

A handoff passes only after two decisions.

The producer does not assume that the receiver shares every unstated term or method. The handoff carries a `shared_foundation`: stable concept identifiers, names, versions, sources when applicable, quality items, and the scope in which each definition is valid. It also identifies which assumptions and expert judgments are not shared facts.

For example, the `export-ownership` handoff defines whether ownership means an authenticated individual, a selected organization, or another principal; names the accepted output schema; and links the must-pass authorization criterion and its independent fixture identity. The receiver can then detect a semantic mismatch without inferring meaning from similar words.

### Automatic checks

The harness checks:

- schema and required fields;
- mission, revision, stage, task, and candidate identity;
- required inputs and outputs;
- regular-file status and allowed paths;
- checked SHA-256 values;
- absence of disallowed symbolic links;
- producer authority and event identity.

### Receiver acceptance

The receiving expert decides whether to accept the material as understandable, sufficiently complete, and usable without recreating the previous work.

Acceptance or rejection must name the relevant shared concept or quality item and explain the missing, inconsistent, or unusable material. An unsupported refusal is not itself an authoritative failure; policy requests a reasoned receiver decision or routes the dispute.

A file can be structurally valid but unusable. A persuasive narrative can be useful but fail structural or identity checks. Both decisions are required.

## 6. Research and dispute resolution

A disagreement is not sent to the user merely because agents disagree. The manager first determines whether resolving the disagreement could change the outcome and whether public evidence can resolve it.

The escalation path is:

1. state the disputed question and decision it affects;
2. search primary papers, official standards, official product documentation, or credible public engineering reports;
3. assess applicability to the mission rather than copying a general practice;
4. run a bounded experiment when evidence is insufficient;
5. record the result and remaining uncertainty;
6. ask the user only when the unresolved choice changes purpose, risk acceptance, cost, or scope.

Work marked P5 always has a stop condition and a resource limit. For this harness project, the manager stops and submits a research-and-development plan before starting work projected to consume at least 10% of the OpenAI Codex Max x20 weekly allowance or to run for at least eight hours in one session. The same pause applies when work already in progress is newly projected to cross either threshold.

## 7. Decision rights

| Decision | Primary responsibility | Required contributors | Final authority |
|---|---|---|---|
| Mission outcome and scope | Requirements | Engineering, QA | Policy acceptance of the baseline |
| Design and implementation | Engineering | Relevant experts assigned throughout the workflow phase | Engineering within its issued authority grant |
| Expected results and verification method | QA with Requirements | Engineering for feasibility only | Policy acceptance of the baseline |
| Candidate identity | Policy | Engineering submits inputs | Policy and Candidate Manager |
| Quality finding | QA | Independent execution when required | QA under its issued authority grant |
| State transition | No area alone | An authorized requester supplies evidence | Policy and State Engine |
| Release scope | QA | Requirements and Engineering provide information about residual risk | Policy, after evidence checks |
