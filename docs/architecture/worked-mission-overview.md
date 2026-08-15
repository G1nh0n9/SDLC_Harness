# Worked Mission: `export-ownership`

> **This chapter explains:** how one request becomes a frozen candidate, why the first candidate is held, and how a corrected child candidate reaches release.

> **Reading note:** This is an illustrative execution of the target architecture. It does not claim that the current Python package implemented the feature or produced the symbolic records used below.

## 1. Scenario and acceptance boundary

The user asks:

> Add an authenticated data-export feature that returns only records owned by the requesting account.

The Mission Service records `mission-export-ownership` and creates `revision-0001`. Before implementation, the baseline resolves what counts as the requesting account, which records and formats are supported, how temporary export material is retained, and which storage modes are in scope.

The release boundary includes five must-pass conditions:

- an authenticated account receives only its own records;
- unauthenticated and cross-account requests fail before material is exposed;
- required owned records are complete and not duplicated;
- every declared configuration completes as specified;
- every asynchronous export operation has a known outcome, and every resulting external side effect is tracked.

Usability and performance remain improvement targets unless the accepted baseline promotes them to must-pass acceptance criteria. They cannot offset a security or data-integrity failure.

## 2. Walkthrough

The same nine steps introduced in the system overview carry the mission from request to release.

1. **Create the revision.** The planner determines whether the request is specific enough to choose a development path and verify the result. Acceptance-changing steering creates another revision.
2. **Accept the quality baseline.** Requirements defines ownership and forbidden disclosure; Engineering identifies the authorization and storage boundaries; QA defines independent ownership fixtures, negative cases, and required observations.
3. **Assign the required expertise.** The authorization perspective requires continuous expert participation and independent assessment. The perspective on storage semantics can trigger a bounded investigation when documentation and existing evidence do not answer a release-relevant question.
4. **Issue bounded authority.** Engineering receives a one-use authority grant for one task attempt, approved workspace, allowed operations, and approved tools. A submitted role name cannot expand it.
5. **Execute and capture.** The runner records the executable, arguments, bounded environment, exit status, output, produced files, checked SHA-256 values, checkpoints, and external-operation IDs.
6. **Freeze candidate `C1`.** The Candidate Manager binds source, requirements, independently controlled expected results and decision rules, build settings, dependencies, and toolchain identity to one immutable manifest. Verification cannot edit this material.
7. **Accept the handoff.** Automatic checks validate identity, lineage, paths, regular files, and hashes. The independent verifier separately confirms that the handoff is understandable and usable.
8. **Verify `C1`.** QA reruns the required checks in a read-only workspace, compares observations with independently controlled expected results and decision rules, and records criterion results for `C1`.
9. **Decide and package.** Policy accepts a release decision only when every required observation belongs to the active revision and candidate and no blocker remains. Packaging can use only the approved candidate and evidence set.

## 3. From `C1` to `C2`

QA finds that a secondary download route accepts an account ID from the request and bypasses the authenticated ownership filter.

1. QA records a reproducible authorization finding for `C1`.
2. The security acceptance criterion fails, and the mission is held.
3. `C1` remains unchanged.
4. Engineering receives a correction-only authority grant and creates child candidate `C2` with `C1` as parent.
5. Evidence that depends on the changed authorization path becomes `STALE`.
6. Automatic handoff checks and receiver acceptance run again for `C2`.
7. QA receives a new read-only authority grant, reruns every affected case, and records fresh observations for `C2`.
8. After every applicable must-pass acceptance criterion passes independently, the new quality decision records `RELEASE` for `C2`.
9. Policy makes `C2` `PACKAGE_ELIGIBLE`; packaging produces `PKG2` from the exact `C2`, `QD2`, and `ES2` identities.

The original hold and stale decisions remain in the history. A change from individual ownership to organization-wide ownership would create `revision-0002`, not merely another child candidate, because it changes the meaning of acceptance.

## 4. Observable decision chain

| Decision point | Required material | Result in this mission |
|---|---|---|
| Baseline acceptance | Contributions from all three areas, quality profile, methods, and open assumptions | `revision-0001` can enter execution |
| Candidate freeze | Complete input manifest, checked bytes, toolchain identity, and lineage | `C1`, then child `C2` |
| Handoff acceptance | Automatic identity and file checks plus receiver acceptance | QA may begin read-only verification |
| Criterion decision | Independent observations and findings bound to one candidate | Authorization fails for `C1`; affected checks pass for `C2` |
| Release and package | Complete valid evidence set, no unresolved blocker, exact candidate binding | `QD2=RELEASE`, `C2:PACKAGE_ELIGIBLE`, `PKG2:CREATED` |

No transition succeeds merely because a payload names the expected role, state, or result.

**Next:** [Runtime Architecture](runtime-overview.md) shows which logical components enforce each step. The [complete worked-mission trace](worked-mission.md) preserves the authority records, manifest derivation, rejection cases, and `event-0001` through `event-0035` for readers auditing causal closure.
