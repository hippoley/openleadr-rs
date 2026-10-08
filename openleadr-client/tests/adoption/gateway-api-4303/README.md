# Gateway API #4303 transplant draft

Purpose: minimize time from upstream semantic decision to a native conformance PR.

Status: **spec-decision-required**. This directory is not a claim that Gateway API currently requires a particular losing Route condition.

Upstream target:
- `conformance/tests/httproute-exact-conflict.go`
- `conformance/tests/httproute-exact-conflict.yaml`

Bounded scope:
- exact conflict only;
- deterministic precedence only;
- no partial header/query/rule conflict semantics;
- live dataplane assertion for the winner;
- final upstream test should also delete the winner and prove the former loser becomes effective.

Normative blocker: kubernetes-sigs/gateway-api#4303 must settle the machine-visible status of the deterministic loser before the placeholder status assertion can be replaced.
