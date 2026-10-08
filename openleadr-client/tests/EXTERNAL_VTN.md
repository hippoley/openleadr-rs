# External VTN integration test contract (draft)

This branch is an experimental contribution toward [OpenLEADR #53](https://github.com/OpenLEADR/openleadr-rs/issues/53), not a claim of interoperability certification.

## Preconditions

- Rust toolchain satisfying the workspace MSRV (currently 1.91).
- A **running** OpenADR 3.1 VTN reachable from the test runner over HTTP(S).
- Pre-provisioned Business Logic credentials with Program/Event create, read, update and delete permissions.
- A dedicated disposable test environment. These tests create, update and delete resources.
- Any database required for compiling the in-tree `openleadr-vtn` dev dependency must be configured separately; using an external HTTP VTN does **not** currently remove all compile-time or SQLx dependencies.

## Environment

```sh
export OPENLEADR_RS_VTN_URL='https://vtn.example.test/'
export OPENLEADR_RS_BL_CLIENT_ID='<business-logic-client-id>'
export OPENLEADR_RS_BL_CLIENT_SECRET='<business-logic-client-secret>'
# Optional VEN role configuration for other role-aware callers:
export OPENLEADR_RS_VEN_CLIENT_ID='<ven-client-id>'
export OPENLEADR_RS_VEN_CLIENT_SECRET='<ven-client-secret>'
```

`OPENADR_VTN_URL` is a compatibility alias used only when `OPENLEADR_RS_VTN_URL` is absent. `OPENLEADR_RS_CLIENT_ID` and `OPENLEADR_RS_CLIENT_SECRET` remain compatibility fallbacks when role-specific credentials are absent. An unset credential may use an in-tree test default, which is unlikely to work against a third-party VTN; supply explicit credentials for external tests.

## Run the focused black-box tests

```sh
cargo test -p openleadr-client --test program program_crud -- --exact --nocapture
cargo test -p openleadr-client --test event event_crud -- --exact --nocapture
```

The tests use public client HTTP APIs for their CRUD assertions. They are marked `serial` to reduce collisions with other serial tests in the same test binary. This does **not** coordinate across separately invoked binaries or independent runners.

## What a successful run would demonstrate

- The configured VTN accepted the supplied Business Logic identity.
- Program and Event CRUD operations behaved as asserted by the client tests.
- HTTP requests were sent to the configured VTN URL rather than an in-process mock.

It would **not** prove full OpenADR compliance, VEN role authorization, all resource types, or interoperability with every VTN implementation.

## Known limitations before upstream submission

1. The focused Program and Event CRUD tests now use per-run UUID-based names and do not pre-delete similarly named resources. This reduces name collisions, but does not guarantee isolation from other test runners or resource cleanup after failures. Use a dedicated environment.
2. Cleanup occurs on the normal success path; an assertion failure or panic can leave test resources behind. A cleanup-on-failure design is still required.
3. Existing SQLx-backed integration tests are not all converted to remote-only tests. Run the focused commands above; a full `cargo test` may still require PostgreSQL.
4. No real third-party VTN run, CI result, or maintainer acceptance is asserted by this document. Record the VTN implementation/version, runner commit SHA, redacted configuration, command, exit code, and cleanup result before claiming independent reproducibility.

## Machine-readable evidence artifact

For a run that will be shared or cited, record the result against
`external-vtn-evidence.schema.json`. The schema deliberately separates the exact source
commit, independently deployed VTN identity/version, runner environment, per-test exit
codes and redacted-log digests, and post-run cleanup verification.

A result should use the narrowest supported claim. In particular, a passing command is
not certification, and a run against the in-tree VTN must not be labeled
`independent-vtn-crud`.

This gives reviewers and downstream automation a stable evidence shape without requiring
them to trust prose or screenshots.


### Effect verification, not just execution receipts

Version 0.2 of the evidence schema draws a deliberate boundary between evidence that a
request/test ran and evidence that the target VTN exposed the expected resulting state.
An `independent-vtn-crud` or `interoperability-candidate` claim therefore requires an
independently deployed VTN plus at least one verified effect observation (for example,
read-after-write or not-found-after-delete).

This is intentionally narrower than general-purpose agent evidence bundles: the goal here
is not to invent another trace/archive format, but to make a protocol integration claim
depend on an observable effect in the target system.

## Evidence checklist

- [ ] `cargo fmt --check` and `cargo check -p openleadr-client --tests` pass
- [ ] Both focused commands pass against an independently deployed VTN
- [ ] Confirm all created test resources are removed, including on failure
- [ ] Attach redacted logs and exact source commit
- [ ] Obtain independent reviewer feedback and link the upstream PR

Do not commit credentials or tokens to the repository.
