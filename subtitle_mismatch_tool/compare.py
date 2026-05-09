import importlib
import unicodedata


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
        # Whisper and Tesseract may emit visually identical Devanagari text with different byte layouts in NFC vs NFD, and normalization prevents false mismatches.
        audio_text = unicodedata.normalize("NFC", str(segment.get("text", ""))).strip()
        subtitle_text = unicodedata.normalize("NFC", str(segment.get("subtitle_text", ""))).strip()

        segment["text"] = audio_text
        segment["subtitle_text"] = subtitle_text

        if not audio_text and not subtitle_text:
            segment["score"] = 1.0
            segment["flagged"] = False
            continue

        if not audio_text and subtitle_text:
            segment["score"] = None
            segment["flagged"] = True
            continue

        if audio_text and not subtitle_text:
            segment["score"] = None
            segment["flagged"] = True
            continue

        # token_sort_ratio handles cases where ASR and OCR contain the same words in different order, so layout-driven word order differences are not treated as mismatches.
        score = fuzz.token_sort_ratio(audio_text, subtitle_text) / 100.0
        segment["score"] = score
        segment["flagged"] = score < threshold

    return segments
