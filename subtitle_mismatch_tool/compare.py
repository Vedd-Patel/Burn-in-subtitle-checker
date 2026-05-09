import importlib
import unicodedata


def _normalize_text(text_value):
    """Normalize and trim text to make Unicode comparisons reliable.

    Parameters:
        text_value: Raw text value from input data.

    Returns:
        Cleaned string normalized to NFC form.
    """
    # Whisper and Tesseract may emit visually identical Devanagari text with different byte layouts in NFC vs NFD, and normalization prevents false mismatches.
    return unicodedata.normalize("NFC", str(text_value)).strip()


def compute_similarity(segments, threshold=0.75):
    """Compute similarity scores between ASR text and OCR subtitle text.

    Parameters:
        segments: List of segment dictionaries containing text and subtitle_text.
        threshold: Minimum score required to avoid flagging a segment.

    Returns:
        The same segments list with score and flagged keys added to each segment.
    """
    fuzz = importlib.import_module("rapidfuzz.fuzz")

    for segment in segments:
        audio_text = _normalize_text(segment.get("text", ""))
        subtitle_text = _normalize_text(segment.get("subtitle_text", ""))

        segment["text"] = audio_text
        segment["subtitle_text"] = subtitle_text

        if not audio_text and not subtitle_text:
            segment["score"] = 1.0
            segment["flagged"] = False
            segment["status"] = "OK"
            segment["reason"] = "silence with no subtitle"
            continue

        if not audio_text and subtitle_text:
            segment["score"] = None
            segment["flagged"] = True
            segment["status"] = "REVIEW"
            segment["reason"] = "missing speech"
            continue

        if audio_text and not subtitle_text:
            segment["score"] = None
            segment["flagged"] = True
            segment["status"] = "REVIEW"
            segment["reason"] = "missing subtitle"
            continue

        # token_sort_ratio handles cases where ASR and OCR contain the same words in different order, so layout-driven word order differences are not treated as mismatches.
        score = fuzz.token_sort_ratio(audio_text, subtitle_text) / 100.0
        segment["score"] = score
        segment["flagged"] = score < threshold
        segment["status"] = "REVIEW" if segment["flagged"] else "OK"
        segment["reason"] = "low similarity" if segment["flagged"] else "high similarity"

    return segments
