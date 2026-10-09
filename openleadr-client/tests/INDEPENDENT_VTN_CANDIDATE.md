# Independent VTN adapter: hupe1980/openadr (candidate, not verified)

This is an **external implementation**, not a vendored dependency. Do not
interpret this recipe as an interoperability pass. The external implementation
must be installed and started by the operator, with its version and exact
revision retained in the evidence artifact.

## Version and licensing gate

Before adoption, inspect the upstream source LICENSE, package version,
supported OpenADR 3.1 API path, Rust MSRV, and release activity. Record
these facts with the exact tested revision. No source code is copied into
this repository. Upstream documentation has differed on the CLI feature
set; check `openadr --version` and `openadr vtn --help` rather than
assuming that a previously documented command still applies.

## Disposable local instance

The external implementation documents a VTN binary with SQLite storage
and OAuth2 client-credentials for BL and VEN:

```sh
cargo install openadr --features vtn,client,internal-auth,sqlite
export BL_SECRET="$(openssl rand -hex 24)"
export VEN_SECRET="$(openssl rand -hex 24)"
openadr vtn --listen 127.0.0.1:3000 --database ./external-vtn.sqlite \
  --client "bl-1:$BL_SECRET:bl" --client "ven-1:$VEN_SECRET:ven"
```

In a second shell, **using the same secrets**:

```sh
export OPENLEADR_RS_VTN_URL=http://127.0.0.1:3000/openadr3/3.1.0
export OPENLEADR_RS_BL_CLIENT_ID=bl-1
export OPENLEADR_RS_BL_CLIENT_SECRET="$BL_SECRET"
export OPENLEADR_RS_VEN_CLIENT_ID=ven-1
export OPENLEADR_RS_VEN_CLIENT_SECRET="$VEN_SECRET"
bash openleadr-client/tests/run_external_vtn_evidence.sh
bash openleadr-client/tests/run_external_vtn_parallel_isolation.sh
```

Do not expose these credentials or log them in public CI. The command is
a candidate recipe: it is **not** a substitute for a real test run.

## Independent acceptance

Retain the binary version, exact implementation revision, startup log,
runner commit, redacted test logs, and SHA-256 digests. Use an independent
VTN read/observer to verify created IDs are absent after each normal and
fault-injected run. The test executor's own assertion cannot substitute
for that independent observation. Do not promote an artifact to a strong
claim if any step fails, and do not describe this as Alliance certification.

Sources:
- https://hupe1980.github.io/openadr/docs/getting-started/
- https://hupe1980.github.io/openadr/docs/authentication/
- https://hupe1980.github.io/openadr/docs/vtn/
- https://www.openadr.org/openadr-3-certification
