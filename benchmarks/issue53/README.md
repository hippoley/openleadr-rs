# Issue #53 interoperability benchmark — v1.0.0

**Status: dataset and scorer committed, NO external VTN execution evidence yet.** This benchmark is based on upstream [Issue #53](https://github.com/OpenLEADR/openleadr-rs/issues/53), not an independent standards certification scheme.

## Design decisions
- The dataset contains **16 distinct cases** tied to `US53-01` through `US53-07`; gates: local (5), external (5), fault (4), concurrency (2).
- The manifest intentionally separates *expected behavior* from *observed evidence*. Cases are specification-level requirements; they do not imply an executable scenario driver is available.
- Expected classes: `valid`, `invalid`, `success`, `recoverable`, `exclusive`, `isolated`. The meaning and remote fixture expectations must be finalized with actual VTN adapters before claiming conformance.
- Evidence must be a JSONL object with `id`, `status`, `runner`, `commit`, `exit_code`, `trace_uri`. Do not store credentials or private endpoint tokens in reports.
- `score.py` only validates evidence **claims** and coverage; it cannot verify authenticity of traces, match a request to its protocol semantics, or prove the endpoint was a third-party VTN. `verified_closed` deliberately stays `false`.
- `ignored`, `skipped`, missing results, unknown IDs and missing traces never count as passing. An invalid affirmative claim raises a scoring failure; unknown/duplicate evidence IDs fail the manifest.
- Run `python3 benchmarks/issue53/score.py` for schema/uniqueness checks; `python3 -m unittest discover -s benchmarks/issue53 -p 'test_*.py'` for scorer negative tests.
- For supplied evidence: `python3 benchmarks/issue53/score.py path/to/results.jsonl`. **Never** treat a zero result from the scorer as VTN conformance: it only means the evidence report's shape was accepted.
- CI checks the manifest and scoring contract on every push to this branch but does **not** run destructive tests. External mutation tests are ignored and require a disposable, explicitly authorized, dedicated VTN.

## Data splits and leakage prevention
The four `gate` values represent task families, *not* train/validation/test statistical splits. Keep resource names and credentials out of the dataset. Record the endpoint implementation and version, Cargo binary version, Git commit SHA, OS, timestamps, random seed if relevant, resource IDs, request/response redacted trace and cleanup outcome in separate artifacts; never insert these into this static manifest. Use distinct VTN implementations (not just two URLs of the same implementation) for genuine cross-vendor coverage.

## Acceptance and prioritization
1. P0: compile + local manifest tests; run client Program/Event tests without local PostgreSQL; verify cleanup and fault injection.
2. P0: verify both cross-process serialization and remote-host isolation scope; prove parent/child restoration after timeout or crash.
3. P1: test at least two independent VTN implementations and role combinations with redacted traces.
4. P2: measure latency distribution, resource cleanup time and failure rates with enough repeated runs for confidence intervals; publish run configuration and raw artifacts.

**Known missing pieces:** no automated per-case driver, no successful real-VTN runs, no cross-implementation equivalence oracle, and no evidence provenance signature. All story gates remain NOT Verified Closed.

## Cross-manifest integrity audit (2026-10-09)

The repository currently retains **two non-equivalent 16-case datasets**: `cases.json` (B001–B016, with executor/status metadata) and `cases.jsonl` (named scenario definitions and evidence scoring). Treating their totals as 32 independent passed tests or aligning rows by position would be a false result. `crosswalk.json` records explicitly non-equivalent tracing relations; `audit_crosswalk.py` now checks every canonical ID, unknown references, collisions, and orphan scenarios. CI invokes it.

Remote source-level crosswalk evaluation found **3 canonical unmapped cases** (B008 journal durability, B009 duplicate journal rejection, B016 denied-role test) and **3 secondary unmapped cases** (embedded-secret URL rejection, Program list, Event list). The post-correction mapping has no many-to-one references. These are **coverage reconciliation gaps**, not failed live VTN test outcomes.

Run `python3 benchmarks/issue53/audit_crosswalk.py` to see these gaps. The script deliberately exposes `joint_pass_count: null` and `joint_verified_closed: false`: a relationship between cases does not authorize aggregating or deduplicating real execution evidence. Next priority: establish one canonical, executable, versioned case schema and per-case runner mappings with a migration test before removing either legacy manifest. No Rust or external VTN pass is claimed here.
