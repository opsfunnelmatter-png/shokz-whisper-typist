"""
Shokz Whisper Typist — Ultra-fast, bilingual Manglish-native voice typing for Windows.
Tuned for bone conduction headsets (Shokz OpenRun Pro 2) and general microphones.

Powered by Groq Whisper Large v3 with real-time parallel audio chunking and 
instant paste into any active Windows application.
"""

import os
import sys
import time
import queue
import io
import wave
import ctypes
import winsound
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyperclip
import keyboard

# Load environment variables (.env)
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Initialize Groq Cloud Client
GROQ_CLIENT = None
if os.environ.get('GROQ_API_KEY'):
    try:
        from groq import Groq
        GROQ_CLIENT = Groq()
    except Exception as e:
        print(f"[!] Groq initialization failed: {e}")

# Redirect stdout/stderr to service.log if running in pythonw background mode
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'service.log')
try:
    log_fd = open(LOG_FILE, 'a', encoding='utf-8', buffering=1)
    sys.stdout = log_fd
    sys.stderr = log_fd
except Exception:
    pass

# Single-Instance Mutex: Prevent duplicate background processes
MUTEX_NAME = "Local\\ShokzWhisperTypistMutex"
kernel32 = ctypes.windll.kernel32
mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Mutex '{MUTEX_NAME}' already held. Exiting duplicate instance.")
    sys.exit(0)

# Audio and Key Configuration
TRIGGER_KEY = 'f8'           # Press F8 to start dictation, press F8 again to stop and paste
LANG_KEY = 'f9'              # Press F9 to toggle language mode (English <-> Bahasa Melayu)
SAMPLE_RATE = 16000          # 16kHz sample rate optimal for Whisper models
CHANNELS = 1                 # Mono
LANGUAGE = 'en-US'           # Default starting mode

# Audio Feedback Cues
MEDIA_DIR = r"C:\Windows\Media"
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")
SOUND_START = os.path.join(MEDIA_DIR, "Speech On.wav")
SOUND_STOP = os.path.join(MEDIA_DIR, "Speech Off.wav")
SOUND_SUCCESS = os.path.join(MEDIA_DIR, "notify.wav")
SOUND_ERROR = os.path.join(MEDIA_DIR, "Speech Misrecognition.wav")
SOUND_LANG_MS = os.path.join(SOUNDS_DIR, "voice_malay.wav")
SOUND_LANG_EN = os.path.join(SOUNDS_DIR, "voice_english.wav")

def play_audio(sound_type: str):
    """Play pleasant non-blocking audio cues through active audio output."""
    try:
        path = None
        if sound_type == "start":
            path = SOUND_START
        elif sound_type == "stop":
            path = SOUND_STOP
        elif sound_type == "success":
            path = SOUND_SUCCESS
        elif sound_type == "error":
            path = SOUND_ERROR
        elif sound_type == "lang_en":
            path = SOUND_LANG_EN
        elif sound_type == "lang_ms":
            path = SOUND_LANG_MS
            
        if path and os.path.exists(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass

def show_osd_toast(title: str, subtitle: str = ""):
    """Display an elegant, non-intrusive floating HUD pill at top-center of screen."""
    def _run():
        try:
            import tkinter as tk
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            root.attributes('-alpha', 0.94)
            root.configure(bg='#18181b')
            
            w, h = 260, 56
            sw = root.winfo_screenwidth()
            x = (sw - w) // 2
            y = 50
            root.geometry(f"{w}x{h}+{x}+{y}")
            
            frame = tk.Frame(root, bg='#18181b', highlightthickness=1, highlightbackground='#3f3f46')
            frame.pack(fill='both', expand=True)
            
            lbl_title = tk.Label(frame, text=title, font=('Segoe UI', 11, 'bold'), fg='#f4f4f5', bg='#18181b')
            lbl_title.pack(pady=(7, 1))
            
            if subtitle:
                lbl_sub = tk.Label(frame, text=subtitle, font=('Segoe UI', 8), fg='#a1a1aa', bg='#18181b')
                lbl_sub.pack(pady=(0, 4))
                
            root.after(1000, root.destroy)
            root.mainloop()
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

# Global Speech Recognition Worker
executor = ThreadPoolExecutor(max_workers=4)
recognizer = sr.Recognizer()

def toggle_language():
    """Toggle recognition language mode between English (en-US) and Bahasa Melayu (ms-MY)."""
    global LANGUAGE
    if is_recording:
        return
    if LANGUAGE == 'en-US':
        LANGUAGE = 'ms-MY'
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Switched language to Bahasa Melayu (ms-MY)")
        play_audio("lang_ms")
        show_osd_toast("🇲🇾 Bahasa Melayu", "Google Speech (ms-MY)")
    else:
        LANGUAGE = 'en-US'
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Switched language to English (en-US)")
        play_audio("lang_en")
        show_osd_toast("🇬🇧 English", "Google Speech (en-US)")

def transcribe_chunk_task(pcm_bytes: bytes, lang: str = None) -> str:
    """
    Transcribes raw 16kHz 16-bit mono PCM bytes via Groq Whisper Large v3
    with automatic fallback to Google Speech if API key is absent or offline.
    """
    if not pcm_bytes:
        return ""
        
    # 1. Primary Engine: Groq Whisper Large v3 Turbo (Native Bilingual & Code-Switching)
    if GROQ_CLIENT:
        try:
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(pcm_bytes)
            buf.seek(0)
            
            text = GROQ_CLIENT.audio.transcriptions.create(
                file=('chunk.wav', buf.read()),
                model='whisper-large-v3',
                prompt="Bilingual speech in English and Bahasa Melayu (Manglish). Accurate transcription without translating.",
                temperature=0.0,
                response_format='text'
            )
            text_str = text.strip() if text else ""
            # Filter Whisper phantom hallucinations on ambient silence
            phantom_tokens = {'.', '...', ' .', ' . . .', 'You', 'Thank you.', 'Bye.', 'Thank you for watching.', 'Subtitles by', 'MBC'}
            if text_str and text_str not in phantom_tokens:
                print(f"  [⚡ Groq Whisper Chunk] >> {text_str}")
                return text_str
        except Exception as e:
            print(f"[!] Groq Whisper error, falling back to Google Speech: {e}")

    # 2. Fallback Engine: Google Speech API
    try:
        audio_data = sr.AudioData(pcm_bytes, SAMPLE_RATE, 2)
        use_lang = lang or LANGUAGE
        text = recognizer.recognize_google(audio_data, language=use_lang)
        text_str = text.strip() if text else ""
        if text_str:
            print(f"  [Google Speech Chunk ({use_lang})] >> {text_str}")
        return text_str
    except (sr.UnknownValueError, sr.RequestError):
        return ""
    except Exception as e:
        print(f"[!] Transcribe error: {e}")
        return ""

class RealtimeVoicePipeline:
    """
    Real-Time Parallel Audio Pipeline.
    Listens to incoming audio frames, continuously slices into chunks at natural
    speech boundaries (~380ms pause), and transcribes chunks concurrently.
    """
    def __init__(self):
        self.frame_queue = queue.Queue()
        self.is_active = False
        self.futures = []
        self.thread = None
        self.total_samples = 0
        self.current_lang = LANGUAGE

    def start(self, lang: str = None):
        self.frame_queue = queue.Queue()
        self.is_active = True
        self.futures = []
        self.total_samples = 0
        self.current_lang = lang or LANGUAGE
        self.thread = threading.Thread(target=self._process_stream, daemon=True)
        self.thread.start()

    def feed(self, frames):
        if self.is_active:
            self.frame_queue.put(frames)

    def _process_stream(self):
        current_chunk = []
        current_chunk_samples = 0
        silence_samples = 0
        
        SILENCE_RMS_THRESHOLD = 0.012                  # RMS below this is treated as ambient room silence
        MIN_CHUNK_SAMPLES = int(1.8 * SAMPLE_RATE)     # 1.8s minimum chunk before testing pause
        MAX_CHUNK_SAMPLES = int(7.0 * SAMPLE_RATE)     # 7.0s maximum hard ceiling
        SILENCE_SPLIT_SAMPLES = int(0.38 * SAMPLE_RATE) # 380ms silence = natural sentence boundary

        while self.is_active or not self.frame_queue.empty():
            try:
                data = self.frame_queue.get(timeout=0.04)
            except queue.Empty:
                continue

            current_chunk.append(data)
            num_samples = len(data)
            current_chunk_samples += num_samples
            self.total_samples += num_samples

            rms = np.sqrt(np.mean(data**2))
            if rms < SILENCE_RMS_THRESHOLD:
                silence_samples += num_samples
            else:
                silence_samples = 0

            # Natural sentence boundary split while user is still dictating
            should_split = False
            if current_chunk_samples >= MIN_CHUNK_SAMPLES and silence_samples >= SILENCE_SPLIT_SAMPLES:
                should_split = True
            elif current_chunk_samples >= MAX_CHUNK_SAMPLES:
                should_split = True

            if should_split and current_chunk:
                self._dispatch_chunk(current_chunk)
                current_chunk = []
                current_chunk_samples = 0
                silence_samples = 0

        # Dispatch final remaining audio tail when user stops recording
        if current_chunk:
            self._dispatch_chunk(current_chunk)

    def _dispatch_chunk(self, chunk_frames):
        audio_np = np.concatenate(chunk_frames, axis=0)
        # Drop micro tail fragments < 350ms (avoid button click / release breath)
        if len(audio_np) < int(0.35 * SAMPLE_RATE):
            return
        # Verify it has actual voice content, not dead air or button clicks
        rms = np.sqrt(np.mean(audio_np**2))
        if rms >= 0.012 and np.max(np.abs(audio_np)) >= 0.02:
            pcm_bytes = (audio_np * 32767).clip(-32768, 32767).astype(np.int16).tobytes()
            fut = executor.submit(transcribe_chunk_task, pcm_bytes, self.current_lang)
            self.futures.append(fut)

    def finish_and_get_text(self) -> str:
        self.is_active = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        results = []
        for fut in self.futures:
            try:
                res = fut.result(timeout=6.0)
                if res:
                    results.append(res)
            except Exception as e:
                print(f"[!] Worker future timeout/error: {e}")

        final_text = " ".join(results).strip()
        return final_text

pipeline = RealtimeVoicePipeline()
is_recording = False

def find_audio_device():
    """Locate Shokz OpenRun mic or fall back to Windows Default Recording Device."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            name = dev['name'].lower()
            if 'shokz' in name or 'openrun' in name:
                print(f"[+] Detected Shokz Headset Mic: [{idx}] {dev['name']}")
                return idx
    print("[-] Shokz mic not explicitly found; using Default System Recording Device.")
    return None

def audio_callback(indata, frames, time_info, status):
    if is_recording:
        pipeline.feed(indata.copy())

def main():
    global is_recording

    engine_name = "⚡ Groq Whisper Large v3 (Ultra-Fast Bilingual)" if GROQ_CLIENT else f"Google Speech API ({LANGUAGE})"
    print("=" * 65)
    print("   🎙️ SHOKZ WHISPER TYPIST (WINDOWS SPEECH PIPELINE) 🎙️   ")
    print("=" * 65)
    print(f"• Trigger Hotkey  : [{TRIGGER_KEY.upper()}] (Press to Start, Press again to Paste)")
    print(f"• Language Hotkey : [{LANG_KEY.upper()}] (Toggle English / Bahasa Melayu)")
    print(f"• Active Engine   : {engine_name}")
    print("=" * 65)
    
    # Register F9 language toggle
    try:
        keyboard.add_hotkey(LANG_KEY, toggle_language)
        print(f"[+] Hotkey [{LANG_KEY.upper()}] registered successfully.")
    except Exception as e:
        print(f"[!] Failed to register hotkey [{LANG_KEY.upper()}]: {e}")
    
    active_stream = None

    print(f"[*] Voice typist ready. Press [{TRIGGER_KEY.upper()}] anywhere to begin dictation...")
    while True:
        keyboard.wait(TRIGGER_KEY)
        
        if not is_recording:
            # Engage microphone on-demand
            device_id = find_audio_device()
            is_recording = True
            pipeline.start(lang=LANGUAGE)
            
            try:
                active_stream = sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    device=device_id,
                    callback=audio_callback
                )
                active_stream.start()
                play_audio("start")
                print(f"[🔴 LISTENING] Recording via device [{device_id}]... Press {TRIGGER_KEY.upper()} when done.")
            except Exception as e:
                print(f"[!] Failed to open audio stream: {e}")
                is_recording = False
                active_stream = None
                play_audio("error")
            time.sleep(0.3)
        else:
            # Stop recording and trigger immediate audio cue
            play_audio("stop")
            
            # Allow 350ms Bluetooth buffer flush so the final word is preserved
            time.sleep(0.35)
            is_recording = False
            
            if active_stream:
                try:
                    active_stream.stop()
                    active_stream.close()
                except Exception:
                    pass
                active_stream = None
            
            print(f"[⏹️ PROCESSING] Assembling parallel transcriptions...")
            t_start = time.time()
            final_text = pipeline.finish_and_get_text()
            elapsed = time.time() - t_start
            
            if final_text:
                print(f"[RESULT ({elapsed:.2f}s)] >> {final_text}")
                pyperclip.copy(final_text)
                time.sleep(0.04)
                keyboard.send('ctrl+v')
                print("[+] Successfully pasted into active cursor!\n")
                play_audio("success")
            else:
                print(f"[-] No speech detected (elapsed: {elapsed:.2f}s).")
                play_audio("error")

            time.sleep(0.3)

if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        import traceback
        msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Exited with {type(e).__name__}: {e}\n{traceback.format_exc()}\n"
        print(msg)
        with open(os.path.join(BASE_DIR, 'crash.log'), 'a', encoding='utf-8') as f:
            f.write(msg)
        sys.exit(0 if isinstance(e, SystemExit) else 1)
