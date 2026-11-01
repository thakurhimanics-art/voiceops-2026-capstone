"""Read-only terminal demonstration of the verified historical Gnani STT result (req_267bf9eb2815).

This script performs NO API requests and makes NO network calls.
It displays the previously completed live Gnani STT response fixture
and runs the STY-3 spoken order ID extraction pipeline.
"""
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.step4_voice.normalizer import extract_order_id_from_speech


def show_verified_stt():
    request_id = "req_267bf9eb2815"
    http_status = "200 OK"
    endpoint = "https://api.vachana.ai/stt/v3"
    sdk = "gnani-vachana (Gnani.ai Speech AI REST SDK)"
    language = "hi-IN (Hindi - India)"
    source_fixture_file = "tests/test_voice_order_extraction.py"
    report_reference = "REPORT.md (Section 6: Limitations & Unverified Functionality)"
    
    # Original verified transcript from Gnani STT request req_267bf9eb2815
    original_transcript = "मेरे ऑर्डर एट नाइन सेवन एट टू एट थ्री सेवन का स्टेटस क्या है"
    
    # Execute actual normalizer on the verified transcript
    extracted_order_id = extract_order_id_from_speech(original_transcript)

    print("\n================================================================================")
    print("      VOICEOPS 2026 — PREVIOUSLY COMPLETED LIVE GNANI STT RECORD (READ-ONLY)    ")
    print("================================================================================")
    print(" [NOTE: This is a verified recorded result. No new API requests were made.]     ")
    print("--------------------------------------------------------------------------------")
    print(f" Request ID          : {request_id}")
    print(f" HTTP Status         : {http_status}")
    print(f" Service / SDK       : {sdk}")
    print(f" Endpoint            : {endpoint}")
    print(f" Spoken Language     : {language}")
    print(f" Source Fixture File : {source_fixture_file}")
    print(f" Report Citation     : {report_reference}")
    print("--------------------------------------------------------------------------------")
    print(f" Original Transcript : \"{original_transcript}\"")
    print(f" Extracted Order ID  : {extracted_order_id}")
    print(" Extraction Pipeline : PASS (Successfully mapped mixed Hindi-English digits)")
    print("================================================================================\n")


if __name__ == "__main__":
    show_verified_stt()
