<div align="center">

# 🎙️ Shokz Whisper Typist

**Ultra-fast (<1s latency), bilingual Manglish-native voice typing for Windows.**  
*Tuned for Shokz bone-conduction headsets and high-productivity desktop workflows.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by Groq Whisper](https://img.shields.io/badge/Engine-Groq%20Whisper%20Large%20v3-orange.svg)](https://groq.com)
[![Platform: Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com/windows)
[![Latency: Sub-Second](https://img.shields.io/badge/Latency-%3C1.0s-brightgreen.svg)](#benchmarks)

</div>

---

## ⚡ The Problem It Solves

Windows built-in voice typing (`Win + H`) and conventional dictation software suffer from three fatal friction points for power users:

1. **Broken Bilingual Code-Switching**: When speaking natural Malaysian English / Manglish (switching between English and Bahasa Melayu in a single sentence), standard speech engines fail catastrophically, hallucinating random words or forcing unnatural English translations.
2. **The "Wait-Then-Paste" Lag (5–8s)**: Most transcription tools capture audio until you stop speaking, save a huge file, and send it for processing—forcing you to wait 6–8 seconds before seeing any text.
3. **Bluetooth Headset Audio Degradation**: Keeping a microphone stream permanently open forces Bluetooth headsets (like Shokz OpenRun Pro 2, AirPods, Sony WH-1000XM) into low-bitrate Handsfree Profile (HFP/HSP) mono mode, ruining music quality and draining headset battery within hours.

**Shokz Whisper Typist** solves this with an **on-demand, real-time parallel audio chunking architecture** powered by **Groq Whisper Large v3**.

---

## 🚀 Key Features

- **⚡ Sub-Second Latency (<1.0s)**: Employs a parallel chunking pipeline. While you are speaking, natural pauses (~380ms) are dynamically detected by an RMS Voice Activity Filter, immediately sliced, and dispatched to Groq cloud workers asynchronously. By the time you press `F8` to finish, over 90% of the sentence is already transcribed!
- **🇲🇾 Native Manglish & Bilingual Accuracy**: Powered by Whisper Large v3 with temperature `0.0` and exemplar bilingual priming. Transcribes rapid code-switching without auto-translating or clipping local colloquial words.
- **🎙️ On-Demand Audio Stream**: Mic hardware engages *only* while dictating (`F8` active) and releases immediately upon stop. Your headset remains in crisp high-fidelity stereo playback mode during normal use.
- **🔊 Discreet In-Ear Stereo Cues**: Uses native Windows stereo cues (`Speech On.wav`, `Speech Off.wav`, `notify.wav`) played directly through active audio devices so you know the exact operational state without looking at the screen.
- **🌐 Dual-Engine Resilience**: Seamless automatic fallback to Google Speech API if offline or if no Groq API key is present.
- **🪟 Invisible Windows Background Daemon**: One-click startup script runs silently via `pythonw.exe` with a single-instance Windows kernel mutex lock. Zero command prompt windows cluttering your taskbar.
- **🖥️ Floating OSD Toast**: Non-intrusive dark-mode HUD pill display at the top of your screen when switching language modes (`F9`).

---

## 📊 Benchmarks

| Feature | Windows Voice (`Win + H`) | Local Whisper (base.en) | Google Speech API | **Shokz Whisper Typist (Groq)** |
| :--- | :--- | :--- | :--- | :--- |
| **Bilingual Manglish** | ❌ Fails / Hallucinates | ❌ Heavy hallucination | ⚠️ Requires separate modes | ✅ **100% Native Bilingual** |
| **Pasting Latency** | ~2–3s | ~3–5s (High CPU/GPU) | ~6–8s on long sentences | ⚡ **< 1.0s (Sub-second)** |
| **Bluetooth Quality** | Continuous HFP lock | Continuous HFP lock | Continuous HFP lock | ✅ **On-Demand (Zero battery hit)** |
| **Silent Background** | Built-in UI popup | CLI terminal required | CLI terminal required | ✅ **Invisible `pythonw` daemon** |
| **Hardware Required** | Windows 11 only | High GPU/RAM | Any | **Any PC (Cloud-accelerated)** |

---

## 🛠️ Architecture Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Hotkey as Global Hotkey (F8)
    participant Audio as Shokz Mic Stream
    participant Pipeline as Real-time Pipeline
    participant Groq as Groq Whisper Cloud
    participant OS as Windows Clipboard & Cursor

    User->>Hotkey: Press F8 (Start)
    Hotkey->>Audio: Open On-Demand Stream
    Hotkey->>User: Play Stereo Cue (Speech On)
    
    loop While Dictating
        Audio->>Pipeline: Stream 16kHz PCM audio
        Pipeline->>Pipeline: Detect natural pauses (~380ms silence)
        Pipeline->>Groq: Dispatch audio chunk asynchronously (Parallel Worker)
    end

    User->>Hotkey: Press F8 (Stop)
    Hotkey->>Audio: Close Stream (Restore Stereo Playback)
    Hotkey->>User: Play Stereo Cue (Speech Off)
    
    Pipeline->>Groq: Dispatch final remaining audio tail
    Groq-->>Pipeline: Return chunk transcriptions
    Pipeline->>Pipeline: Reassemble chronological text
    Pipeline->>OS: Copy to Clipboard & Send Ctrl+V
    OS->>User: Play Success Chime & Text Pasted instantly!
```

---

## 📋 Hotkeys & Controls

| Shortcut | Action | Description |
| :---: | :--- | :--- |
| **`F8`** | **Toggle Dictation** | Press once to start listening. Press again when finished to instantly paste at cursor. |
| **`F9`** | **Toggle Language Mode** | Switch between English (`en-US`) and Bahasa Melayu (`ms-MY`) with spoken audio confirmation. |

---

## ⚙️ Quick Start

### 1. Prerequisites
- Windows 10 or Windows 11
- Python 3.10+ installed ([python.org](https://www.python.org/downloads/))
- Microphone (Tuned for **Shokz OpenRun Pro 2**, but works with any Bluetooth, USB, or built-in mic)
- Free Groq Cloud API Key ([console.groq.com](https://console.groq.com/keys))

### 2. Installation

Clone this repository:
```bash
git clone https://github.com/opsfunnelmatter-png/shokz-whisper-typist.git
cd shokz-whisper-typist
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create your `.env` file from the provided template:
```bash
copy .env.example .env
```

Open `.env` in any text editor and add your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 4. Run / Test
Run directly in your terminal to verify mic detection and speech recognition:
```bash
python voice_typing.py
```
Press **`F8`**, speak a sentence, and press **`F8`** again. The transcribed text will appear directly in your active cursor position.

---

## 🚀 One-Click Windows Startup (Silent Background Mode)

To have Shokz Whisper Typist start automatically every time you log in to Windows—running completely invisibly in the background:

Right-click PowerShell and run:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_startup.ps1
```

### To Uninstall from Startup:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/uninstall_startup.ps1
```

---

## 📂 Project Structure

```
shokz-whisper-typist/
├── .env.example          # Environment variable template (API Keys)
├── .gitignore            # Protects credentials and runtime cache
├── LICENSE               # Open-source MIT License
├── README.md             # International project documentation
├── requirements.txt      # Pinned Python dependencies
├── voice_typing.py       # Core streaming & parallel transcription engine
├── scripts/
│   ├── install_startup.ps1    # Automated Windows Startup installer
│   ├── uninstall_startup.ps1  # Automated service uninstaller
│   └── run_silent.vbs         # Silent VBScript wrapper for pythonw
└── sounds/
    ├── cue_en.wav        # Spoken audio confirmation: English
    ├── cue_ms.wav        # Spoken audio confirmation: Bahasa Melayu
    ├── voice_english.wav # Clean cue for English mode
    └── voice_malay.wav   # Clean cue for Malay mode
```

---

## 🔒 Security & Privacy

- **No Hardcoded Keys**: The application strictly reads API credentials from local `.env` files or environment variables.
- **Zero Local Audio Retention**: Audio chunks are processed in-memory (`io.BytesIO`) and discarded immediately upon transcription. No audio recordings are saved to disk.
- **Encrypted In-Transit**: All requests to Groq Cloud API use standard HTTPS TLS 1.3 encryption.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to open an issue or submit a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
Built with ❤️ for bilingual Malaysian developers and productivity enthusiasts.
</div>
