#!/usr/bin/env bash
set -euo pipefail

: "${OPENLEADR_RS_VTN_URL:?set OPENLEADR_RS_VTN_URL to a disposable independent VTN}"
: "${OPENLEADR_RS_BL_CLIENT_ID:?set OPENLEADR_RS_BL_CLIENT_ID}"
: "${OPENLEADR_RS_BL_CLIENT_SECRET:?set OPENLEADR_RS_BL_CLIENT_SECRET}"
: "${OPENLEADR_RS_VEN_CLIENT_ID:?set OPENLEADR_RS_VEN_CLIENT_ID}"
: "${OPENLEADR_RS_VEN_CLIENT_SECRET:?set OPENLEADR_RS_VEN_CLIENT_SECRET}"

export OPENLEADR_RS_REQUIRE_EXTERNAL_VTN=1
OUT_DIR="${1:-external-vtn-evidence}"
mkdir -p "$OUT_DIR"
python3 openleadr-client/tests/preflight_external_vtn.py >"$OUT_DIR/preflight.json"

failures=0
run_capture() {
  local name="$1" expected="$2"
  shift 2
  local log="$OUT_DIR/$name.log" rc
  if "$@" >"$log" 2>&1; then rc=0; else rc=$?; fi
  printf '%s %s %s\n' "$name" "$rc" "$(sha256sum "$log" | cut -d' ' -f1)" | tee -a "$OUT_DIR/exit-codes.sha256.txt"
  if [[ "$expected" == "zero" && "$rc" -ne 0 ]] || [[ "$expected" == "nonzero" && "$rc" -eq 0 ]]; then
    printf 'UNEXPECTED_EXIT %s expected=%s actual=%s\n' "$name" "$expected" "$rc" >&2
    failures=$((failures + 1))
  fi
}

: >"$OUT_DIR/exit-codes.sha256.txt"
run_capture program_crud zero cargo test -p openleadr-client --test program program_crud -- --exact --nocapture
run_capture event_crud zero cargo test -p openleadr-client --test event event_crud -- --exact --nocapture
run_capture ven_role_cannot_create_program zero cargo test -p openleadr-client --test program ven_role_cannot_create_program -- --exact --nocapture
run_capture concurrent_program_runs_do_not_cross_delete zero cargo test -p openleadr-client --test program concurrent_program_runs_do_not_cross_delete -- --exact --nocapture

export OPENLEADR_RS_INJECT_FAILURE_AFTER_CREATE=1
run_capture program_post_create_panic nonzero cargo test -p openleadr-client --test program program_crud -- --exact --nocapture
run_capture event_post_create_panic nonzero cargo test -p openleadr-client --test event event_crud -- --exact --nocapture
unset OPENLEADR_RS_INJECT_FAILURE_AFTER_CREATE

if (( failures > 0 )); then
  echo "FAIL: $failures unexpected test exit codes; inspect retained logs in $OUT_DIR" >&2
  exit 1
fi
echo "PASS: expected exit-code pattern; remote cleanup and effect attribution NOT verified"
echo "Logs and digests: $OUT_DIR"
