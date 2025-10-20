Param([string]$Python = "python")

# Pastas
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $base
New-Item -ItemType Directory -Force -Path "out" | Out-Null

# Teste 1
$in  = "tests/script1.txt"
$exp = "tests/expect1.txt"
$out = "out/run1.txt"

# Executa o programa alimentando stdin com o script
Get-Content $in | & $Python -m vending.main | Set-Content -Encoding utf8 $out

# Verifica presença das linhas-chave (robusto a espaços/colunas)
$expected = Get-Content $exp
$fail = $false
foreach ($line in $expected) {
  if (-not (Select-String -Path $out -SimpleMatch $line -Quiet)) {
    Write-Host "[FAIL] faltou no output: $line" -ForegroundColor Red
    $fail = $true
  }
}

if ($fail) {
  Write-Host "[FAIL] script1" -ForegroundColor Red
  exit 1
} else {
  Write-Host "[OK]   script1" -ForegroundColor Green
  exit 0
}
