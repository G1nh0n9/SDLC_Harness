# Core Concepts and Operating Model

> **This chapter explains:** the stable concepts, responsibility separation, and planning decisions needed to read the worked mission.

## 1. Core concepts

| Concept | Meaning in this architecture |
|---|---|
| **Mission** | A bounded user outcome whose work, evidence, and decisions share one identity. |
| **Revision** | One accepted interpretation of the mission. An acceptance-changing instruction creates a new revision rather than rewriting the old one. |
| **Task** | A logical unit of work in the workflow plan. |
| **Attempt** | One execution of a task under one authority grant and retry budget. A retry creates a new attempt, not a new logical task. |
| **Authority grant** | An issued, bounded record that establishes acting identity and permitted operations for a specific mission, revision, workflow phase, task, attempt, workspace, and candidate when applicable. |
| **Candidate** | An immutable verification unit that binds the work product and every decision-relevant input to one identity. It is not a person or a mutable directory. |
| **Evidence** | A checked artifact, execution record, observation, handoff decision, or finding whose dependencies and identity are explicit. |
| **Quality decision** | A candidate-bound result for each must-pass acceptance criterion plus the supported release scope, uncertainty, and residual risk. |

## 2. Areas of responsibility

The three areas define quality together, then remain separate where combining authority would undermine the decision.

- **Requirements and Outcomes** defines the intended result, scope, forbidden behavior, scenarios, and what acceptance means. It cannot declare its own requirements satisfied.
- **Engineering and Software Delivery** designs and builds a reproducible candidate. It cannot modify independently controlled expected results or decision rules, approve the candidate, or edit a candidate under review.
- **Verification and Quality Assurance** determines what the frozen candidate demonstrates and whether the observations support the intended use. It cannot modify the candidate or invent missing execution evidence.

The **Mission Manager** coordinates workflow phases, dependencies, disputes, resources, and transition requests. It does not implement work, perform final quality judgment, or change state. The **Policy and State Engine** is the only authority that may accept a transition and derive the next authoritative state.

## 3. Joint quality planning

Before Engineering receives write authority, the three areas establish:

- intended outcome, scope, and forbidden behavior;
- must-pass acceptance criteria and improvement targets;
- required perspectives and verification methods;
- independently controlled expected results and decision rules;
- required inputs, outputs, observations, and handoff material;
- assumptions that would reopen the baseline.

A must-pass acceptance criterion succeeds or fails independently. Performance, usability, or reviewer enthusiasm cannot offset a confirmed authorization, integrity, security, or required-functionality failure.

## 4. Participation profile

The planner enumerates perspectives before deciding how many experts or agents to use. Participation has three independent fields:

```text
delivery_depth: P0 | P1 | P2 | P3
independent_assessment_required: true | false
bounded_investigation_required: true | false
```

`P0` through `P3` describe the base level of involvement: deterministic enforcement, routine coverage by an assigned expert, consultation at defined decision points, or continuous participation throughout a workflow phase. Independent assessment and bounded investigation are separate conditions. Display forms such as `P3+P4`, `P2+P5`, and `P2+P5+P4` are shorthand; P4 and P5 are not higher ranks than P3.

Perspectives may share an expert only when their responsibility, knowledge, workflow phase, and quality objectives are compatible. Implementation remains separate from final judgment, and implementation remains separate from control of the independently controlled expected results and decision rules used to evaluate it.

## 5. Handoff and decision rights

A handoff advances only after two decisions:

1. automatic checks confirm schema, identity, required material, regular-file status, permitted paths, SHA-256 values, lineage, and producer authority;
2. the receiver confirms that the material is understandable, complete enough, and usable without recreating the previous work.

A structurally valid but unusable handoff does not pass. A persuasive explanation with missing files or incorrect hashes also does not pass.

Policy owns state transitions and candidate identity. Engineering owns design and implementation within issued authority. QA owns findings and final quality judgment under separate authority. Packaging receives an approved candidate and evidence set but cannot edit source or acceptance material.

**Next:** [Worked Mission: `export-ownership`](worked-mission-overview.md) applies these concepts to one request. The [operating-model deep dive](operating-model.md) contains the complete perspective inventory, participation rules, research escalation, and decision-rights table.
