# Issue #53 — user-story traceability and evidence ledger

Last audited: 2026-10-09. Scope: the upstream [OpenLEADR/openleadr-rs #53](https://github.com/OpenLEADR/openleadr-rs/issues/53) and directly supporting [PR #525](https://github.com/OpenLEADR/openleadr-rs/pull/525). This is NOT a claim to exhaust every issue in the upstream repository.

## Source baseline and history
- #53 asks for Program and Event client integration tests to stop depending on sqlx-created PostgreSQL databases, run against a configured VTN URL and credentials, run serially, and avoid leaving state after failures. Existing VEN/Resource tests provide examples.
- Maintainer discussion on #53 emphasizes implementation-independent Rust fixtures rather than testcontainers and allows incremental draft PRs.
- #525 supplies configurable credentials but explicitly claims only an initial seam and retains local admin defaults for compatibility. It remains open and is not a resolution of #53.
- This fork's `feat/external-vtn-readonly-conformance-smoke` contains experimental opt-in external probes; they are not upstream-merged.

## State definitions
- VERIFIED: code and required automated/E2E tests executed successfully, with linked evidence.
- IMPLEMENTED_UNVERIFIED: source committed; required tests not executed or not demonstrated.
- PARTIAL: acceptance conditions not implemented end-to-end.
- BLOCKED: missing required environment, permissions, or external inputs.
- NOT_IN_SCOPE: idea not grounded in #53 or another repository issue/story, tracked separately; never mark #53 finished by shipping it.

## Traceability matrix

| ID | Source requirement | Implementation evidence | Acceptance condition | State |
|---|---|---|---|---|
| US53-01 | Program tests must not require sqlx database | `tests/external_vtn_program_crud.rs` | Cargo compile + CRUD executes without PgPool or DATABASE_URL against independent VTN | IMPLEMENTED_UNVERIFIED |
| US53-02 | Event tests must not require sqlx database | `tests/external_vtn_event_crud.rs` | Same, including parent Program and child Event lifecycle | IMPLEMENTED_UNVERIFIED |
| US53-03 | Configurable VTN URL and valid role credentials | #525, `tests/common/mod.rs` | Known-good independent VTN with explicit credentials; clear auth-failure evidence | PARTIAL |
| US53-04 | Serial execution to avoid shared state conflicts | `#[serial]` for destructive test modules | Two separately launched processes cannot interfere on shared VTN; prove with concurrency injection | PARTIAL |
| US53-05 | Failure does not leave VTN state changed | opt-in CRUD probes with delete + not-found verification; parent deletion withheld if child delete failed | Inject read/update/delete failures; recovery after kill; inventory orphan objects and clean them | PARTIAL |
| US53-06 | Fixtures independent of VTN implementation | experimental HTTP-only probes; existing `program.rs` and `event.rs` still use `#[sqlx::test]` | Replace/migrate existing test families and data setup, demonstrate two distinct VTN implementations | PARTIAL |
| US53-07 | Existing VEN/Resource behavior maintained | no changes to their test files | Cargo regression tests with retained behavior and independent external runs | BLOCKED |
| PR525-01 | First configuration seam with backwards compatibility | upstream PR #525, DCO checks | upstream reviewer acceptance and successful CI/test matrix | PARTIAL |

## Defect register
| Defect | Priority | Evidence | Resolution / remaining gate |
|---|---|---|---|
| DEF-01 parent Program cleanup attempted after child Event cleanup error | P0 | prior `external_vtn_event_crud.rs` | FIX COMMITTED: parent withheld if child cleanup fails; runtime failure injection pending |
| DEF-02 external test resource cleanup not durable across process termination | P0 | current test files log IDs only | OPEN: durable recovery journal and crash/replay test needed |
| DEF-03 `#[serial]` cannot coordinate separate cargo test binaries/processes | P0 | test structure | OPEN: lock or dedicated per-run VTN isolation, cross-process test needed |
| DEF-04 former in-tree test suites still accept PgPool | P0 | `tests/program.rs`, `tests/event.rs` | OPEN: migrate legacy family and rerun regression |
| DEF-05 no executed Rust build or live independent VTN results | P0 | absence of CI run on fork experimental branch / external VTN endpoint | BLOCKED: Rust toolchain and independent disposable VTN needed |
| DEF-06 separate credentials policy differs from #525 compatibility promise | P1 | experimental `tests/common/mod.rs` requires explicit credentials; PR #525 preserves defaults | OPEN: reconcile with maintainer before merge; do not silently alter PR #525 |

## Evidence and known limits
- GitHub source changes and SHA links prove only that modifications were persisted, not that Cargo compiled them.
- #525 DCO was observed successful on head `9139c1718ee1043493f343f02c84f0fd00d9b7cf`; this does not certify the experimental branch.
- No real external-VTN CRUD run, failure injection, or cross-process lock test is verified at this audit.
- #53 remains OPEN upstream. No third-party adoption or conformance certification is claimed.

## Next executable entry point
1. Run `cargo test -p openleadr-client --test external_vtn_readonly` (non-ignored URL unit tests) and `cargo test --no-run -p openleadr-client --tests` on this branch. Attach actual exit code/log/commit SHA to this ledger.
2. Execute ignored probes on a **disposable, exclusively controlled VTN** with authorized credentials and the required opt-ins. Capture result and resource cleanup evidence. Never run mutation probes on shared or production VTNs.
3. Inject failed Event deletion and confirm the parent Program remains identifiable; then recover both resources. Add durable recovery/journal and cross-process isolation before marking US53-05 verified.
4. Migrate existing SQL-dependent families, run baseline regressions, and request upstream review of scoped changes. Keep experimental tests out of #525 until reviewed.

No user story in this document is marked VERIFIED until its corresponding acceptance evidence exists.
