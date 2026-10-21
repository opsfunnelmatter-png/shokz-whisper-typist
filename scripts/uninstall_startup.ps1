# Uninstall Shokz Whisper Typist from Windows Startup

$startupFolder = [Environment]::GetFolderPath('Startup')
$vbsPath = Join-Path $startupFolder "ShokzVoiceTyping.vbs"

if (Test-Path $vbsPath) {
    Remove-Item -Path $vbsPath -Force
    Write-Host "[+] Removed from Windows Startup: $vbsPath"
} else {
    Write-Host "[-] Startup script was not found in Startup folder."
}

# Terminate running background process
$killed = 0
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*voice_typing.py*" } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    $killed++
}

Write-Host "[+] Terminated $killed running voice typing process(es)."
