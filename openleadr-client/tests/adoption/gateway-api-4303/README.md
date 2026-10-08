# Gateway API #4303 transplant draft

Purpose: minimize time from upstream semantic decision to a native conformance PR.

Status: **spec-decision-required**. This directory is not a claim that Gateway API currently requires a particular losing Route condition.

Upstream target:
- `conformance/tests/httproute-exact-conflict.go`
- `conformance/tests/httproute-exact-conflict.yaml`

Bounded scope:
- exact conflict only;
- deterministic precedence only; derive the expected winner from actual creationTimestamp, then namespace/name on timestamp ties;
- no partial header/query/rule conflict semantics;
- live dataplane assertion for the winner;
- final upstream test should also delete the winner and prove the former loser becomes effective.

Normative blocker: kubernetes-sigs/gateway-api#4303 must settle the machine-visible status of the deterministic loser before the placeholder status assertion can be replaced.

## Allocation checkpoint (2026-10-08)

Status: **HOLD, not abandoned**.

Reason: the transplant is blocked on an upstream normative decision for the losing Route condition/reason. Additional local implementation before that decision would create speculative semantics rather than adoption value.

Resume only when at least one of these changes externally:
- kubernetes-sigs/gateway-api#4303 settles the machine-visible loser semantics;
- a maintainer asks for a concrete conformance test/manifest;
- a related normative PR makes the expected condition/reason reviewable.

Do not resume merely because more implementations reproduce the same indistinguishable-success behavior; more witnesses no longer remove the normative blocker.

While held, higher-value conformance work should be pursued at active upstream validation surfaces rather than adding local abstractions here.
