Param([string]$Python = "python")

$inputs = Get-ChildItem -Path "tests/inputs" -Filter *.sparql | Sort-Object Name
New-Item -ItemType Directory -Force -Path "tests/out" | Out-Null

function Normalize([string[]]$lines) {
  # junta por `n`, aplica regex pra reduzir espaços em excesso, volta a separar
  ($lines -join "`n") -replace "[`t ]+", " " -replace "`r", "" -split "`n"
}

$allOk = $true
foreach ($in in $inputs) {
  $name = [IO.Path]::GetFileNameWithoutExtension($in.Name)
  $exp = "tests/expected/$name.tokens.txt"
  $out = "tests/out/$name.tsv"

  & $Python -m src.main $in.FullName | Set-Content -Encoding utf8 $out

  if (!(Test-Path $exp)) {
    Write-Host "[WARN] missing expected: $exp" -ForegroundColor Yellow
    $allOk = $false; continue
  }

  $normExp = Normalize (Get-Content $exp)
  $normOut = Normalize (Get-Content $out)

  $diff = Compare-Object $normExp $normOut
  if ($diff) {
    Write-Host "[FAIL] $name" -ForegroundColor Red
    $diff | Format-Table | Out-String | Write-Host
    $allOk = $false
  } else {
    Write-Host "[OK]   $name" -ForegroundColor Green
  }
}

if ($allOk) { exit 0 } else { exit 1 }
