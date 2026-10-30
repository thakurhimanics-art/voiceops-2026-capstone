"""Speech text normalizer adhering to STY-3 and voice clarity standards."""
import re
from datetime import datetime

NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
    10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
    15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
    20: "twenty", 25: "twenty-five", 30: "thirty", 40: "forty", 48: "forty-eight",
    49: "forty-nine", 79: "seventy-nine", 100: "one hundred", 300: "three hundred",
    499: "four hundred and ninety-nine", 999: "nine hundred and ninety-nine",
    10000: "ten thousand"
}

ORDINAL_SUFFIXES = {
    1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th", 8: "8th",
    9: "9th", 10: "10th", 11: "11th", 12: "12th", 13: "13th", 14: "14th", 15: "15th",
    16: "16th", 17: "17th", 18: "18th", 19: "19th", 20: "20th", 21: "21st", 22: "22nd",
    23: "23rd", 24: "24th", 25: "25th", 26: "26th", 27: "27th", 28: "28th", 29: "29th",
    30: "30th", 31: "31st"
}


def normalize_dates_for_speech(text: str) -> str:
    """Normalize ISO and day-month dates to spoken forms: 'the 24th of October 2026'."""
    # Match YYYY-MM-DD
    def replace_iso(match):
        iso_str = match.group(0)
        try:
            dt = datetime.strptime(iso_str, "%Y-%m-%d")
            ord_day = ORDINAL_SUFFIXES.get(dt.day, f"{dt.day}th")
            return f"the {ord_day} of {dt.strftime('%B')} {dt.year}"
        except Exception:
            return iso_str

    text = re.sub(r"\b2026-\d{2}-\d{2}\b", replace_iso, text)

    # Match DD Month YYYY (e.g. 24 October 2026)
    def replace_standard(match):
        day = int(match.group(1))
        month = match.group(2)
        year = match.group(3)
        ord_day = ORDINAL_SUFFIXES.get(day, f"{day}th")
        return f"the {ord_day} of {month} {year}"

    text = re.sub(r"\b(\d{1,2})\s+([A-Za-z]+)\s+(2026)\b", replace_standard, text)
    return text


def normalize_order_ids_for_speech(text: str) -> str:
    """Read order IDs in groups of four digits per STY-3."""
    def replace_oid(match):
        digits = match.group(0).replace(" ", "")
        if len(digits) == 8:
            part1 = " ".join(digits[:4])
            part2 = " ".join(digits[4:])
            return f"{part1}, {part2}"
        return match.group(0)

    # Match 8-digit order IDs or spaced 4+4 digits
    text = re.sub(r"\b\d{4}\s*\d{4}\b", replace_oid, text)
    return text


def normalize_currency_for_speech(text: str) -> str:
    """Convert rupee symbols and amounts to spoken words: 'forty-nine rupees'."""
    def replace_rupees(match):
        raw_num = match.group(1).replace(",", "")
        num = int(raw_num)
        word = NUMBER_WORDS.get(num, str(num))
        return f"{word} rupees"

    text = re.sub(r"₹\s*([0-9,]+)", replace_rupees, text)
    text = re.sub(r"\b([0-9,]+)\s*(?:rupaye|rupees|inr)\b", replace_rupees, text, flags=re.I)
    return text


def clean_text_for_voice(text: str) -> str:
    """Strip section tags, markdown formatting, and brackets for natural speech."""
    # Remove markdown bold/italics
    t = re.sub(r"[*_#`]", "", text)
    # Remove bracketed section IDs like [RET-2], [WAR-1]
    t = re.sub(r"\[[A-Z0-9_\-\.]+\]", "", t)
    # Remove excessive punctuation
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_text_for_speech(text: str) -> str:
    """Full normalization pipeline for voice synthesis."""
    t = clean_text_for_voice(text)
    t = normalize_dates_for_speech(t)
    t = normalize_currency_for_speech(t)
    t = normalize_order_ids_for_speech(t)
    return t


# Spoken numbers mapping (Hindi-English transliterations, Devanagari numerals, English words, Romanized Hindi)
SPOKEN_DIGIT_WORDS = {
    # Hindi-English transliterations in Devanagari (standard Gnani STT output)
    "ज़ीरो": "0", "जीरो": "0", "ज़िरो": "0",
    "वन": "1",
    "टू": "2", "टु": "2",
    "थ्री": "3", "थ्रि": "3",
    "फोर": "4", "फ़ोर": "4",
    "फाइव": "5", "फ़ाइव": "5",
    "सिक्स": "6",
    "सेवन": "7",
    "एट": "8",
    "नाइन": "9",

    # Native Hindi numerals in Devanagari
    "शून्य": "0",
    "एक": "1",
    "दो": "2",
    "तीन": "3",
    "चार": "4",
    "पाँच": "5", "पांच": "5",
    "छह": "6", "छः": "6", "छे": "6",
    "सात": "7",
    "आठ": "8",
    "नौ": "9",

    # English digit words
    "zero": "0", "oh": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",

    # Romanized Hindi digit words
    "shunya": "0",
    "ek": "1",
    "teen": "3",
    "chaar": "4", "char": "4",
    "paanch": "5", "panch": "5",
    "chhah": "6", "che": "6",
    "saat": "7",
    "aath": "8", "ath": "8",
    "nau": "9",
}


def extract_order_id_from_speech(text: str):
    """Extract an 8-digit ZentroMart order ID from digits or spoken number words.
    
    Strictly requires exactly 8 digits; sequences of >8 digits are not truncated.
    """
    if not text:
        return None

    clean_text = text.replace("।", " ").replace("॥", " ")
    tokens = re.findall(r"[a-zA-Z0-9_\u0900-\u0963\u0966-\u097F]+", clean_text.lower())
    current_digits = []
    candidates = []
    for t in tokens:
        if t.isdigit():
            for digit_char in t:
                current_digits.append(digit_char)
        elif t in SPOKEN_DIGIT_WORDS:
            current_digits.append(SPOKEN_DIGIT_WORDS[t])
        else:
            if current_digits:
                if len(current_digits) == 8:
                    candidates.append("".join(current_digits))
                current_digits = []

    if current_digits and len(current_digits) == 8:
        candidates.append("".join(current_digits))

    if candidates:
        return candidates[0]

    return None


def extract_verification_digits(text: str):
    """Extract a 4-digit phone suffix or 6-digit delivery pincode from text or spoken digits."""
    if not text:
        return None

    clean_text = text.replace("।", " ").replace("॥", " ")

    # 1. First check if explicit 6-digit pincode or 4-digit phone suffix exists in ASCII digits
    pincodes = re.findall(r"\b\d{6}\b", clean_text)
    if pincodes:
        return pincodes[0]

    last4 = re.findall(r"\b\d{4}\b", clean_text)
    if last4:
        return last4[-1]

    digit_chars = "".join(ch for ch in clean_text if "0" <= ch <= "9")
    if len(digit_chars) in (4, 6):
        return digit_chars

    # 2. Extract from spoken digit words (Hindi Devanagari, English, or Romanized)
    tokens = re.findall(r"[a-zA-Z0-9_\u0900-\u0963\u0966-\u097F]+", clean_text.lower())
    all_digits = []
    for t in tokens:
        if t.isdigit():
            for d in t:
                all_digits.append(d)
        elif t in SPOKEN_DIGIT_WORDS:
            all_digits.append(SPOKEN_DIGIT_WORDS[t])

    if len(all_digits) in (4, 6):
        return "".join(all_digits)

    # In case of framing words like 'last four digits are...' (5 digits starting with 4) or 'last six digits are...' (7 digits starting with 6)
    if len(all_digits) == 5 and all_digits[0] == "4":
        return "".join(all_digits[1:])
    if len(all_digits) == 7 and all_digits[0] == "6":
        return "".join(all_digits[1:])

    return None


