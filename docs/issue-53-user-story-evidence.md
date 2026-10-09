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

## HCA iteration — symmetric Program CREATE uncertainty (2026-10-09)

- Independent cross-story review found the Program test assumed an error response implied CREATE did not happen; the Event test had already addressed the same ambiguity.
- **DEF-09 P0, source mitigation committed**: Program CREATE errors now report the run-unique name and explicitly require VTN reconciliation rather than pretending no remote resource was created. Commit `70d7d71408088f7b4c935ed80ac5c041df13da06`.
- This is *not* crash-safe journaling, automatic cleanup, or a passed integration test. An error may happen after remote commit; humans must still locate and remove the named resource. Vertical status: PARTIAL. Horizontal state/recovery: PARTIAL, E2E: BLOCKED.
- **Independent falsification**: inject a VTN that accepts Program POST then drops its response; verify the diagnostic includes the unique name; find and delete the resource by name. Repeat Event and Program workflows after real Cargo compilation.
- **Runtime/toolchain check**: no `cargo` or `rustc` resolved in the available execution container on 2026-10-09; actual compile and run results cannot be asserted.
- Next P0 sequence: install or use a runner with Rust, compile all external test binaries, fix any API/compiler errors, then implement a durable pre-CREATE journal plus crash recovery and validate against dedicated VTN. Keep upstream #525 unchanged.

## HCA iteration — durable pre-CREATE recovery breadcrumbs (2026-10-09)

- **DEF-02, source partially mitigated:** added `external_recovery_journal.rs` and wired it into both external Program and Event CRUD probes. Requires a pre-existing private directory at `OPENLEADR_RS_RECOVERY_DIR`. Before any remote CREATE the test creates a unique append-only local log with `create_new`, syncs the file and parent directory, then records returned IDs and `CLEANUP_VERIFIED` after remote not-found checks. Relevant commits `010896dcb611656ec847e4617839a38809c05991`, `ad685316f1da4bf240a6b9c9156f9416742c36a6`, `fa66755fd335125aa8b5d7fd457a5c9322424715`.
- **Operational contract:** only run mutation probes on an isolated disposable VTN; specify `OPENLEADR_RS_RECOVERY_DIR` on a persistent private filesystem. Files contain the VTN URL, resource name and returned IDs, never credentials. Logs remain after cleanup for audit.
- **Critical residual P0:** the journal is a breadcrumb, **not** automatic reconciliation, a replay engine, or proof of atomic crash durability across all operating systems/filesystems. A remote POST may complete before an ID is returned. Users must reconcile orphan resource names manually. Directory fsync platform behavior, filesystem permissions, and power-loss consistency need tests. A startup orphan scanner/recovery process is not implemented.
- **Independent test results:** none. The current container has no `cargo` / `rustc` command; no Rust compile, dedicated VTN E2E, injection or rollback outcome has been asserted. Story status remains PARTIAL / BLOCKED, not Verified Closed.
- **HCA dependencies:** US53-01/02 now emit local recovery evidence; US53-05 remains PARTIAL, US53-04 and US53-06 incomplete. `#525` is unchanged. For next execution: compile all test binaries, confirm journal files exist before POST using a server-side probe, kill process after CREATE, and independently reconcile and delete survivors; repeat across platforms before acceptance.

## Independent CI execution gate — 2026-10-09

- **New repository workflow:** `.github/workflows/external-vtn-validation.yml` enables a Rust toolchain and runs `cargo test -p openleadr-client --tests --no-run`, then non-destructive mutation-guard tests and URL validation tests. Source commit: `30915149fc33c33110433100169ef4f59514da4e`.
- **External validation evidence:** https://github.com/hippoley/openleadr-rs/actions/runs/37892126901 . On inspection, checkout and Rust toolchain setup had completed successfully, but the compile job was still in progress. **Status = CI_RUNNING, NOT VERIFIED**, not a pass claim.
- **HCA cross-story impact:** compilation gate applies to US53-01/02/03/04/05/06/07; the guard regression gate applies to US53-03/04/05. CI explicitly excludes ignored destructive remote VTN tests, which remain BLOCKED pending isolated service access.
- **Critical acceptance boundary:** green local/CI tests do not prove external VTN behavior, post-crash reconciliation or cross-host serialization. Do not promote any story to Verified Closed without independent E2E evidence.
- **Resume:** inspect the latest actual CI run on this branch and its failing job logs, fix compiler/test failures, record exact run IDs and statuses. Then run controlled external VTN and failure-injection acceptance.

## Actual CI compiler counterexample and repair (2026-10-09)

- **Independent failed run:** https://github.com/hippoley/openleadr-rs/actions/runs/37892209559 (conclusion FAILURE, Rust exit 101, compilation stage). Its job log shows `error[E0061]` in `openleadr-client/tests/external_vtn_readonly.rs:65`: `Client::get_event_list` needs `Option<&ProgramId>` followed by `Filter`, but probe supplied only `Filter`.
- **P0 compiler repair committed:** `37012bade30ceaed33d9f94e4081c44fb441ec12` changes `get_event_list(Filter::none())` to `get_event_list(None, Filter::none())` following the compiler's API signature. This preserves a global Event list request without a per-Program filter.
- **Retest run:** https://github.com/hippoley/openleadr-rs/actions/runs/37892618922 was QUEUED upon inspection; status **RETEST_PENDING**, no pass claims.
- **HCA linkage:** US53-02 external Event list functional correctness, test compilation, client API compatibility, and regression coverage. DEF-10 = P0 incorrect get_event_list signature; fixed in source, independent validation pending.
- **Remaining limitations:** workflow may still fail on additional errors; normal tests do not exercise a real VTN, and even green CI cannot close US53-02/05 or #53. Reinspect the above CI run, extract exact new failures, fix and rerun. Do not label Verified Closed until required vertical and horizontal acceptance evidence exists.

## HCA independent verification — successful Rust CI (2026-10-09)

**Verified evidence**: [Run #37892618922](https://github.com/hippoley/openleadr-rs/actions/runs/37892618922) (commit `37012bade30ceaed33d9f94e4081c44fb441ec12`) and [Run #37892646476](https://github.com/hippoley/openleadr-rs/actions/runs/37892646476) (commit `84083e0211de5fdb885d46c260ce275850db669d`) both completed with GitHub Actions conclusion **success**. In the latter run, `cargo test -p openleadr-client --tests --no-run`, `cargo test -p openleadr-client --test external_mutation_guard`, and `cargo test -p openleadr-client --test external_vtn_readonly` each concluded **success** according to independent job steps.
- **DEF-10** (`get_event_list` wrong arity): **VERIFIED FIXED at CI compiler gate**. Narrow technical defect can be closed; this does not mean the entire US53-02 is Verified Closed.
- **US53-01/02/03** local compiler and pure validation gates now **VERIFIED** at commit `84083e0`, while real third-party behavior stays **BLOCKED**.
- **US53-04** file-lock code compiles, but independent cross-process overlap/fault-injection execution still required.
- **US53-05/06/07** E2E, recovery, and legacy regression criteria remain open.
- No ignored live-VTN mutation test was executed. No external interoperability or OpenADR official certification is claimed.

**Next executable entry**: prioritize disposable, authorized third-party VTN E2E + injected lost-response and failed-cleanup cases. Maintain a separate durable recovery journal and record deletion verification. Coordinate tests across hosts by isolated environments or an external lease; local file locking alone is insufficient.

**Double closure**: no complete original #53 User Story is marked `Verified Closed`. The isolated P0 compiler defect DEF-10 is confirmed fixed by CI.

## HCA follow-up: durable pre-CREATE intent markers (2026-10-09)

- Review of the existing `external_recovery_journal.rs` showed it opens and syncs a unique journal before operations, but earlier clients only recorded successful CREATE results. A crash or lost response after POST could not be distinguished from a failure before attempting the POST.
- **Source improvement:** Program CRUD now syncs `PROGRAM_CREATE_ATTEMPT` before the Program POST (`4865c39c2269afc408722526bff6a02b6ef73612`). Event CRUD syncs `PARENT_CREATE_ATTEMPT` before parent Program POST and `EVENT_CREATE_ATTEMPT` before child Event POST (`ac769bc48e8f163f7043210ce73ef5c7e326b6c1`). The journal records use the existing `sync_all` implementation; no new dependency.
- **Independent acceptance:** CI run https://github.com/hippoley/openleadr-rs/actions/runs/37893644028 was queued at source inspection. Status `IMPLEMENTED_UNVERIFIED`; no crash/fault injection, journal replay or third-party VTN execution has been demonstrated.
- **P0 remaining:** replay/reconcile the latest journal state with remote VTN before deletion; ensure idempotency and operator evidence. Note filesystem journal durability depends on reliable underlying storage; fsync does not imply remote operation atomicity.
- **Scope:** improvement supports US53-05 (failed-test state preservation) but does not redefine Issue #53 or imply certification.

## HCA anti-false-positive journal test (2026-10-09)

- **Previous baseline:** Actions runs [37893637136](https://github.com/hippoley/openleadr-rs/actions/runs/37893637136), [37893644028](https://github.com/hippoley/openleadr-rs/actions/runs/37893644028), [37893675207](https://github.com/hippoley/openleadr-rs/actions/runs/37893675207) all concluded SUCCESS for the pre-CREATE markers (compile plus non-destructive guard/URL tests). No real VTN was contacted.
- **New independent falsification:** prior `external_recovery_journal.rs` unsafe-name test could pass solely because `OPENLEADR_RS_RECOVERY_DIR` was unset, never reaching the filename validation branch. Updated source extracts `begin_in(dir,kind,name,url)` and tests against actual isolated temp directories. The replacement tests read persisted BEGIN/CREATE_ATTEMPT records, assert duplicate file refusal without truncation, reject traversal-like names, and reject absent directories. Commit `f1c78751c9d03999cc0eb892e8fbc3e9c4d3d74a`.
- **Status:** CODE COMMITTED, independent CI RUN PENDING at authoring; testing results must be read before claiming a pass. The helper intentionally stays local to the test integration module; no new production library.
- **HCA:** improves US53-05 test reliability, state persistence, observability, security. Still missing crash/replay recovery and real VTN E2E; no change to overall Verified Closed.

## Dataset and benchmark horizontal audit (2026-10-09)

- **Added source-traceable scenario manifest:** `benchmarks/issue53/cases.json` (16 scenarios covering issue #53 configuration, Program/Event lifecycle, durable journal, isolation, failure injection, regression and independent implementation). Every case explicitly starts `not_executed`; no synthetic benchmark score is asserted. Source commit `4748f69baea99f9947d733a7f60c9a2e72c80614`.
- **Anti-false-positive validator:** `benchmarks/issue53/validate.py` enforces unique case IDs, known story identifiers, polarity, mutation annotation, permitted outcomes, and requires independently identified run URL + commit before a pass/fail may be declared; negative selftests ensure duplicate/unsupported/false-pass records are rejected. Source `c116accbfd05fa22f0decb9a5a6d7a8d42d48b2a`.
- **CI integration:** validation was merged into the existing benchmark score workflow (not overwritten); commit `a382b7686ada2d982cbeda0724639be72770982b`, run https://github.com/hippoley/openleadr-rs/actions/runs/37895326319 in progress at review time.
- **Concurrent branch changes:** a separate `cases.jsonl` / `score.py` / `test_score.py` suite appeared in the same branch concurrently. Both formats currently coexist, with no verified semantic synchronization. **DEF-BENCH-01 P1**: reconcile a single canonical schema and derive other formats; do not double-count case numbers or issue completion.
- **External options:** OpenADR Alliance retains its own licensed official certification testing workflow (https://www.openadr.org/openadr-3-certification), separate from these engineering probes. Schemathesis (https://schemathesis.io/) can add OpenAPI-derived boundary/stateful tests when a disposable VTN is available, but no dependency is added here, and no live target was accessed.
- **Acceptance:** manifest validation alone cannot increase interoperability success rates. Only independent VTN execution, fault injection and verified cleanup may promote a case to executed pass. All issue #53 user stories remain unclosed.

## Issue 53 benchmark dataset v1.0.0 — 2026-10-09
- New `benchmarks/issue53/cases.jsonl`: 16 cases, unique IDs, four gates: local (5), external (5), fault (4), concurrency (2). Source: US53-01–07 from Issue #53.
- `score.py` and `test_score.py` implement a manifest check and independent false-pass assertions; `README.md` defines evidence contract and limitations. The existing external VTN CI now calls Python manifest and test checks.
- Remote GitHub fetch confirmed 16/16 unique case identifiers with required fields. Python scorer execution and Cargo build NOT witnessed here; no live third-party VTN run. Candidate result with supplied trace is never automatically treated as independently verified.
- HCA status: functional P, state P, integration B, security P, scalability N, maintainability P, observability P, testability P, user value B, external compatibility B. All stories remain NOT Verified Closed.
- BENCH-01 P0: no executable driver connecting dataset cases to real endpoints; BENCH-02 P0: no independent trace/semantic oracle; BENCH-03 P1: no cross-implementation run provenance; BENCH-04 P1: no repeated performance measurements. Next gate is actual Python CI success, followed by authenticated isolated VTN fault cases.

## Public GitHub Actions run evidence — 2026-10-09 (actual executed checks)

**Source of truth**: [GitHub Actions Run 37896311620](https://github.com/hippoley/openleadr-rs/actions/runs/37896311620), job `113708343983`, head commit `00f75d98fc79c80b60dc02d8062b95f35756f3d3`, conclusion **success**. This is an executed CI job, not a source-only inspection.

Job step outcomes retrieved from GitHub Actions: scenario metadata and false-pass assertions SUCCESS; crosswalk audit SUCCESS; JSONL scoring validation SUCCESS; Rust `cargo test -p openleadr-client --tests --no-run` SUCCESS; `external_mutation_guard` unit tests SUCCESS; `external_vtn_readonly` local tests SUCCESS.

Direct job-log observations:
- Benchmark manifest: `16 cases; {'pass': 0, 'not_executed': 16, 'fail': 0, 'blocked': 0}`.
- Python counterexample suite: `Ran 6 tests` (successful job step).
- Rust authorization guard: `3 passed; 0 failed; 0 ignored`.
- Rust read-only URL checks: `2 passed; 0 failed; 2 ignored` (the ignored tests are actual external-VTN requests, **NOT successes**).

**Acceptance interpretation**: The same commit has public evidence for compiling Rust test binaries and passing local benchmark/guard checks. This clears the former "no successful compilation evidence" blocker **for commit 00f75d98**, but does not establish compilation of later commits, actual remote VTN interoperability, recovery, role correctness, resource cleanup, or Issue #53 Verified Closed. All 16 benchmark scenario status fields remain `not_executed` in the canonical manifest. Independent VTN endpoint and authorized credentials are not available in this tool context.

**Next executable gate**: run opt-in Program/Event tests on a disposable independent VTN with authorized credentials; capture redacted request/response logs, created resource IDs, cleanup audit, and a GitHub Actions run tied to the exact tested SHA. Do not mutate shared/production systems. Compare with the upstream `program.rs` and `event.rs` legacy sqlx tests before closure.

**Note**: historical summaries saying "there is no Cargo compilation evidence" were correct at the time of those statements, but are superseded for this exact 2026-10-09 CI SHA. Avoid copying the superseded blocker into future summaries without checking Actions.

## Real upstream VTN network E2E gate (2026-10-09)

- **Source commit** `af91f6f4f9e938524c742d879e2a28991e703cf8`: adds `.github/workflows/upstream-vtn-e2e.yml`, a real upstream VTN process backed by an ephemeral PostgreSQL 18 service, the project's SQL migrations and fixture BL role, and **ignored live** Program/Event listing probes over the loopback HTTP server. No production or third-party VTN is contacted.
- **Public execution**: https://github.com/hippoley/openleadr-rs/actions/runs/37900349307 . Initial status QUEUED; **no pass or failure outcome yet** as of this ledger update.
- **Public evidence outputs:** the workflow uploads `vtn.log`, `readonly-e2e.log`, and `seed.log` as a 30-day GitHub Actions artifact, including when the job fails. The log greps require both `PROGRAM_LIST PASS` and `EVENT_LIST PASS` alongside Cargo exit code 0.
- **Vertical claim if green:** real upstream Rust VTN ↔ Rust VEN client authentication and list endpoints, with ephemeral local storage. Not evidence for third-party interoperability, mutation CRUD, cross-host isolation or crash recovery.
- **Residual critical gates:** inspect this run's first outcome, repair any real errors and rerun, then obtain **authorized independent third-party VTN** results. A public URL and run artifacts cannot substitute for evidence that a distinct vendor implementation was exercised.
- **US53-01/02/03 integration status:** E2E_RUN_QUEUED, no Verified Closed; **US53-05/06** remain incomplete.
