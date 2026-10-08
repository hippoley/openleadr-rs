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

## Attribution boundary

A matching read-back is deliberately not treated as proof that the tested action caused
the observed state. The state may already have matched before the request, or another
actor may have produced the same mutation.

Schema v0.4 therefore separates `effect-observed` from stronger integration claims.
The stronger claims require a pre-action observation and bounded attribution evidence.
The example artifact intentionally demonstrates the important negative case:
`matched-but-unattributed`. Its read-back matches, but its claim ceiling remains
`effect-observed`.

This is an auditability rule, not a claim of general causal identification. Protocols
that expose stronger mutation/correlation identifiers can record them as additional
evidence; protocols that do not must not manufacture attribution from timing alone.

### Reusable negative conformance case

A verifier can reuse the following invariant without adopting this repository's schema:

- given a matching post-action external observation,
- when no pre-action observation was captured and no target-system operation correlation exists,
- then the effect may be reported as observed, but attribution remains unestablished,
- and the verifier must reject promotion to an interoperability-level claim.

This is the `matched-but-unattributed` case. Its value is the negative boundary: a
verifier that promotes this case is overclaiming what its evidence establishes.

### Prior-art alignment

This boundary should not be presented as a novel causal mechanism. Existing verification
patterns already use a pre-action baseline plus a post-action delta to distinguish a
run-scoped state change from ambient state, and pair that delta with an action-specific
tag or equivalent scoping when concurrent writers are possible.

The contribution exercised here is narrower: applying that verification discipline to
an independently deployed OpenADR VTN and bounding the interoperability claim when the
protocol or deployment does not expose enough correlation evidence. The useful output
is therefore protocol-level conformance evidence and counterexamples, not a new causal
inference primitive.

### OpenADR assurance profile (draft)

This work is also not a replacement for an OpenADR specification conformance suite.
A black-box conformance suite answers whether a VTN behaves as required by cited OpenADR
clauses. This profile asks a different question: given the observations an OpenADR client
can obtain from that VTN, what state-change claim can an autonomous caller independently
support?

Initial capability mapping:

| OpenADR observation | What it supports | What it does not establish |
| --- | --- | --- |
| successful POST/PUT/DELETE response | request accepted at the VTN API boundary | externally persistent effect or attribution |
| VTN-assigned object ID | stable identity for subsequent reads of that object | identity of the actor that caused a later state |
| created/modification timestamps | server-reported temporal metadata | exclusive causation by this test action |
| read-after-write matching expected fields | externally observable post-state | that the post-state differed from the pre-state |
| pre-action read plus post-action read | a state delta within the observation window | exclusion of a concurrent writer |
| not-found after delete | deletion is externally observable at read time | which actor caused deletion without stronger correlation |
| independently deployed VTN | observation crosses the client implementation boundary | independent causal attribution by itself |

The profile should be revised from actual independent-VTN runs and from the normative
OpenADR 3.x surface. If a deployment exposes stronger operation correlation outside the
base protocol, that evidence must be identified as deployment-specific rather than
silently attributed to OpenADR itself.

### Cross-protocol pressure test: Kubernetes

The questions above are not specific to OpenADR. As a pressure test, Kubernetes exposes
a materially richer native observation surface: object `uid` identifies an object,
`resourceVersion` supports change detection and optimistic concurrency,
`metadata.generation` identifies a desired-state generation, and many controller-managed
statuses expose `observedGeneration` to say which desired-state generation the controller
has observed.

That produces a different assurance ladder from OpenADR:

| Kubernetes observation | Narrow supported statement | Remaining gap |
| --- | --- | --- |
| API mutation succeeds | API server accepted/persisted an object mutation | controller or workload effect |
| resourceVersion changes | this API object changed | which higher-level effect resulted |
| generation advances | desired specification changed | controller has observed that generation |
| status.observedGeneration catches up | controller reports status based on that desired generation | workload/external effect may still lag or fail |
| Ready/Available-style condition for the same generation | controller/runtime reports a stronger operational post-condition | end-user or physical-world outcome may remain outside Kubernetes |

The reusable method is therefore not a common field schema. It is to identify each
protocol's native observation and correlation primitives, then stop the claim at the
first boundary the protocol cannot independently bridge. A second protocol producing a
different ladder is evidence that this is a profiling method rather than an OpenADR-only
taxonomy.

### From assurance boundary to conformance oracle

Gateway API issue #4303 provides a useful pressure test for turning a boundary into a
conformance obligation. Multiple implementations can accept two conflicting HTTPRoutes
while only one is effective in the dataplane. For the deliberately narrow case where two
routes are identical at the conflict-relevant surface and protocol precedence selects a
deterministic single winner, a useful implementation-neutral oracle is:

1. create both routes against the same listener;
2. wait until status has converged for their current generations;
3. verify traffic resolves only to the precedence winner;
4. require the losing route to expose at least one machine-detectable non-success state
   for that parent; and
5. reject the result if both routes remain indistinguishable as successful while only
   one can ever receive traffic.

The oracle intentionally does not choose between `Accepted=False` and
`Programmed=False`; that is a protocol-semantics decision for Gateway API. The reusable
infrastructure step is earlier: derive a negative oracle from an observed assurance gap,
then let the protocol define the exact status vocabulary that satisfies it.

This suggests a minimal pipeline worth validating before creating a standalone project:

`protocol evidence surface -> unsupported stronger claim -> minimal counterexample ->
implementation-neutral oracle -> protocol-specific conformance probe`.

## Evidence checklist

- [ ] `cargo fmt --check` and `cargo check -p openleadr-client --tests` pass
- [ ] Both focused commands pass against an independently deployed VTN
- [ ] Confirm all created test resources are removed, including on failure
- [ ] Attach redacted logs and exact source commit
- [ ] Obtain independent reviewer feedback and link the upstream PR

Do not commit credentials or tokens to the repository.
