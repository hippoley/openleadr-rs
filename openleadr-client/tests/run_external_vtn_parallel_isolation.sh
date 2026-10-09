#!/usr/bin/env bash
set -euo pipefail

: "${OPENLEADR_RS_VTN_URL:?set OPENLEADR_RS_VTN_URL}"
: "${OPENLEADR_RS_BL_CLIENT_ID:?set OPENLEADR_RS_BL_CLIENT_ID}"
: "${OPENLEADR_RS_BL_CLIENT_SECRET:?set OPENLEADR_RS_BL_CLIENT_SECRET}"
export OPENLEADR_RS_REQUIRE_EXTERNAL_VTN=1

OUT_DIR="${1:-external-vtn-parallel}"
mkdir -p "$OUT_DIR"

run_one() {
  local slot="$1"
  cargo test -p openleadr-client --test program concurrent_program_runs_do_not_cross_delete -- --exact --nocapture \
    >"$OUT_DIR/$slot.log" 2>&1
}

run_one runner-a &
pid_a=$!
run_one runner-b &
pid_b=$!

set +e
wait "$pid_a"; rc_a=$?
wait "$pid_b"; rc_b=$?
set -e

sha_a="$(sha256sum "$OUT_DIR/runner-a.log" | cut -d' ' -f1)"
sha_b="$(sha256sum "$OUT_DIR/runner-b.log" | cut -d' ' -f1)"
printf 'runner-a %s %s\nrunner-b %s %s\n' "$rc_a" "$sha_a" "$rc_b" "$sha_b"

if [[ "$rc_a" -ne 0 || "$rc_b" -ne 0 ]]; then
  echo "parallel isolation probe failed; inspect retained logs" >&2
  exit 1
fi
