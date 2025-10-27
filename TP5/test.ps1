Param([string]$Python = "python")

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
New-Item -ItemType Directory -Force -Path "out" | Out-Null

function Run-Case($in, $exp, $tag) {
  $out = "out/$tag.out.txt"
  & $Python -m src.main $in | Set-Content -Encoding utf8 $out
  $expected = Get-Content $exp
  $fail = $false
  foreach ($line in $expected) {
    if (-not (Select-String -Path $out -SimpleMatch $line -Quiet)) {
      Write-Host "[FAIL] $tag: faltou '$line'" -ForegroundColor Red
      $fail = $true
    }
  }
  if ($fail) { exit 1 } else { Write-Host "[OK]   $tag" -ForegroundColor Green }
}

Run-Case "tests/inputs/ok1.txt"     "tests/expected/ok1.out.txt"     "ok1"
Run-Case "tests/inputs/ok2.txt"     "tests/expected/ok2.out.txt"     "ok2"
Run-Case "tests/inputs/err_lex.txt" "tests/expected/err_lex.out.txt" "err_lex"
Run-Case "tests/inputs/err_syn.txt" "tests/expected/err_syn.out.txt" "err_syn"
