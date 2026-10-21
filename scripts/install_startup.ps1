# Install Shokz Whisper Typist into Windows Startup (Runs silently in background on boot)

$projectDir = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $projectDir "voice_typing.py"
$startupFolder = [Environment]::GetFolderPath('Startup')
$vbsPath = Join-Path $startupFolder "ShokzVoiceTyping.vbs"

# Resolve pythonw.exe dynamically
$pythonwCmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if ($pythonwCmd) {
    $pythonwPath = $pythonwCmd.Source
} else {
    $pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonwPath = $pythonCmd.Source -replace 'python\.exe$', 'pythonw.exe'
    } else {
        $pythonwPath = "pythonw.exe"
    }
}

$vbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """$pythonwPath"" ""$scriptPath""", 0, False
"@

Set-Content -Path $vbsPath -Value $vbsContent -Encoding ASCII
Write-Host "[+] Successfully registered in Windows Startup: $vbsPath"

# Terminate any previously running instances
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*voice_typing.py*" } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# Launch silent background process
Start-Process "wscript.exe" -ArgumentList "`"$vbsPath`""
Start-Sleep -Seconds 2

$active = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*voice_typing.py*" }
if ($active) {
    Write-Host "[+] Shokz Whisper Typist is now ACTIVE in background (PID: $($active.ProcessId[0]))!"
    Write-Host "[+] Press F8 anywhere in Windows to start/stop dictating."
} else {
    Write-Host "[!] Warning: Process did not start immediately. Please verify Python dependencies."
}
