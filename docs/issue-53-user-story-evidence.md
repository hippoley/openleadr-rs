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

## Execution log — 2026-10-09, follow-up audit
- **P0 false-positive test coverage fixed:** `external_mutation_guard.rs` previously contained a vacuous string comparison that never exercised authorization. Replaced with pure `validate_target` invoked by the production guard and three table-driven positive/negative unit tests. Commit: `d6d6f61469fff1c33fc0e2d4c2437fa81c36c9f7`.
- **Verification status:** GitHub source change verified; unit tests NOT EXECUTED. The available execution container did not provide `cargo` in PATH; no real VTN credentials/endpoint are available. This is not a VERIFIED story.
- **DEF-07 (P0, FIX COMMITTED / TEST BLOCKED):** prior guard test was a false-positive assertion comparing literals, not testing the guard. Its code was replaced but test outcome remains unknown pending Cargo execution.
- **Scope integrity:** existing upstream #525 head remains `9139c1718ee1043493f343f02c84f0fd00d9b7cf`; experimental branch remains separate. Issue #53's migration, cross-process isolation and recovery criteria remain incomplete.
- **Resume directly:** run `cargo test -p openleadr-client --test external_mutation_guard` and `cargo test -p openleadr-client --tests --no-run`; record exit codes and error traces here. If passing, execute independent VTN test matrix only on explicitly authorized, isolated VTN.

## Horizontal Completeness Audit (HCA) — 2026-10-09

**Applicability and provenance.** The only upstream requirement baseline here is [#53](https://github.com/OpenLEADR/openleadr-rs/issues/53) plus the scoped first step [#525](https://github.com/OpenLEADR/openleadr-rs/pull/525). The HCA dimensions below are **audit axes**, not new upstream user stories. Status keys: V = verified by executed test; P = partially covered/code present but not E2E verified; N = unimplemented; B = blocked; NA = not applicable with reason. No V is assigned from source review alone.

| Story | Function | State | Integration | Security | Scale | Maintainability | Observability | Testing | User value | External compatibility |
|---|---|---|---|---|---|---|---|---|---|---|
| US53-01 Program | P | P | B | P | B | P | N | B | B | B |
| US53-02 Event | P | P | B | P | B | P | N | B | B | B |
| US53-03 URL/credentials | P | NA | B | P | NA | P | N | B | B | P |
| US53-04 serialization | P | P | B | P | P | P | N | B | B | P |
| US53-05 cleanup | P | N | B | P | B | P | P | B | B | B |
| US53-06 implementation-neutral fixtures | P | P | B | P | B | P | N | B | B | B |
| US53-07 VEN/Resource regressions | P | P | B | P | NA | P | N | B | B | P |
| PR525-01 configuration seam | P | NA | B | P | NA | P | N | B | B | P |

NA for credentials state means no persistent state is required of the configuration seam itself. NA for scale of configuration and regression preservation means no independent throughput target was specified; this does **not** waive load-related integration concerns. A runtime/real VTN trace is required to upgrade the remaining dimensions to V.

### Cross-story dependency and regression edges

`US53-03 credentials + URL -> US53-01 Program, US53-02 Event -> US53-05 cleanup -> US53-06 portable fixtures -> US53-07 existing regression -> third-party evidence`.
`US53-04 serialization` applies to all mutating test families and shared VTN environments.
`PR525-01` is kept isolated from this fork's stricter credential policy: compatibility is an explicit upstream contract, not a silently removed default.

### Mature external tooling comparison

- Existing dependency `serial_test = 3.4.0` supports cross-process file locks via its `file_locks` feature and `#[file_serial(key)]`. Applied to the two destructive probe binaries with the same key. Avoids inventing a custom lock service. Source: https://docs.rs/serial_test/3.5.0/serial_test/attr.file_serial.html
- `cargo-nextest` also offers `test-groups` with `max-threads = 1`; this is an alternative within a single nextest invocation, not a distributed lock. Source: https://www.nexte.st/docs/configuration/test-groups/
- The OpenADR Alliance has its own authorized conformance/certification process; these integration probes are **not** official certification. Source: https://www.openadr.org/openadr-3-certification

### Latest actual change, evidence and limitations

- P0/HCA serialization enhancement (source committed): workspace `Cargo.toml` enables `serial_test/file_locks`; both `external_vtn_program_crud.rs` and `external_vtn_event_crud.rs` use `#[file_serial(openleadr_external_vtn)]` rather than `#[serial]`.
- This addresses cooperating test binaries **on one shared filesystem**, not separate machines, unrelated processes, or crashed remote resources. It does not imply exclusive control of the external VTN.
- **Test status: NOT EXECUTED.** A check in the available execution container found no `cargo` / `rustc` in PATH. Full Cargo compilation, behavior tests and external VTN E2E remain B.
- **Independent falsification gates:** (a) launch Program and Event binaries concurrently sharing a temp directory and show mutual exclusion; (b) run both against a disposable VTN and verify not-found after delete; (c) interrupt after creation and recover using durable record; (d) run existing VEN/Resource tests to expose regression; (e) test against an independent implementation.
- **DEF-03 status:** PARTIAL CODE FIX; NOT VERIFIED CLOSED. Other-machine coordination still OPEN; dedicate the VTN or add a remotely coordinated lease if required.
- **Do not mark any User Story as Verified Closed on the strength of this change alone.**

### Resume precisely
1. Ensure Rust toolchain is available; run `cargo test -p openleadr-client --test external_mutation_guard`, `cargo test -p openleadr-client --tests --no-run` and record raw exits and logs.
2. Confirm the `file_serial` lock behavior with two **separate** `cargo test --test ... -- --ignored` invocations on the same host against a dedicated VTN. Do not assume different hosts share locks.
3. Only then run fault injection and cross-VTN interoperability against authorized isolated infrastructure; report failed cleanup as residual risk.

## HCA follow-up — uncertain Event creation response (2026-10-09)

**Cross-system counterexample**: A remote VTN may commit an Event but the client may lose the HTTP response. The former Event CRUD probe treated any failed CREATE response as if the Event did not exist, and proceeded to delete the parent Program. This confuses network uncertainty with transaction failure and risks hiding orphaned state.

**P0 source fix**: `external_vtn_event_crud.rs` now records `event_creation_uncertain` before consuming the result. On uncertain CREATE, it withholds parent deletion and emits the run-unique Program name/ID and error details for reconciliation. Commit: `f7fb5295a6a92ce6c86c18d7548dca1103cbddf7`.

**Residual gap**: This is a fail-safe response, not automatic reconciliation. A durable pre-CREATE journal and remote lookup by run-specific names, retry-safe cleanup, and crash/failure injection are still required. Status **PARTIAL / TEST BLOCKED**. Neither vertical nor horizontal Verified Closed is justified.

**Mature dependency cross-check**: `serial_test::file_serial` is documented under feature `file_locks`, with a shared key giving file-backed serialization for cooperating tests. See https://docs.rs/serial_test/latest/serial_test/attr.file_serial.html . Not a distributed lease across hosts.

**Runtime evidence**: Local container check 2026-10-09: neither `cargo` nor `rustc` found on PATH; no compilation or external-service E2E test was executed. Do not claim test success.

**Next concrete execution**: run Cargo check with the latest branch, then inject a fault where the server persists an Event but drops its POST response; verify test reports uncertainty and retains the Program for recovery. Separately verify normal delete path and no regressions.

**HCA impact**: US53-02 Event state/abnormal control flow improved in code only; US53-05 error recovery still PARTIAL; US53-04 cross-machine serialization still BLOCKED. DEF-08 = P0 ambiguous remote Event CREATE response, source mitigation committed, independent verification outstanding.
