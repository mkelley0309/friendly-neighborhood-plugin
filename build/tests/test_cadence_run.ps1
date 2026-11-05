# Exercises the cadence-run wrapper end to end against a FAKE claude shim in a temp
# USERPROFILE and temp WorkspaceRoot. Never touches the real claude or real cadences.
# Takes about 30 seconds. Exits 1 if any case fails.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\tests\test_cadence_run.ps1
#
# Runs against src/templates/tools/cadence-run.ps1 by default. -Wrapper points it at another
# copy, such as a generated edition's or a committed version to compare against. Themed
# editions rename the wrapper to patrol-run.ps1, and its folder to control-plane\patrols.
param([string]$Wrapper)
$ErrorActionPreference = "Stop"
if (-not $Wrapper) { $Wrapper = Join-Path $PSScriptRoot "..\..\src\templates\tools\cadence-run.ps1" }
$Wrapper = (Resolve-Path $Wrapper).Path
$script:failures = 0

$root = Join-Path $env:TEMP ("cadence-overlap-" + [guid]::NewGuid())
$fakeHome = Join-Path $root "home"
$ws = Join-Path $root "ws"
New-Item -ItemType Directory -Force -Path (Join-Path $fakeHome ".local\bin") | Out-Null
New-Item -ItemType Directory -Force -Path $ws | Out-Null
$prompt = Join-Path $root "prompt.md"
Set-Content -Path $prompt -Value "fake prompt"
$shim = Join-Path $fakeHome ".local\bin\claude"
[IO.File]::WriteAllText($shim, "#!/usr/bin/env bash`necho fake-claude-ran`nsleep `${FAKE_SLEEP:-1}`nexit `${FAKE_EXIT:-0}`n")

$tierDir = if ((Split-Path -Leaf $Wrapper) -eq "patrol-run.ps1") { "patrols" } else { "cadences" }
$work = Join-Path $ws "control-plane\$tierDir\t\_working"
$ps = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"

function Start-Run($sleep, $exit = 0) {
    $inner = "`$env:USERPROFILE='$fakeHome'; `$env:FAKE_SLEEP='$sleep'; `$env:FAKE_EXIT='$exit'; & '$Wrapper' -CadenceName t -PromptFile '$prompt' -PermissionFlag '--permission-mode acceptEdits' -WorkspaceRoot '$ws'; exit `$LASTEXITCODE"
    Start-Process -FilePath $ps -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $inner) -PassThru -WindowStyle Hidden
}
function Flags($pattern) { @(Get-ChildItem -Path $work -Filter $pattern -ErrorAction SilentlyContinue) }
function Reset { if (Test-Path $work) { Get-ChildItem $work -Filter "*.flag" | Remove-Item -Force } }
function Report($name, $ok, $detail) {
    if (-not $ok) { $script:failures++ }
    "{0,-4} {1} {2}" -f $(if ($ok) { "PASS" } else { "FAIL" }), $name, $detail
}

# 1. Overlap: A long, B starts mid-run and finishes first. No false FAILED; both exit 0.
Reset
$a = Start-Run 12
$deadline = (Get-Date).AddSeconds(15)
while ((Flags "RUNNING-*.flag").Count -lt 1 -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 200 }
Start-Sleep -Seconds 1
$b = Start-Run 1
$b.WaitForExit(); $bExit = $b.ExitCode
$midRunning = (Flags "RUNNING-*.flag").Count
$midFailed = (Flags "FAILED-*.flag").Count
$a.WaitForExit(); $aExit = $a.ExitCode
Report "overlap" ($aExit -eq 0 -and $bExit -eq 0 -and $midRunning -eq 1 -and (Flags "FAILED-*.flag").Count -eq 0 -and (Flags "RUNNING-*.flag").Count -eq 0) "a=$aExit b=$bExit running-after-b=$midRunning failed-after-b=$midFailed failed-final=$((Flags 'FAILED-*.flag').Count)"

# 2. Kill evidence: flag owned by a dead process is swept to FAILED.
Reset
$dead = Start-Process -FilePath $ps -ArgumentList @("-NoProfile", "-Command", "exit 0") -PassThru -WindowStyle Hidden
$deadStart = $dead.StartTime.ToString("o"); $dead.WaitForExit()
Set-Content -Path (Join-Path $work "RUNNING-2000-01-01-000000.flag") -Value "killed run owner=$($dead.Id)@$deadStart"
$c = Start-Run 1; $c.WaitForExit()
Report "dead-owner" ((Test-Path (Join-Path $work "FAILED-2000-01-01-000000.flag")) -and $c.ExitCode -eq 0) "exit=$($c.ExitCode)"

# 3. Legacy flag with no owner line is swept to FAILED.
Reset
Set-Content -Path (Join-Path $work "RUNNING-2000-01-02-000000.flag") -Value "cadence-run.ps1 started 't' before owner lines"
$c = Start-Run 1; $c.WaitForExit()
Report "legacy-flag" (Test-Path (Join-Path $work "FAILED-2000-01-02-000000.flag")) "exit=$($c.ExitCode)"

# 4. Reused PID: live PID with the wrong start time counts as dead.
Reset
Set-Content -Path (Join-Path $work "RUNNING-2000-01-03-000000.flag") -Value "reused owner=$PID@2000-01-01T00:00:00.0000000+00:00"
$c = Start-Run 1; $c.WaitForExit()
Report "reused-pid" (Test-Path (Join-Path $work "FAILED-2000-01-03-000000.flag")) "exit=$($c.ExitCode)"

# 5. Real failures still flag: non-zero claude exit gives FAILED and exit 1, no RUNNING left.
Reset
$c = Start-Run 1 3; $c.WaitForExit()
Report "claude-fail" ($c.ExitCode -eq 1 -and (Flags "FAILED-*.flag").Count -eq 1 -and (Flags "RUNNING-*.flag").Count -eq 0) "exit=$($c.ExitCode)"

# 6. Clean solo run leaves no flags.
Reset
$c = Start-Run 1; $c.WaitForExit()
Report "solo-clean" ($c.ExitCode -eq 0 -and (Flags "*.flag").Count -eq 0) "exit=$($c.ExitCode)"

Remove-Item $root -Recurse -Force -Confirm:$false
exit [int]($script:failures -gt 0)
