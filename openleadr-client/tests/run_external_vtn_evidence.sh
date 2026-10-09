#!/usr/bin/env bash
set -u

: "${OPENLEADR_RS_VTN_URL:?set OPENLEADR_RS_VTN_URL to a disposable independent VTN}"
: "${OPENLEADR_RS_BL_CLIENT_ID:?set OPENLEADR_RS_BL_CLIENT_ID}"
: "${OPENLEADR_RS_BL_CLIENT_SECRET:?set OPENLEADR_RS_BL_CLIENT_SECRET}"
: "${OPENLEADR_RS_VEN_CLIENT_ID:?set OPENLEADR_RS_VEN_CLIENT_ID for the negative authorization probe}"
: "${OPENLEADR_RS_VEN_CLIENT_SECRET:?set OPENLEADR_RS_VEN_CLIENT_SECRET for the negative authorization probe}"

export OPENLEADR_RS_REQUIRE_EXTERNAL_VTN=1
OUT_DIR="${1:-external-vtn-evidence}"
mkdir -p "$OUT_DIR"

run_capture() {
  local name="$1"; shift
  local log="$OUT_DIR/$name.log"
  set +e
  "$@" >"$log" 2>&1
  local rc=$?
  set -e
  printf '%s %s %s\n' "$name" "$rc" "$(sha256sum "$log" | cut -d' ' -f1)"
}

set -e
echo "# normal CRUD: expected exit 0"
run_capture program_crud cargo test -p openleadr-client --test program program_crud -- --exact --nocapture
run_capture event_crud cargo test -p openleadr-client --test event event_crud -- --exact --nocapture
run_capture ven_role_cannot_create_program cargo test -p openleadr-client --test program ven_role_cannot_create_program -- --exact --nocapture
run_capture concurrent_program_runs_do_not_cross_delete cargo test -p openleadr-client --test program concurrent_program_runs_do_not_cross_delete -- --exact --nocapture

echo "# deliberate post-create failures: expected nonzero; cleanup must be verified remotely"
export OPENLEADR_RS_INJECT_FAILURE_AFTER_CREATE=1
run_capture program_post_create_panic cargo test -p openleadr-client --test program program_crud -- --exact --nocapture
run_capture event_post_create_panic cargo test -p openleadr-client --test event event_crud -- --exact --nocapture
unset OPENLEADR_RS_INJECT_FAILURE_AFTER_CREATE

echo "# logs retained in $OUT_DIR"
echo "# IMPORTANT: this runner does not assert remote cleanup. Inspect the independent VTN and record"
echo "# remaining_resources plus pre/post observation digests before making a strong claim."
