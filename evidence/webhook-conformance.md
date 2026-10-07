# WEBHOOK conformance evidence

Status: **prepared, not yet executed in GitHub Actions**

This evidence lane is intentionally separate from the implementation patch in
`fix/notifiers-webhook-binding`.

## Claim under test

OpenADR 3.1.0 requires `GET /notifiers` to include the `WEBHOOK` binding key.

This lane tests only notifier **discovery conformance**. It does not claim that
webhook delivery, retry, authentication, or callback behavior is conformant.

## Normative provenance

- Public specification mirror: `grid-coordination/openadr3-specification`
- Revision: `17b91725e0f07203574ddc946e28def31cb11e44`
- OpenADR version: `3.1.0`
- `3.1.0/openadr3.yaml`: `WEBHOOK` is listed as required in the notifier response schema.
- `doc/OpenADR3 Object Operation Notifications via Additional Protocols.md`:
  the `WEBHOOK` notifier binding key MUST be provided by the VTN.

## Independent executable check

- Suite: `hupe1980/openadr`
- Revision: `fd57b1d1915394cdd7024b6406fa14ee85841bc4`
- Check ID: `notifiers-webhook-key`
- Classification: `Severity::Required`
- Suite methodology: normative sentences are turned into requests and assertions.

## Implementation under test

- Repository: `hippoley/openleadr-rs`
- Patch branch: `fix/notifiers-webhook-binding`
- Evidence branch: `evidence/webhook-conformance-rerun`

The patch:
- adds `WEBHOOK` to `NotifiersResponse`;
- returns `WEBHOOK: true` from notifier discovery;
- adds a focused serialization regression test.

## Reproduction

The workflow builds the patched VTN image and runs the independent peer harness
with:

```text
OPENADR_PEER_IMAGE=openleadr-webhook-fix:local
OPENADR_INTEROP_JSON=../openleadr-webhook-conformance.json
cargo test --all-features --test interop -- --ignored --nocapture
```

Expected evidence is the generated JSON report containing the
`notifiers-webhook-key` finding.

## Evidence state

- Known prior independent observation: OpenLEADR failed the required
  `notifiers-webhook-key` check.
- Patched rerun: **not yet observed**.
- PASS: **not claimed**.
- GitHub Actions run for this evidence branch: **not yet observed**.

A future PASS supports only this claim:

> the patched implementation advertises the required `WEBHOOK` notifier
> binding under the pinned independent check and pinned OpenADR 3.1.0
> normative provenance.

It does **not** establish end-to-end webhook delivery conformance.
