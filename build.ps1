param(
  [string]$Name = "SafeNote"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "Virtualenv not found at .\.venv\. Create it first (see README)."
}

& $python -m pip install --upgrade pip | Out-Null
& $python -m pip install -r requirements.txt | Out-Null
& $python -m pip install pyinstaller | Out-Null

& $python -m PyInstaller `
  --noconsole `
  --name $Name `
  --clean `
  --onefile `
  ".\safenote.py"

Write-Host ""
Write-Host "Built: dist\$Name.exe"
