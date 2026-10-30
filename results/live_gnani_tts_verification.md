# VoiceOps 2026 — Live Gnani TTS Verification Report

- **Verification Date:** 2026-10-30 20:41:32
- **Test Status:** **SUCCESS**
- **Endpoint:** `https://api.vachana.ai/v1/tts` (Official Gnani REST SDK)
- **Request ID:** `req_239a47818eaa`
- **Model:** `timbre-v2.5`
- **Voice:** `Kaveri`
- **Language Code:** `en-IN`
- **Target Text:** `"Hello, this is a live text to speech test for the VoiceOps capstone."`
- **API Request Latency:** `2.319 seconds`
- **Output File Path:** `C:\Users\Himani Thakur\Desktop\VoiceOps\sample_outputs\live_gnani_tts_test.wav`
- **File Size:** `353,324 bytes`
- **Audio Format:** WAV (linear PCM)
  - **Sample Rate:** `48,000 Hz`
  - **Channels:** `1 (Mono)`
  - **Bit Depth:** `16-bit`
  - **Duration:** `3.68 seconds` (353,280 audio bytes at 96,000 bytes/sec)
- **Local Playback Verification:** `Audible playback succeeded via Windows SoundPlayer (winsound)`

## Diagnostic Details
The official Gnani.ai TTS synthesis API executed successfully with a valid 200 OK response. The audio payload was decoded as standard linear PCM WAV and verified playable on the host machine.
