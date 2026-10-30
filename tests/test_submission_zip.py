"""Automated verification test for the final submission ZIP."""
import zipfile
from pathlib import Path
from src.config import PROJECT_ROOT


def test_submission_zip_exists_and_clean():
    zip_path = PROJECT_ROOT / "zentromart_voiceops.zip"
    assert zip_path.exists(), f"Submission ZIP {zip_path} must exist"
    assert zip_path.stat().st_size > 1000, "ZIP must not be empty"

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()

        # Check required deliverables are present
        assert "README.md" in names, "README.md must be in ZIP"
        assert "report.pdf" in names or "REPORT.pdf" in names, "report.pdf must be in ZIP"
        assert "REPORT.md" in names, "REPORT.md must be in ZIP"
        assert "DEMO_SCRIPT.md" in names, "DEMO_SCRIPT.md must be in ZIP"
        assert "requirements.txt" in names, "requirements.txt must be in ZIP"
        assert "run.py" in names, "run.py must be in ZIP"
        assert ".env.example" in names, ".env.example must be in ZIP"
        assert any(n.startswith("src/") for n in names), "src/ must be in ZIP"
        assert any(n.startswith("eval/") for n in names), "eval/ must be in ZIP"
        assert any(n.startswith("tests/") for n in names), "tests/ must be in ZIP"
        assert any(n.startswith("sample_outputs/") for n in names), "sample_outputs/ must be in ZIP"

        # Check strict forbidden exclusions
        for n in names:
            assert "Capstone_Project_Dataset_FTTT_2026" not in n, f"Dataset leaked into ZIP: {n}"
            assert "__pycache__" not in n, f"Cache leaked into ZIP: {n}"
            assert ".pytest_cache" not in n, f"Pytest cache leaked into ZIP: {n}"
            assert "venv" not in n.split("/")[0], f"Virtualenv leaked into ZIP: {n}"
            if n.startswith(".env") and n != ".env.example":
                assert False, f"Secret .env file leaked into ZIP: {n}"
