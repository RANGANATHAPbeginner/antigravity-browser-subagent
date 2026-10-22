$ErrorActionPreference = 'Stop'

$toolsDir = 'D:\Tools\browser-agent'
$launcher = Join-Path $toolsDir 'launcher.cmd'
$profileDir = 'C:\Users\super\.gemini\browser-agent-profile'
$chromeBinary = 'C:\Program Files\Google\Chrome\Application\chrome.exe'

if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

# 1. Register / Update Scheduled Task for interactive execution
$taskName = "AntigravityAgentBrowser"
schtasks /Create /TN $taskName /TR "`"$launcher`"" /SC ONCE /ST 00:00 /IT /F | Out-Null
Write-Output "Registered scheduled task: $taskName"

# 2. Register Start Menu Shortcuts using real Google Chrome crisp icon
$ws = New-Object -ComObject WScript.Shell
$startMenuDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'

$destinations = @(
    (Join-Path $startMenuDir 'Antigravity Browser Agent.lnk'),
    (Join-Path $startMenuDir 'Antigravity Browser Agent\Antigravity Browser Agent.lnk')
)

foreach ($dest in $destinations) {
    $parent = Split-Path $dest
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $sc = $ws.CreateShortcut($dest)
    $sc.TargetPath = $launcher
    $sc.Arguments = ""
    $sc.WorkingDirectory = $toolsDir
    $sc.Description = "Antigravity Dedicated Interactive Browser Agent (Official Crisp UI)"
    $sc.IconLocation = "$chromeBinary,0"
    $sc.WindowStyle = 7
    $sc.Save()
    Write-Output "Created shortcut: $dest"
}

Write-Output "Setup completed successfully."
