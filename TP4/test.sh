#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out

# Teste 1
python3 -m vending.main < tests/script1.txt > out/run1.txt

ok=1
while IFS= read -r line; do
  if ! grep -Fq -- "$line" out/run1.txt; then
    echo "[FAIL] faltou no output: $line"
    ok=0
  fi
done < tests/expect1.txt

if [ $ok -eq 1 ]; then
  echo "[OK]   script1"
  exit 0
else
  exit 1
fi
