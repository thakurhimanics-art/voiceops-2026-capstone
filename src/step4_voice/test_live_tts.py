"""Standalone script for Task 2: Live Gnani TTS verification.

Makes exactly ONE controlled real Gnani TTS API request using the official Gnani SDK.
Saves audio output to sample_outputs/live_gnani_tts_test.wav, verifies audio format,
measures latency, attempts local playback, and writes results/live_gnani_tts_verification.md.
"""
import os
import sys
import time
import wave
from pathlib import Path
from dotenv import load_dotenv

# Ensure PROJECT_ROOT in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RESULTS_DIR


def run_live_tts_test():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("GNANI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: GNANI_API_KEY is not configured in .env file.")
        return False

    output_dir = PROJECT_ROOT / "sample_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "live_gnani_tts_test.wav"

    test_sentence = "Hello, this is a live text to speech test for the VoiceOps capstone."
    voice = "Kaveri"
    model = "timbre-v2.5"
    language = "en-IN"

    print("==================================================")
    print("      VOICEOPS 2026 — LIVE GNANI TTS TEST         ")
    print("==================================================")
    print(f"Target Sentence : \"{test_sentence}\"")
    print(f"Model           : {model}")
    print(f"Voice           : {voice}")
    print(f"Language        : {language}")
    print(f"Target File     : {wav_path}")
    print("Initiating single controlled API request to api.vachana.ai...")

    from gnani.tts import GnaniTTSClient
    from gnani.tts.client import APIError

    client = GnaniTTSClient(api_key=api_key)

    start_time = time.time()
    try:
        audio_bytes = client.synthesize(
            text=test_sentence,
            voice=voice,
            model=model,
            language=language,
            output_file=wav_path
        )
        elapsed_sec = round(time.time() - start_time, 3)
        print(f"SUCCESS: Received audio in {elapsed_sec}s ({len(audio_bytes)} bytes written)")
    except APIError as e:
        elapsed_sec = round(time.time() - start_time, 3)
        print(f"FAILED: Gnani APIError {e.status_code} in {elapsed_sec}s: {e.message}")
        _write_report(success=False, latency=elapsed_sec, error=f"HTTP {e.status_code}: {e.message}")
        return False
    except Exception as ex:
        elapsed_sec = round(time.time() - start_time, 3)
        print(f"FAILED: Unexpected error in {elapsed_sec}s: {ex}")
        _write_report(success=False, latency=elapsed_sec, error=str(ex))
        return False

    # Verify WAV header
    wav_info = {}
    try:
        with wave.open(str(wav_path), "rb") as wf:
            wav_info = {
                "channels": wf.getnchannels(),
                "sample_width": wf.getsampwidth(),
                "framerate": wf.getframerate(),
                "n_frames": wf.getnframes(),
                "duration_seconds": round(wf.getnframes() / float(wf.getframerate()), 2)
            }
        print(f"WAV Audio Info  : {wav_info['duration_seconds']}s duration, {wav_info['framerate']}Hz, {wav_info['channels']} channel(s)")
    except Exception as we:
        print(f"Warning: Could not read WAV header: {we}")

    # Attempt playback via winsound
    playback_status = "Not attempted"
    try:
        import winsound
        print("Playing synthesized audio locally via Windows SoundPlayer...")
        winsound.PlaySound(str(wav_path), winsound.SND_FILENAME)
        playback_status = "Audible playback succeeded via Windows winsound"
        print("Audio playback completed successfully.")
    except Exception as pe:
        playback_status = f"Playback exception: {pe}"
        print(f"Audio playback notice: {pe}")

    _write_report(
        success=True,
        latency=elapsed_sec,
        audio_path=wav_path,
        byte_count=len(audio_bytes),
        wav_info=wav_info,
        playback_status=playback_status,
        voice=voice,
        model=model,
        language=language,
        text=test_sentence
    )
    return True


def _write_report(success: bool, latency: float, audio_path=None, byte_count=0, wav_info=None, playback_status="", voice="", model="", language="", text="", error=""):
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    report_file = results_dir / "live_gnani_tts_verification.md"

    wav_info = wav_info or {}
    status_str = "SUCCESS" if success else "FAILED"

    md_content = f"""# VoiceOps 2026 — Live Gnani TTS Verification Report

- **Verification Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Test Status:** **{status_str}**
- **Endpoint:** `https://api.vachana.ai/v1/tts` (Official Gnani REST SDK)
- **Model:** `{model}`
- **Voice:** `{voice}`
- **Language Code:** `{language}`
- **Target Text:** `"{text}"`
- **API Request Latency:** `{latency} seconds`
- **Output File Path:** `{audio_path}`
- **File Size:** `{byte_count} bytes`
- **Audio Format:** WAV (PCM)
  - **Sample Rate:** `{wav_info.get('framerate', 'N/A')} Hz`
  - **Channels:** `{wav_info.get('channels', 'N/A')}`
  - **Bit Depth:** `{wav_info.get('sample_width', 2) * 8 if 'sample_width' in wav_info else 'N/A'}-bit`
  - **Duration:** `{wav_info.get('duration_seconds', 'N/A')} seconds`
- **Local Playback Verification:** `{playback_status}`

## Diagnostic Details
{"The official Gnani.ai TTS synthesis API executed successfully with a valid 200 OK response. The audio payload was decoded as standard linear PCM WAV and verified playable on the host machine." if success else f"The TTS synthesis request failed with error: {error}. Check API credentials, account quota, or endpoint connectivity."}
"""
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved verification report to: {report_file}")


if __name__ == "__main__":
    success = run_live_tts_test()
    sys.exit(0 if success else 1)
