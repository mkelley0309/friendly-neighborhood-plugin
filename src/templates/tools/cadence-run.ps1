# Shared unattended-run helper for Task Scheduler-triggered cadences.
#
# Why this exists: a cadence's run.ps1 that calls `& claude -p ...` directly
# can silently no-op. Where `claude` on PATH resolves to the VS Code extension
# *Bash shim* (~\.local\bin\claude, shebang #!/usr/bin/env bash), PowerShell's
# `&` call operator cannot run it - a shebang script is not a Win32
# application. That failure can be silent (0-byte log, exit 0) or terminate
# the script before anything is written (Task Scheduler LastTaskResult=1, log
# dir never created).
#
# Fix: invoke the shim through Git Bash explicitly, by full path - never bare
# `bash` on PATH, which resolves to the WSL launcher
# (C:\WINDOWS\system32\bash.exe), a different filesystem/PATH entirely where
# `claude` does not exist. After the run, a 0-byte log or non-zero exit writes
# a FAILED-*.flag next to the log and exits 1, so a no-op leaves evidence.
#
# Usage from a cadence's own run.ps1:
#   & (Join-Path $workspace "tools\cadence-run.ps1") `
#       -CadenceName "my-cadence" `
#       -PromptFile (Join-Path $workspace "control-plane\cadences\my-cadence\prompt.md") `
#       -PermissionFlag "--permission-mode acceptEdits"
#
# -PermissionFlag is required on purpose: an unattended run has nobody to
# approve prompts, so choose deliberately ("--permission-mode acceptEdits",
# "--dangerously-skip-permissions", ...). The .claude/settings.json deny-list
# still applies either way. -Model is optional; omitted, Claude Code's default
# model is used.

param(
    [Parameter(Mandatory)][string]$CadenceName,
    [Parameter(Mandatory)][string]$PromptFile,
    [Parameter(Mandatory)][string]$PermissionFlag,
    [string]$Model,
    [string]$WorkspaceRoot  # defaults to this script's parent (tools\ -> workspace root)
)

$ErrorActionPreference = "Stop"

# $PSScriptRoot is empty inside param() defaults on Windows PowerShell 5.1, so resolve here.
if (-not $WorkspaceRoot) { $WorkspaceRoot = Split-Path -Parent $PSScriptRoot }

$logDir = Join-Path $WorkspaceRoot "control-plane\cadences\$CadenceName\_working"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$logFile = Join-Path $logDir "run-$stamp.log"
$failFlag = Join-Path $logDir "FAILED-$stamp.flag"

function Fail($reason) {
    Set-Content -Path $failFlag -Value "cadence-run.ps1 failed for '$CadenceName' at $(Get-Date -Format o): $reason"
    Write-Error $reason -ErrorAction Continue
    exit 1
}

$gitBash = @(
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
    "$env:ProgramFiles\Git\bin\bash.exe"
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $gitBash) {
    Fail "Git Bash not found in any known install location - cannot invoke the claude shim. (Do not fall back to bare 'bash' on PATH: that resolves to the WSL launcher, a different environment where claude is not on PATH.)"
}

$claudeShim = Join-Path $env:USERPROFILE ".local\bin\claude"
if (-not (Test-Path $claudeShim)) {
    Fail "claude shim not found at $claudeShim"
}

if (-not (Test-Path $PromptFile)) {
    Fail "prompt file not found at $PromptFile"
}

Set-Location $WorkspaceRoot
$prompt = Get-Content -Raw -Path $PromptFile

$claudeArgs = @("-p", $prompt) + ($PermissionFlag -split '\s+' | Where-Object { $_ })
if ($Model) { $claudeArgs += @("--model", $Model) }
$claudeArgs += @("--output-format", "text")

# Windows PowerShell 5.1 turns any native stderr line into a terminating error
# under EAP=Stop when redirected - so a harmless claude warning (e.g. the
# workspace-trust notice) kills the script before the log is written or Fail()
# runs (0-byte log, no FAILED flag, LastTaskResult=1). Relax EAP for the
# native call only; exit code + log size are checked explicitly below.
$ErrorActionPreference = "Continue"
& $gitBash $claudeShim @claudeArgs *> $logFile
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

if (-not (Test-Path $logFile) -or (Get-Item $logFile).Length -eq 0) {
    Fail "claude produced a 0-byte log (exit code $exitCode) - the run almost certainly no-op'd. Check that Git Bash and the claude shim are still valid, and that the task's logon type lets it run at trigger time."
}

if ($exitCode -ne 0) {
    Fail "claude exited $exitCode. See $logFile for output."
}
