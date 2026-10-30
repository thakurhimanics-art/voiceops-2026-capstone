"""Configuration and business logic utilities for ZentroMart VoiceOps."""
import csv
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Reference Date for Capstone
REFERENCE_DATE = date(2026, 10, 20)
REFERENCE_DATE_STR = "2026-10-20"

# Directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = PROJECT_ROOT / "Capstone_Project_Dataset_FTTT_2026"
DATA_DIR = DATASET_ROOT / "data"
KB_DIR = DATASET_ROOT / "kb"
PRACTICE_DIR = DATASET_ROOT / "practice"
TOOLS_DIR = DATASET_ROOT / "tools"
RESULTS_DIR = PROJECT_ROOT / "results"
SAMPLE_OUTPUTS_DIR = PROJECT_ROOT / "sample_outputs"

# Ensure runtime directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# LLM & Voice Environment Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # 'ollama', 'openai', 'groq', 'gemini'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GNANI_API_KEY = os.getenv("GNANI_API_KEY", "")

# Load Holidays
HOLIDAYS = {}
holidays_csv = DATA_DIR / "holidays.csv"
if holidays_csv.exists():
    with open(holidays_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_str = row["date"].strip()
            if d_str:
                HOLIDAYS[datetime.strptime(d_str, "%Y-%m-%d").date()] = row["name"].strip()


def parse_date(d_val) -> date:
    """Parse date from string or date object."""
    if isinstance(d_val, date) and not isinstance(d_val, datetime):
        return d_val
    if isinstance(d_val, datetime):
        return d_val.date()
    d_str = str(d_val).strip()
    if "T" in d_str:
        d_str = d_str.split("T")[0]
    return datetime.strptime(d_str, "%Y-%m-%d").date()


def is_business_day(d: date) -> bool:
    """A business day is Monday to Saturday (0 to 5), excluding listed holidays."""
    if d.weekday() == 6:  # Sunday
        return False
    if d in HOLIDAYS:
        return False
    return True


def add_business_days(start_d: date, n_days: int) -> date:
    """Add n business days starting from start_d (exclusive of start_d)."""
    curr = start_d
    added = 0
    while added < n_days:
        curr += timedelta(days=1)
        if is_business_day(curr):
            added += 1
    return curr


def business_days_between(start_d: date, end_d: date) -> int:
    """Count business days strictly between start_d and end_d (exclusive of start, inclusive of end)."""
    if start_d >= end_d:
        return 0
    curr = start_d
    count = 0
    while curr < end_d:
        curr += timedelta(days=1)
        if is_business_day(curr):
            count += 1
    return count


def get_return_window_days(category: str, order_placed_date: date = None, delivered_date: date = None) -> int:
    """Return window in calendar days under POL-RET v4 and RET-8 festive exception."""
    cat = (category or "").lower().strip()
    # Festive sale exception (RET-8): orders placed between 01 Oct 2026 and 15 Oct 2026 for fashion
    if cat == "fashion" and order_placed_date:
        if date(2026, 10, 1) <= order_placed_date <= date(2026, 10, 15):
            return 30

    if cat == "electronics":
        # Electronics delivered before 1 August 2026 keep 10-day window (RET-3)
        if delivered_date and delivered_date < date(2026, 8, 1):
            return 10
        return 7
    elif cat == "fashion":
        return 15
    elif cat in ("home_kitchen", "books_media"):
        return 10
    elif cat == "beauty_sealed":
        return 7
    elif cat in ("grocery", "innerwear", "digital"):
        return 0
    return 7


def get_return_deadline(delivered_date: date, category: str, order_placed_date: date = None) -> date:
    """Calculate return deadline in calendar days from delivery date."""
    window = get_return_window_days(category, order_placed_date, delivered_date)
    return delivered_date + timedelta(days=window)
