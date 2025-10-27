#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out

run_case () {
  local in="$1" exp="$2" tag="$3"
  python3 -m src.main "$in" > "out/$tag.out.txt" || true
  local ok=1
  while IFS= read -r line; do
    if ! grep -Fq -- "$line" "out/$tag.out.txt"; then
      echo "[FAIL] $tag: faltou '$line'"
      ok=0
    fi
  done < "$exp"
  if [ $ok -eq 1 ]; then echo "[OK]   $tag"; else exit 1; fi
}

run_case tests/inputs/ok1.txt     tests/expected/ok1.out.txt     ok1
run_case tests/inputs/ok2.txt     tests/expected/ok2.out.txt     ok2
run_case tests/inputs/err_lex.txt tests/expected/err_lex.out.txt err_lex
run_case tests/inputs/err_syn.txt tests/expected/err_syn.out.txt err_syn
