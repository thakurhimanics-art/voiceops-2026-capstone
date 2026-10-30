"""Official Gnani.ai STT & TTS client integration using gnani-vachana."""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import GNANI_API_KEY

logger = logging.getLogger(__name__)


class GnaniVoiceClient:
    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("GNANI_API_KEY", "") or GNANI_API_KEY
        self.stt_client = None
        self.tts_client = None
        self._init_sdk()

    def _init_sdk(self):
        """Initialize official Gnani SDK clients if API key is provided."""
        if not self.api_key:
            logger.warning("GNANI_API_KEY not found in environment. Voice operations will report missing_api_key.")
            return

        try:
            from gnani.stt import GnaniSTTClient
            from gnani.tts import GnaniTTSClient
            self.stt_client = GnaniSTTClient(api_key=self.api_key)
            self.tts_client = GnaniTTSClient(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gnani SDK clients: {e}")

    def is_configured(self) -> bool:
        """Check if Gnani API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def transcribe_audio(self, audio_path: str, language_code: str = "hi-IN") -> Dict[str, Any]:
        """Transcribe an audio file using Gnani STT.

        Never falls back to another provider.
        """
        if not self.is_configured():
            return {
                "success": False,
                "status": "missing_api_key",
                "transcript": "",
                "error": "GNANI_API_KEY is not set in environment (.env). Voice transcription requires an active Gnani API key."
            }

        audio_file = Path(audio_path)
        if not audio_file.exists():
            return {
                "success": False,
                "status": "file_not_found",
                "transcript": "",
                "error": f"Audio file not found: {audio_path}"
            }

        try:
            # Call official Gnani STT Client
            result = self.stt_client.transcribe(str(audio_file), language_code=language_code)
            transcript = ""
            if isinstance(result, dict):
                transcript = result.get("transcript") or result.get("text") or ""
            elif hasattr(result, "transcript"):
                transcript = getattr(result, "transcript")
            elif hasattr(result, "text"):
                transcript = getattr(result, "text")
            else:
                transcript = str(result)

            transcript = transcript.strip()
            if not transcript:
                return {
                    "success": True,
                    "status": "empty_transcript",
                    "transcript": "",
                    "message": "Audio transcription was empty or inaudible."
                }

            return {
                "success": True,
                "status": "success",
                "transcript": transcript,
                "raw_result": result
            }
        except Exception as e:
            logger.error(f"Gnani STT transcription error: {e}")
            return {
                "success": False,
                "status": "transcription_error",
                "transcript": "",
                "error": str(e)
            }

    def synthesize_speech(
        self,
        text: str,
        output_path: str,
        language: str = "hi-IN",
        voice: str = "Nalini",
        model: str = "timbre-v2.5"
    ) -> Dict[str, Any]:
        """Synthesize spoken text into audio using Gnani TTS.

        Never falls back to another provider.
        """
        if not self.is_configured():
            return {
                "success": False,
                "status": "missing_api_key",
                "output_path": None,
                "error": "GNANI_API_KEY is not set in environment (.env). Voice synthesis requires an active Gnani API key."
            }

        try:
            response = self.tts_client.synthesize(
                text=text,
                model=model,
                language=language,
                voice=voice
            )

            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)

            # Write audio content bytes
            content = response.content if hasattr(response, "content") else response
            with open(out_file, "wb") as f:
                f.write(content)

            return {
                "success": True,
                "status": "success",
                "output_path": str(out_file),
                "bytes_written": len(content)
            }
        except Exception as e:
            logger.error(f"Gnani TTS synthesis error: {e}")
            return {
                "success": False,
                "status": "synthesis_error",
                "output_path": None,
                "error": str(e)
            }
