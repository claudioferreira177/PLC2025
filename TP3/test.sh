#!/usr/bin/env bash
set -euo pipefail
mkdir -p tests/out
ok=1
for in in tests/inputs/*.sparql; do
  base="$(basename "$in" .sparql)"
  exp="tests/expected/$base.tokens.txt"
  out="tests/out/$base.tsv"
  python3 -m src.main "$in" > "$out"
  if ! diff -u "$exp" "$out"; then
    echo "[FAIL] $base"
    ok=0
  else
    echo "[OK]   $base"
  fi
done
exit $ok
