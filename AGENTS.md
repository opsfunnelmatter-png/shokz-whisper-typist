<!-- HQ_STATE
Name: Shokz Whisper Typist
Category: Voice AI & System Automation
Tier: STANDBY
Stage: v1.0.0 Public Release
Where_I_Stopped: Pakej standalone siap dibina, didokumentasikan mengikut standard antarabangsa, dan di-push ke GitHub (https://github.com/opsfunnelmatter-png/shokz-whisper-typist).
Next_Action: (Pilihan) Tambah installer .exe/GUI ringkas atau bina custom macro triggers.
Ideas: Bina tray icon untuk pantau status mikrofon atau toggle model Whisper.
Resume_Prompt: Sambung dari AGENTS.md (shokz-whisper-typist): Repo v1.0.0 sedia ada di GitHub.
-->

# AGENTS.md — Shokz Whisper Typist

## 🎯 Project Overview
Ultra-fast (<1s latency), bilingual Manglish-native voice typing for Windows powered by Groq Whisper Large v3 and tuned for Shokz bone-conduction headsets.

- **GitHub Repository:** [https://github.com/opsfunnelmatter-png/shokz-whisper-typist](https://github.com/opsfunnelmatter-png/shokz-whisper-typist)
- **License:** MIT License
- **Author:** Muhammad Amin Azman (`opsfunnelmatter-png`)

---

## 🛠️ Architecture & Core Components
- `voice_typing.py` — In-memory real-time parallel audio chunking engine
- `requirements.txt` — Dependencies (groq, sounddevice, speechrecognition, keyboard, pyperclip)
- `scripts/install_startup.ps1` — One-click silent Windows Startup daemon
- `scripts/uninstall_startup.ps1` — Daemon uninstaller
- `sounds/` — In-ear stereo feedback audio cues (F8/F9)
