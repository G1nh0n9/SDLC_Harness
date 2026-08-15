# Architecture Content Coverage

> This verification map connects the requested architecture content to the exact explanatory sections. It is not a substitute for the prose.

| Requested content | Primary section | What the section must demonstrate |
|---|---|---|
| Problem and reason to use the harness | `overview-and-scope.md`; deep dive `purpose-and-scope.md` §§1–3 | Why multiple agents, role prompts, self-reported tests, and chat consensus do not establish authority or completion |
| Narrow assurance and deliberate non-goals | `overview-and-scope.md`; `trust-overview.md`; deep dives `purpose-and-scope.md` §§3–6 and `trust.md` | What deterministic policy can enforce; why total correctness, OS isolation, correctness of external-service results, and exactly-once effects are outside the claim |
| System boundary and normal path | `architecture-at-a-glance.md` | Policy boundary, logical responsibilities, stable nine-step mission path, authoritative record groups, and containment of the five opening failures |
| Requirements, Engineering, and QA areas of responsibility | `operating-model-overview.md`; deep dive `operating-model.md` §§1–3 | Inputs, outputs, decisions, forbidden actions, and joint quality planning from requirements definition onward |
| Mission Manager responsibility and prohibitions | `operating-model.md` §2 | Request specificity, workflow phase, expert, risk, evidence, and transition coordination without implementation, review, self-approval, or packaging |
| Dynamic perspectives and participation profiles | `operating-model.md` §4; `worked-mission.md` §4 | Perspectives are enumerated first; the P0–P3 base level of involvement, P4 independence, P5 investigation, three types of knowledge, and conflicts of interest determine how experts are grouped |
| Research-software must-pass acceptance criteria | `operating-model.md` §3 | Method suitability, semantic alignment, metric validation, experiment integrity, raw-data-to-report provenance, and evidence that effects stayed within the approved scope are evaluated separately and must pass independently |
| Common foundation and dual handoff acceptance | `operating-model.md` §5; `worked-mission.md` §9 | Schema, identity, path, regular-file, and SHA-256 checks, together with receiver acceptance |
| Prior work and harness-specific adaptation | `prior-work-overview.md`; deep dive `prior-work.md` §§1–17 | The main path explains the design concerns and harness synthesis; the deep dive separates direct source support, retained rules or design references, adaptations, exclusions, and attribution evidence |
| One mission from request to release | `worked-mission-overview.md`; deep dive `worked-mission.md` §§1–14 | The main path preserves the stable nine-step mission and C1→C2 correction; the deep dive preserves authority, manifests, gates, compact records, and the complete causal trace |
| False-completion rejection | `worked-mission.md` §13 | Each role-text, self-pass, old-revision, changed-candidate, self-approval, missing-artifact, symbolic-link-escape, incomplete-test, wrong-mission, and false-checkpoint case includes a reason, unchanged state, appended decision, and permitted follow-up |
| Logical enforcement architecture | `runtime-overview.md`; deep dive `runtime.md` §§2–5 | Mission, planning, policy, workspace, execution, candidate, handoff, QA, records, and policy-only transitions |
| Separate authoritative state machines | `runtime.md` §5 | Mission revision, task attempt, candidate, evidence validity, external operation, compensation, and release states cannot collapse into one status |
| Central transition procedure | `runtime.md` §6 | Stored authority, current state, stage records, files, hashes, blockers, and quality decisions are checked before one appended decision |
| Artifact and SHA-256 completion | `reliability-overview.md` §§1–2; deep dives `worked-mission.md` §§7–10 and `reliability.md` §§1–2 | Actual regular files and independently calculated hashes bind evidence to one candidate and active revision |
| Interruption before and after checkpoint | `reliability.md` §3 | Uncommitted partial output is not reusable; committed verified progress resumes under a new attempt |
| Duplicate result and superseded attempt | `reliability.md` §4 | Event identity prevents a duplicate transition; arrival time does not make either conflicting output authoritative |
| Unknown external side effect and state reconciliation | `reliability.md` §5 | A stable logical operation ID, an unknown state, a status query before replay, and blocked completion when status cannot be established |
| Compensation and residual external state | `reliability.md` §6 | Confirmed partial success remains in history, and completion requires observed evidence of mission-specific compensation |
| Mandatory failure and immutable child candidate | `reliability.md` §7; `worked-mission.md` §11 | The failed candidate stays unchanged; the correction receives a child identity and new evidence for the affected checks |
| LLM verifier disagreement and bias | `reliability.md` §11; `trust.md` §7 | Attribute-by-attribute judgment, order reversal, model provenance, the rule that assigning the same model different role labels does not create independence, and an insufficient-evidence outcome |
| Completion invalidation | `reliability.md` §8 | Later valid rework appends invalidation, changes release state, and reopens the earliest affected stage |
| Trust boundary and external controls | `trust-overview.md`; deep dive `trust.md` §§1–9 | Protected assets, input trust levels, the `export-ownership` boundary path, target enforcement, OS controls, model limits, external side effects, and residual uncertainty |
| Terms, schemas, states, code, tests, and decisions | `reference-overview.md`; deep dive `reference.md` | Stable navigation from explanations to normative and implementation material |
| Target record fields and validation order | `reference.md` §4 | Mission, quality, perspective, stage, authority, attempt, checkpoint, candidate, evidence, handoff, finding, external side effect, invalidation, and release records |

## Verification rules

1. A row is covered only when the primary section contains explanatory prose, not merely a heading or outbound link.
2. The same worked mission and identifiers must remain consistent across normal execution, failure injection, recovery, and invalidation.
3. Historical claims require inline citations and a mechanically generated source list.
4. Target capability and current implementation evidence must remain separately labeled.
5. The generated guide must include the complete newcomer path and link every intentionally omitted state, event, schema, and attribution detail to its authoritative deep-dive source.
