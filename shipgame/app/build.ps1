# Builds ShipGame.exe. The build tools and the app itself live in %LOCALAPPDATA%\ShipGame (not in
# OneDrive, they're a few hundred MB); the exe loads the game straight from this folder, so edits
# to shipgame.html show up the next time you start it. Run again only if main.js changes.
$ErrorActionPreference = 'Stop'
$game = Split-Path $PSScriptRoot -Parent
$work = Join-Path $env:LOCALAPPDATA 'ShipGame\build'
New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'main.js'), (Join-Path $PSScriptRoot 'package.json') $work -Force

Push-Location $work
try {
  npm install --no-audit --no-fund
  if ($LASTEXITCODE) { throw 'npm install failed' }
  npm run package
  if ($LASTEXITCODE) { throw 'packaging failed' }
} finally { Pop-Location }

$appDir = Join-Path $work 'dist\ShipGame-win32-x64'
Set-Content -Path (Join-Path $appDir 'game-path.txt') -Value $game -NoNewline

# a shortcut next to shipgame.html
$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $game 'ShipGame.lnk'))
$lnk.TargetPath = Join-Path $appDir 'ShipGame.exe'
$lnk.WorkingDirectory = $appDir
$lnk.Save()
Write-Host "Built $appDir\ShipGame.exe (shortcut: $game\ShipGame.lnk)"
