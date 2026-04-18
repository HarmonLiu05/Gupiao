Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot

py -3.12 -m pip install -e ".[dev]"

py -3.12 -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name polybot-desktop `
  --paths src `
  --hidden-import yfinance `
  --collect-data tzdata `
  --add-data "config/daily_report.example.yml;config" `
  src/polybot/desktop/app.py
