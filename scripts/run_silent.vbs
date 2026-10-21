Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectDir = fso.GetParentFolderName(scriptDir)
targetScript = projectDir & "\voice_typing.py"

WshShell.Run "pythonw.exe """ & targetScript & """", 0, False
