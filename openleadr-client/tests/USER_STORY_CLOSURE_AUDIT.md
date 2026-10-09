# User-story closure audit — 2026-10-08

Scope: `hippoley/openleadr-rs`, branch `test/independent-vtn-seam`. This is a bounded code-and-document inspection, **not** a claim of full repository traversal, successful CI, or third-party VTN interoperability.

## Product identity

The upstream README describes an OpenADR 3.1 Rust VEN client and VTN server. The OpenADR external-VTN seam is the only directly relevant local delivery story. Gateway API / A2A conformance work is research and upstream-adoption preparation, not a shipped feature of this Rust product. Do not conflate upstream README badges or upstream OpenADR Alliance test results with this branch's results.

## User stories and evidence-based verdicts

| Story | Acceptance condition | Inspected evidence | Verdict |
| --- | --- | --- | --- |
| US-01 external target selection | Program/Event CRUD HTTP requests target configured external VTN | `EXTERNAL_VTN.md` and focused test entrypoints; common setup implementation not inspected in this audit | PARTIAL; must inspect `tests/common` and execute against a third-party VTN |
| US-02 role credentials | BL credentials used for write operations; VEN role not silently promoted | strict external credentials fail closed; `ven_role_cannot_create_program` requires 401/403 and cleans any unexpected mutation | IMPLEMENTED; branch CI and independent-VTN execution required before VERIFIED |
| US-03 Program CRUD | create, duplicate conflict, read, update, delete, not-found | `program.rs::program_crud` | CODE PRESENT; no verified independent-VTN execution |
| US-04 Event CRUD | create under program, read, update, delete, not-found | `event.rs::event_crud` | CODE PRESENT; no verified independent-VTN execution |
| US-05 failure cleanup | all created IDs deleted and independently checked after assertion failure/panic | focused CRUD tests now catch unwind, retain created IDs, retry deletion, and surface cleanup errors | IMPLEMENTED; fault-injection and independent-VTN verification still required |
| US-06 test isolation | concurrent test binaries/runners do not delete each other's objects | UUID-owned names plus `concurrent_program_runs_do_not_cross_delete`; runner A deletes A and proves B survives before deleting B | IMPLEMENTED: Program cleanup ownership probe plus `run_external_vtn_parallel_isolation.sh` launches two OS processes against the same external target; branch CI syntax check and real independent-VTN parallel execution remain required before VERIFIED |
| US-07 independent reproduction | target implementation/version, exact commit, redacted logs, command, exits, observed effect | JSON Schema and documentation | CONTRACT PRESENT; actual independent artifact NOT VERIFIED |
| US-08 claim ceiling | failed tests, non-independent deployment, unverified effect, or residual resources cannot produce strong interoperability claim | JSON Schema v0.9 with paired Program/Event success, paired fault-injection cleanup, operation correlation, and retained-log/observation digests | CI-VERIFIED CONTRACT; actual independent artifact still needed |
| US-09 assurance contract CI | validator tests, profile validation and compiler run on PR | Added `assurance-contracts` job to `.github/workflows/checks.yml` | CI VERIFIED; assurance job and repository checks have passed on this branch |
| US-10 mixed-scope safety | unresolved Gateway status semantics cannot become reportable normative test | validator/compiler gate plus `test_assurance_profile_boundaries.py`; CI discovery broadened to execute the boundary regression | IMPLEMENTED; latest CI required before VERIFIED |
| US-11 official Gateway adoption | native conformance PR reviewed/merged | #4303 draft only, normative blocker; prior write attempts 403 | HOLD; NOT ADOPTED |
| US-12 A2A adoption | upstream accepted/merged test or externally consumed artifact | No A2A fork or contribution from this branch | NOT STARTED HERE; do not add unrelated code to OpenADR repo |
| US-13 published identity | independent reviewer can verify contribution via merge, release or report | local commits only | NOT YET |
| US-14 full Rust regression | fmt, clippy, workspace tests, SQLx and external smoke are green | GitHub Actions `Checks` and `Rust docs` succeeded through the failure-cleanup implementation commit `c4f4b7e` | VERIFIED FOR BRANCH; external smoke remains separate |
| US-15 feature scope honesty | no claim that unsupported webhook/subscription, independent VEN authorization, or all OpenADR cases pass | upstream README and `EXTERNAL_VTN.md` state limitations | DOCUMENTED; runtime coverage still incomplete |

## Stop-the-line gaps

1. **P0: No verified third-party VTN execution**. A contract, test function, schema, or operator-entered digest does not establish interoperability; an independently deployed target and retained evidence are still required.
2. **P0: Failure cleanup lacks fault-injection proof**. Cleanup-on-unwind is implemented and repository CI passes, but no deliberately injected mid-CRUD failure has yet demonstrated zero residual resources on an independent VTN.
3. **P0: Claim integrity beyond schema**. Strong-claim regressions cover failed tests, missing correlation, partial CRUD/fault coverage, cleanup residue, and missing evidence digests. The latest v0.7 commit still requires CI completion, and a real independent artifact must exercise the same ceiling.
4. **P1: CI trust**. Assurance Python checks and repository Rust checks are now verified on branch CI; external-VTN smoke remains intentionally outside ordinary CI until credentials/target are available.
5. **P1: Role and isolation**. Negative VEN authorization and Program cleanup ownership now have executable probes; independent-VTN execution and true simultaneous multi-process isolation remain unverified.
6. **P1: Provenance**. The upstream OpenLEADR badges, Alliance test screenshot, and sponsor claims describe the upstream project, not proof of this fork's branch.
7. **P2: Research isolation**. Keep Gateway #4303 as HOLD; avoid growing Gateway/A2A schemas inside the OpenADR production surface.

## Required proof before closing the external-VTN user story

- Run `cargo fmt --check`, `cargo check -p openleadr-client --tests`, and focused CRUD commands on the exact commit.
- Use a disposable independently deployed OpenADR 3.1 VTN; record implementation/version, runner OS/Rust version, redacted command output and SHA-256 digest.
- Capture pre/post effect observations, run-scoped IDs, and cleanup verification (including deliberately injected failure).
- Validate the final evidence artifact against `external-vtn-evidence.schema.json` and reject any stronger claim than the evidence supports.
- Get a third party to reproduce or review the exact result; only then consider an upstream PR and external-adoption credit.

## Capital allocation

Keep this branch focused on closing OpenADR interoperability and evidence truthfulness. Preserve the Gateway #4303 native transplant as a recoverable option until normative semantics change. Evaluate A2A conformance in its own upstream repository, not by adding unrelated test scaffolding here. External adoption stays **0** until an independently verifiable upstream incorporation, required test, or explicit architectural dependency exists.

## Defect ledger

| ID | Severity | User story | Defect | Resolution | Verification |
| --- | --- | --- | --- | --- | --- |
| D-001 | P0 | US-08 | v0.9 positive fixture omitted required Program fault `log_sha256` and added a forbidden cleanup property, so contract tests could fail for fixture drift rather than claim semantics | fixed in `e50b0fc`; template/schema parity regression added | latest branch CI pending |
| D-002 | P0 | US-07/08 | evidence template pre-declared `deployment=independent` before an actual run | changed to `unknown` in `57328af`; regression proves untouched template cannot be promoted to a strong claim | latest branch CI pending |
| D-003 | P1 | US-06 | UUID ownership alone did not prove multi-process isolation | ownership regression plus two-process external runner added | local contract present; independent execution pending |
| D-004 | P1 | US-10 | mixed-scope fail-closed behavior existed in validator/compiler but had no dedicated discovered regression test | added profile-boundary tests and widened CI discovery pattern | latest branch CI pending |

