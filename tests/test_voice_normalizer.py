"""Unit tests for STY-3 speech text normalization."""
from src.step4_voice.normalizer import (
    normalize_dates_for_speech,
    normalize_order_ids_for_speech,
    normalize_currency_for_speech,
    clean_text_for_voice,
    normalize_text_for_speech,
)


def test_normalize_dates_iso():
    # Test YYYY-MM-DD expansion to ordinal day, month name, and year
    text = "Your refund will be credited by 2026-10-24."
    out = normalize_dates_for_speech(text)
    assert out == "Your refund will be credited by the 24th of October 2026."

    text2 = "Order placed on 2026-10-01."
    out2 = normalize_dates_for_speech(text2)
    assert out2 == "Order placed on the 1st of October 2026."

    text3 = "Delivery date is 2026-10-22."
    out3 = normalize_dates_for_speech(text3)
    assert out3 == "Delivery date is the 22nd of October 2026."


def test_normalize_dates_calendar():
    # Test DD Month YYYY expansion
    text = "The refund was started on 17 October 2026."
    out = normalize_dates_for_speech(text)
    assert out == "The refund was started on the 17th of October 2026."

    text2 = "Delivered on 3 October 2026."
    out2 = normalize_dates_for_speech(text2)
    assert out2 == "Delivered on the 3rd of October 2026."


def test_normalize_currency_symbol():
    # Test conversion of rupee symbols and amounts to words
    text = "The reverse pickup fee is ₹49."
    out = normalize_currency_for_speech(text)
    assert out == "The reverse pickup fee is forty-nine rupees."

    text2 = "Late delivery credit is ₹79."
    out2 = normalize_currency_for_speech(text2)
    assert out2 == "Late delivery credit is seventy-nine rupees."

    text3 = "Damaged laptop valued over ₹10,000."
    out3 = normalize_currency_for_speech(text3)
    assert out3 == "Damaged laptop valued over ten thousand rupees."


def test_normalize_currency_words():
    # Test conversion of text-specified rupee amounts
    text = "Annual membership is 999 rupees."
    out = normalize_currency_for_speech(text)
    assert out == "Annual membership is nine hundred and ninety-nine rupees."

    text2 = "Refund of 499 inr initiated."
    out2 = normalize_currency_for_speech(text2)
    assert out2 == "Refund of four hundred and ninety-nine rupees initiated."


def test_normalize_order_ids():
    # Test grouping 8-digit order IDs into 4-digit spoken chunks
    text = "Your order number is 89782837."
    out = normalize_order_ids_for_speech(text)
    assert out == "Your order number is 8 9 7 8, 2 8 3 7."

    # Test spaced 4+4 order IDs
    text2 = "Looking up order 1591 1102."
    out2 = normalize_order_ids_for_speech(text2)
    assert out2 == "Looking up order 1 5 9 1, 1 1 0 2."

    # Test short 4-digit numbers are NOT modified as order IDs
    text3 = "Last 4 digits are 4533."
    out3 = normalize_order_ids_for_speech(text3)
    assert out3 == "Last 4 digits are 4533."


def test_clean_text_for_voice():
    # Test stripping markdown bold/italics
    text = "This item is **non-returnable** under policy."
    out = clean_text_for_voice(text)
    assert out == "This item is non-returnable under policy."

    # Test stripping bracketed section IDs
    text2 = "Per section [RET-2] and [REF-1], your return is accepted."
    out2 = clean_text_for_voice(text2)
    assert "[RET-2]" not in out2
    assert "[REF-1]" not in out2


def test_unchanged_ordinary_text():
    # Text without special tokens should remain unaltered
    text = "Namaste! Main ZentroMart ka AI support assistant hoon."
    out = normalize_text_for_speech(text)
    assert out == "Namaste! Main ZentroMart ka AI support assistant hoon."

    text2 = "How can I help you with your account today?"
    out2 = normalize_text_for_speech(text2)
    assert out2 == "How can I help you with your account today?"


def test_combined_normalization_pipeline():
    # Test end-to-end normalization pipeline
    text = "Order 89782837 was delivered on 2026-10-14. Under **[RET-2]**, reverse pickup fee is ₹49."
    out = normalize_text_for_speech(text)
    assert "8 9 7 8, 2 8 3 7" in out
    assert "the 14th of October 2026" in out
    assert "forty-nine rupees" in out
    assert "[RET-2]" not in out
    assert "**" not in out
