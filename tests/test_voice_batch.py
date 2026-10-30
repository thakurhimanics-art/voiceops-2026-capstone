"""Offline unit tests for Step 4 Voice Batch Processor and Gnani client error handling."""
import json
import pytest
from pathlib import Path

from src.step4_voice.batch_processor import VoiceBatchProcessor
from src.step4_voice.gnani_client import GnaniVoiceClient


class MockGnaniClient:
    """Mock Gnani Voice client for zero-cost, deterministic offline testing."""
    def __init__(self, stt_response=None, tts_response=None, is_conf=True):
        self._stt_response = stt_response
        self._tts_response = tts_response
        self._is_configured = is_conf

    def is_configured(self) -> bool:
        return self._is_configured

    def transcribe_audio(self, audio_path: str, language_code: str = "hi-IN"):
        return self._stt_response

    def synthesize_speech(self, text: str, output_path: str, language: str = "hi-IN", voice: str = "Nalini", model: str = "timbre-v2.5"):
        if self._tts_response and not self._tts_response.get("success"):
            return self._tts_response

        # Write dummy audio bytes to output_path
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "wb") as f:
            f.write(b"RIFF_MOCK_AUDIO_DATA_FOR_OFFLINE_TEST")

        return self._tts_response or {
            "success": True,
            "status": "success",
            "output_path": str(out_file),
            "bytes_written": 37
        }


class MockAgent:
    """Mock agent returning controlled dialogue responses."""
    def __init__(self, reply: str = "Order 89782837 is delivered.", decision: str = "answer", evidence=None):
        self.reply = reply
        self.decision = decision
        self.evidence = evidence or ["DEL-1"]

    def process_turn(self, conversation_id: str, customer_message: str, turn_number: int = 1, language: str = "hi"):
        return {
            "reply": self.reply,
            "decision": self.decision,
            "gold_evidence": self.evidence
        }


def test_batch_processor_success(tmp_path):
    """Test successful STT -> Agent -> TTS pipeline with generated files."""
    in_dir = tmp_path / "audio_in"
    out_dir = tmp_path / "audio_out"
    in_dir.mkdir()

    # Create dummy audio input
    wav_file = in_dir / "customer_query.wav"
    wav_file.write_bytes(b"RIFF_FAKE_INPUT_AUDIO")

    mock_client = MockGnaniClient(
        stt_response={
            "success": True,
            "status": "success",
            "transcript": "Mere order 89782837 ka status kya hai?"
        },
        tts_response={
            "success": True,
            "status": "success",
            "output_path": str(out_dir / "reply_customer_query.wav"),
            "bytes_written": 37
        }
    )
    mock_agent = MockAgent(reply="Order 89782837 deliver ho chuka hai.", decision="answer")

    processor = VoiceBatchProcessor(gnani_client=mock_client, agent=mock_agent)
    manifest = processor.process_folder(input_dir=str(in_dir), output_dir=str(out_dir), language_code="hi-IN")

    assert manifest["total_files"] == 1
    assert manifest["success_count"] == 1
    assert manifest["failed_count"] == 0

    record = manifest["files"][0]
    assert record["status"] == "success"
    assert record["transcription"] == "Mere order 89782837 ka status kya hai?"
    assert "8 9 7 8, 2 8 3 7" in record["spoken_text_reply"]
    assert record["output_audio_path"] is not None
    assert Path(record["output_audio_path"]).exists()

    # Verify output JSON files
    assert (out_dir / "result_customer_query.json").exists()
    assert (out_dir / "batch_manifest.json").exists()


def test_batch_processor_empty_transcription(tmp_path):
    """Test handling of inaudible/silent audio returning empty transcript."""
    in_dir = tmp_path / "audio_in"
    out_dir = tmp_path / "audio_out"
    in_dir.mkdir()

    wav_file = in_dir / "silent_call.wav"
    wav_file.write_bytes(b"RIFF_SILENT_AUDIO")

    mock_client = MockGnaniClient(
        stt_response={
            "success": True,
            "status": "empty_transcript",
            "transcript": "",
            "message": "Audio transcription was empty or inaudible."
        }
    )

    processor = VoiceBatchProcessor(gnani_client=mock_client)
    manifest = processor.process_folder(input_dir=str(in_dir), output_dir=str(out_dir))

    assert manifest["total_files"] == 1
    assert manifest["success_count"] == 0
    assert manifest["failed_count"] == 1

    record = manifest["files"][0]
    assert record["status"] == "empty_transcript"
    assert record["transcription"] == ""
    assert record["output_audio_path"] is None


def test_batch_processor_stt_error(tmp_path):
    """Test handling of STT network or processing failures."""
    in_dir = tmp_path / "audio_in"
    out_dir = tmp_path / "audio_out"
    in_dir.mkdir()

    wav_file = in_dir / "failed_stt.wav"
    wav_file.write_bytes(b"RIFF_BROKEN_AUDIO")

    mock_client = MockGnaniClient(
        stt_response={
            "success": False,
            "status": "transcription_error",
            "transcript": "",
            "error": "Connection reset by peer"
        }
    )

    processor = VoiceBatchProcessor(gnani_client=mock_client)
    manifest = processor.process_folder(input_dir=str(in_dir), output_dir=str(out_dir))

    assert manifest["success_count"] == 0
    assert manifest["failed_count"] == 1

    record = manifest["files"][0]
    assert record["status"] == "transcription_error"
    assert record["error_message"] == "Connection reset by peer"
    assert record["output_audio_path"] is None


def test_batch_processor_tts_error(tmp_path):
    """Test handling when STT succeeds but TTS synthesis encounters an error."""
    in_dir = tmp_path / "audio_in"
    out_dir = tmp_path / "audio_out"
    in_dir.mkdir()

    wav_file = in_dir / "tts_fail.wav"
    wav_file.write_bytes(b"RIFF_AUDIO")

    mock_client = MockGnaniClient(
        stt_response={
            "success": True,
            "status": "success",
            "transcript": "Hello support"
        },
        tts_response={
            "success": False,
            "status": "synthesis_error",
            "output_path": None,
            "error": "Rate limit exceeded on TTS endpoint"
        }
    )
    mock_agent = MockAgent(reply="Hello, how can I help?")

    processor = VoiceBatchProcessor(gnani_client=mock_client, agent=mock_agent)
    manifest = processor.process_folder(input_dir=str(in_dir), output_dir=str(out_dir))

    assert manifest["success_count"] == 0
    assert manifest["failed_count"] == 1

    record = manifest["files"][0]
    assert record["status"] == "synthesis_error"
    assert record["error_message"] == "Rate limit exceeded on TTS endpoint"
    assert record["output_audio_path"] is None


def test_gnani_client_missing_api_key():
    """Test GnaniVoiceClient error handling when API key is missing or unconfigured."""
    client = GnaniVoiceClient(api_key="")
    assert client.is_configured() is False

    stt_res = client.transcribe_audio("any_file.wav")
    assert stt_res["success"] is False
    assert stt_res["status"] == "missing_api_key"
    assert "GNANI_API_KEY is not set" in stt_res["error"]

    tts_res = client.synthesize_speech("Hello", "any_output.wav")
    assert tts_res["success"] is False
    assert tts_res["status"] == "missing_api_key"
    assert "GNANI_API_KEY is not set" in tts_res["error"]


def test_batch_processor_missing_api_key(tmp_path):
    """Test batch processor gracefully logs missing_api_key without crashing."""
    in_dir = tmp_path / "audio_in"
    out_dir = tmp_path / "audio_out"
    in_dir.mkdir()

    wav_file = in_dir / "test_no_key.wav"
    wav_file.write_bytes(b"RIFF_AUDIO")

    mock_client = MockGnaniClient(
        stt_response={
            "success": False,
            "status": "missing_api_key",
            "transcript": "",
            "error": "GNANI_API_KEY is not set in environment (.env)."
        },
        is_conf=False
    )

    processor = VoiceBatchProcessor(gnani_client=mock_client)
    manifest = processor.process_folder(input_dir=str(in_dir), output_dir=str(out_dir))

    assert manifest["failed_count"] == 1
    record = manifest["files"][0]
    assert record["status"] == "missing_api_key"


def test_gnani_client_file_not_found(tmp_path):
    """Test GnaniVoiceClient correctly reports file_not_found before attempting network calls."""
    # Create client with dummy key so is_configured is True
    client = GnaniVoiceClient(api_key="vach_dummy_key_for_testing_offline_paths_only")
    absent_path = str(tmp_path / "non_existent_audio.wav")

    res = client.transcribe_audio(absent_path)
    assert res["success"] is False
    assert res["status"] == "file_not_found"
    assert "Audio file not found" in res["error"]


def test_batch_processor_invalid_input_dir():
    """Test batch processor raises FileNotFoundError for non-existent input folder."""
    processor = VoiceBatchProcessor()
    with pytest.raises(FileNotFoundError):
        processor.process_folder("non_existent_dir_voiceops_test_99999")


def test_batch_processor_ignores_non_audio_files(tmp_path):
    """Test batch processor skips non-audio files (txt, png, csv, etc.)."""
    in_dir = tmp_path / "mixed_files"
    out_dir = tmp_path / "mixed_out"
    in_dir.mkdir()

    (in_dir / "readme.txt").write_text("Not audio", encoding="utf-8")
    (in_dir / "data.csv").write_text("a,b,c", encoding="utf-8")
    (in_dir / "photo.png").write_bytes(b"PNG_DATA")

    mock_client = MockGnaniClient()
    processor = VoiceBatchProcessor(gnani_client=mock_client)
    manifest = processor.process_folder(input_dir=str(in_dir), output_dir=str(out_dir))

    assert manifest["total_files"] == 0
    assert manifest["success_count"] == 0
    assert manifest["failed_count"] == 0
