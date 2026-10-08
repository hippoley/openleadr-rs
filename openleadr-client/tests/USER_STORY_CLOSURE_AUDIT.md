# User-story closure audit — 2026-10-08

Scope: `hippoley/openleadr-rs`, branch `test/independent-vtn-seam`. This is a bounded code-and-document inspection, **not** a claim of full repository traversal, successful CI, or third-party VTN interoperability.

## Product identity

The upstream README describes an OpenADR 3.1 Rust VEN client and VTN server. The OpenADR external-VTN seam is the only directly relevant local delivery story. Gateway API / A2A conformance work is research and upstream-adoption preparation, not a shipped feature of this Rust product. Do not conflate upstream README badges or upstream OpenADR Alliance test results with this branch's results.

## User stories and evidence-based verdicts

| Story | Acceptance condition | Inspected evidence | Verdict |
| --- | --- | --- | --- |
| US-01 external target selection | Program/Event CRUD HTTP requests target configured external VTN | `EXTERNAL_VTN.md` and focused test entrypoints; common setup implementation not inspected in this audit | PARTIAL; must inspect `tests/common` and execute against a third-party VTN |
| US-02 role credentials | BL credentials used for write operations; VEN role not silently promoted | Environment contract and `common::setup::<BusinessLogic>(AuthRole::Bl)` callers | PARTIAL; independent negative auth tests missing from inspected evidence |
| US-03 Program CRUD | create, duplicate conflict, read, update, delete, not-found | `program.rs::program_crud` | CODE PRESENT; no verified independent-VTN execution |
| US-04 Event CRUD | create under program, read, update, delete, not-found | `event.rs::event_crud` | CODE PRESENT; no verified independent-VTN execution |
| US-05 failure cleanup | all created IDs deleted and independently checked after assertion failure/panic | Tests delete on success only; `EXTERNAL_VTN.md` acknowledges limitation | OPEN / HIGH |
| US-06 test isolation | concurrent test binaries/runners do not delete each other's objects | UUID names and serial tests; no cross-process lock | PARTIAL |
| US-07 independent reproduction | target implementation/version, exact commit, redacted logs, command, exits, observed effect | JSON Schema and documentation | CONTRACT PRESENT; actual independent artifact NOT VERIFIED |
| US-08 claim ceiling | failed tests, non-independent deployment, unverified effect, or residual resources cannot produce strong interoperability claim | JSON Schema v0.4 and new exit-code constraint | IMPROVED; schema regression tests and actual artifact validation still needed |
| US-09 assurance contract CI | validator tests, profile validation and compiler run on PR | Added `assurance-contracts` job to `.github/workflows/checks.yml` | CODE WIRED; CI run NOT VERIFIED |
| US-10 mixed-scope safety | unresolved Gateway status semantics cannot become reportable normative test | validator + compiler readiness gate | CODE PRESENT; runtime CI pending |
| US-11 official Gateway adoption | native conformance PR reviewed/merged | #4303 draft only, normative blocker; prior write attempts 403 | HOLD; NOT ADOPTED |
| US-12 A2A adoption | upstream accepted/merged test or externally consumed artifact | No A2A fork or contribution from this branch | NOT STARTED HERE; do not add unrelated code to OpenADR repo |
| US-13 published identity | independent reviewer can verify contribution via merge, release or report | local commits only | NOT YET |
| US-14 full Rust regression | fmt, clippy, workspace tests, SQLx and external smoke are green | existing Rust CI workflow; no run evidence in this audit | NOT VERIFIED |
| US-15 feature scope honesty | no claim that unsupported webhook/subscription, independent VEN authorization, or all OpenADR cases pass | upstream README and `EXTERNAL_VTN.md` state limitations | DOCUMENTED; runtime coverage still incomplete |

## Stop-the-line gaps

1. **P0: No verified third-party VTN execution**. A contract, test function, or schema does not establish interoperability.
2. **P0: No failure-path cleanup**. Panic/assertion failure can leave resources on the external VTN. A disposable dedicated environment is required until cleanup-on-failure is implemented and tested.
3. **P0: Claim integrity**. Strong evidence claims must fail if any test exits nonzero; added schema constraint, but negative fixture tests are still needed.
4. **P1: CI trust**. Assurance Python checks were not wired into the inspected existing CI; a job has now been added, but no CI run has been verified.
5. **P1: Role and isolation**. Negative VEN/BL permission cases and cross-run resource isolation are not established by the two focused CRUD tests.
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
