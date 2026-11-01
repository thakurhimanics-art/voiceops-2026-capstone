"""Step 4: Batch audio processor for customer voice messages using Gnani.ai REST SDK."""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.step4_voice.gnani_client import GnaniVoiceClient
from src.step4_voice.normalizer import normalize_text_for_speech
from src.step3_agent.agent import ZentroMartAgent
from src.config import RESULTS_DIR

logger = logging.getLogger(__name__)
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".pcm", ".flac", ".m4a"}


class VoiceBatchProcessor:
    def __init__(self, gnani_client: Optional[GnaniVoiceClient] = None, agent: Optional[ZentroMartAgent] = None):
        self.gnani = gnani_client or GnaniVoiceClient()
        self.agent = agent or ZentroMartAgent()

    def process_folder(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        language_code: str = "hi-IN",
        safe_mode: bool = True
    ) -> Dict[str, Any]:
        """Process every audio file in input_dir and save transcriptions, text replies, audio replies, and citations.

        Features:
        - Latency measurement per file.
        - Robust error handling for unsupported formats, empty audio, API timeouts, and missing keys.
        - Safe output file paths preventing silent overwrites.
        - Detailed per-file JSON outputs and consolidated batch manifest.
        """
        in_path = Path(input_dir)
        if not in_path.exists() or not in_path.is_dir():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

        out_path = Path(output_dir) if output_dir else (RESULTS_DIR / "voice_batch_output")
        out_path.mkdir(parents=True, exist_ok=True)

        all_files = [p for p in sorted(in_path.iterdir()) if p.is_file()]
        audio_files = [p for p in all_files if p.suffix.lower() in AUDIO_EXTENSIONS]
        unsupported_files = [p for p in all_files if p.suffix.lower() not in AUDIO_EXTENSIONS]

        print(f"\nDiscovered {len(audio_files)} audio file(s) and {len(unsupported_files)} non-audio file(s) in: {in_path}")
        print(f"Output directory: {out_path}\n")

        results = []
        total_files = len(audio_files)
        success_count = 0
        failed_count = 0

        # Process each audio file
        for idx, file_path in enumerate(audio_files, 1):
            t_start = time.time()
            stem = file_path.stem
            print(f"[{idx}/{total_files}] Processing: {file_path.name}...")

            # 1. Transcribe with Gnani STT
            stt_res = self.gnani.transcribe_audio(str(file_path), language_code=language_code)
            status = stt_res.get("status", "error")
            transcript = stt_res.get("transcript", "")
            error_msg = stt_res.get("error", None)

            generated_reply = ""
            spoken_reply = ""
            output_audio_path = None
            retrieved_ids = []
            decision = "answer"

            if stt_res.get("success") and transcript:
                try:
                    # 2. Shared Agent Brain (Step 3 / Step 2)
                    agent_res = self.agent.process_turn(
                        conversation_id=f"voice_{stem}",
                        customer_message=transcript,
                        turn_number=1,
                        language="hi" if "hi" in language_code.lower() else "en"
                    )
                    generated_reply = agent_res.get("reply", "")
                    decision = agent_res.get("decision", "answer")
                    retrieved_ids = agent_res.get("gold_evidence", [])

                    # 3. Speech text normalization (STY-3)
                    spoken_reply = normalize_text_for_speech(generated_reply)

                    # 4. Safe output audio destination
                    audio_out_file = out_path / f"reply_{stem}.wav"
                    if safe_mode and audio_out_file.exists():
                        # Append timestamp suffix to avoid destroying existing audio
                        suffix_ts = int(time.time())
                        audio_out_file = out_path / f"reply_{stem}_{suffix_ts}.wav"

                    # 5. Synthesize Audio Reply with Gnani TTS
                    tts_res = self.gnani.synthesize_speech(
                        text=spoken_reply,
                        output_path=str(audio_out_file),
                        language=language_code
                    )
                    if tts_res.get("success"):
                        output_audio_path = str(audio_out_file)
                        status = "success"
                        success_count += 1
                    else:
                        status = tts_res.get("status", "tts_failed")
                        error_msg = tts_res.get("error")
                        failed_count += 1

                except Exception as agent_err:
                    status = "agent_error"
                    error_msg = str(agent_err)
                    failed_count += 1
                    logger.error(f"Error executing agent on file {file_path.name}: {agent_err}")

            elif stt_res.get("status") == "empty_transcript":
                status = "empty_transcript"
                generated_reply = "I could not hear any speech in the audio. Please try speaking again."
                spoken_reply = generated_reply
                failed_count += 1

            else:
                # Missing API key or transcription failure
                failed_count += 1
                logger.warning(f"File {file_path.name} failed: {status} - {error_msg}")

            t_elapsed = round(time.time() - t_start, 3)

            record = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "status": status,
                "latency_seconds": t_elapsed,
                "transcription": transcript,
                "generated_text_reply": generated_reply,
                "spoken_text_reply": spoken_reply,
                "output_audio_path": output_audio_path,
                "retrieved_section_ids": retrieved_ids,
                "retrieved_sources": retrieved_ids,
                "retrieved_chunks": retrieved_ids,
                "decision": decision,
                "error_message": error_msg
            }
            results.append(record)

            # Save individual record safely
            per_file_json = out_path / f"result_{stem}.json"
            with open(per_file_json, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)

        # Record unsupported files if any
        for u_file in unsupported_files:
            results.append({
                "file_name": u_file.name,
                "file_path": str(u_file),
                "status": "unsupported_audio_format",
                "latency_seconds": 0.0,
                "transcription": "",
                "generated_text_reply": "",
                "spoken_text_reply": "",
                "output_audio_path": None,
                "retrieved_section_ids": [],
                "retrieved_sources": [],
                "retrieved_chunks": [],
                "decision": "error",
                "error_message": f"Unsupported file extension '{u_file.suffix}'. Supported: {sorted(AUDIO_EXTENSIONS)}"
            })

        manifest = {
            "total_files": total_files,
            "success_count": success_count,
            "failed_count": failed_count,
            "unsupported_files_count": len(unsupported_files),
            "input_dir": str(in_path),
            "output_dir": str(out_path),
            "language_code": language_code,
            "files": results
        }

        manifest_file = out_path / "batch_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"\nBatch processing complete.")
        print(f"Total: {total_files} | Success: {success_count} | Status / Failures: {failed_count}")
        print(f"Manifest written to: {manifest_file}")
        return manifest
