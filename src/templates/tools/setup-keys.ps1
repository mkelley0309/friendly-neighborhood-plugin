# Harness API key setup
# Run once to set all keys as persistent user-level environment variables.
# Keys survive reboots and are picked up by all CLI tools automatically.
# Usage: .\tools\setup-keys.ps1

param(
    [string]$AnthropicKey,
    [string]$OpenAIKey,
    [string]$GeminiKey,
    [string]$OpenRouterKey
)

function Set-Key {
    param([string]$Name, [string]$Value, [string]$UsedBy)
    if ($Value) {
        [System.Environment]::SetEnvironmentVariable($Name, $Value, "User")
        Write-Host "SET  $Name ($UsedBy)"
    } else {
        $existing = [System.Environment]::GetEnvironmentVariable($Name, "User")
        if ($existing) {
            Write-Host "OK   $Name ($UsedBy) — already set (length $($existing.Length))"
        } else {
            Write-Host "SKIP $Name ($UsedBy) — not provided"
        }
    }
}

Write-Host ""
Write-Host "Harness key setup"
Write-Host "-----------------"
Set-Key "ANTHROPIC_API_KEY"  $AnthropicKey   "Claude Code"
Set-Key "OPENAI_API_KEY"     $OpenAIKey      "Codex (direct, optional if using OpenRouter)"
Set-Key "GEMINI_API_KEY"     $GeminiKey      "Gemini CLI"
Set-Key "OPENROUTER_API_KEY" $OpenRouterKey  "Codex (primary), OpenCode cloud fallback"
Write-Host ""
Write-Host "Open a new terminal for changes to take effect."
Write-Host ""
Write-Host "Usage:"
Write-Host '  .\tools\setup-keys.ps1 -AnthropicKey "sk-ant-..." -OpenRouterKey "sk-or-..."'
