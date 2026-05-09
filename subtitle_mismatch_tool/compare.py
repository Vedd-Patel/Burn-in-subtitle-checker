import difflib
import importlib
import string
import unicodedata


def _normalize_text(text_value):
    """Normalize text: remove punctuation and make Unicode comparisons reliable.

    Parameters:
        text_value: Raw text value from input data.

    Returns:
        Cleaned string normalized to NFC form, without punctuation.
    """
    if text_value is None:
        return ""
        
    # 1. Normalize to NFC (prevents false Devanagari mismatches due to byte layouts)
    text = unicodedata.normalize("NFC", str(text_value)).strip()
    
    # 2. Remove standard punctuation and Devanagari Dandas ('।' and '॥')
    # This prevents the fuzzy matcher from docking points just because of a comma or period
    translator = str.maketrans('', '', string.punctuation + '।॥')
    text = text.translate(translator)
    
    # 3. Collapse multiple spaces into one
    return " ".join(text.split())


def compute_similarity(segments, threshold=0.75):
    """Compute similarity scores between ASR text and OCR subtitle text.

    Parameters:
        segments: List of segment dictionaries containing text and subtitle_text.
        threshold: Minimum score required to avoid flagging a segment.

    Returns:
        The same segments list with score, flagged, cps, and diff keys added.
    """
    fuzz = importlib.import_module("rapidfuzz.fuzz")

    for segment in segments:
        # Calculate subtitle duration and Characters Per Second (CPS) for accessibility warning
        duration = segment.get("end", 0.0) - segment.get("start", 0.0)
        
        # Use raw text length for CPS (what the user actually sees on screen)
        raw_subtitle = str(segment.get("subtitle_text", "")).strip()
        cps = len(raw_subtitle) / duration if duration > 0 else 0.0
        segment["cps"] = cps
        segment["speed_warning"] = cps > 20.0  # Flag if flashing too fast for standard literacy
        
        # Normalize text for accurate matching
        audio_text = _normalize_text(segment.get("text", ""))
        subtitle_text = _normalize_text(raw_subtitle)

        segment["text"] = audio_text
        segment["subtitle_text"] = subtitle_text

        # Edge cases: missing text
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

        # O(1) Short-circuit: Instantly approve identical strings to save processing time
        if audio_text == subtitle_text:
            segment["score"] = 1.0
            segment["flagged"] = False
            segment["status"] = "OK"
            segment["reason"] = "perfect match"
            continue

        # token_sort_ratio handles cases where ASR and OCR contain the same words in different order
        score = fuzz.token_sort_ratio(audio_text, subtitle_text) / 100.0
        segment["score"] = score
        segment["flagged"] = score < threshold
        segment["status"] = "REVIEW" if segment["flagged"] else "OK"
        segment["reason"] = "low similarity" if segment["flagged"] else "high similarity"

        # Generate inline HTML diff for easy reading on flagged rows
        if segment["flagged"]:
            matcher = difflib.SequenceMatcher(None, audio_text.split(), subtitle_text.split())
            diff_audio = []
            diff_sub = []
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    diff_audio.append(" ".join(audio_text.split()[i1:i2]))
                    diff_sub.append(" ".join(subtitle_text.split()[j1:j2]))
                elif tag in ('replace', 'delete', 'insert'):
                    # Highlight mismatches with HTML <mark> tags
                    if i1 != i2:
                        diff_audio.append(f"<mark style='background: #FEE2E2; color: #991B1B; padding: 0 2px; border-radius: 3px;'>{' '.join(audio_text.split()[i1:i2])}</mark>")
                    if j1 != j2:
                        diff_sub.append(f"<mark style='background: #FEF3C7; color: #92400E; padding: 0 2px; border-radius: 3px;'>{' '.join(subtitle_text.split()[j1:j2])}</mark>")
            
            segment["text_diff"] = " ".join(diff_audio)
            segment["subtitle_diff"] = " ".join(diff_sub)

    return segments
