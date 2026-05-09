import pytest
from subtitle_mismatch_tool.compare import compute_similarity


def test_compute_similarity_handles_empty_cases():
    segments = [
        {"start": 0.0, "end": 1.0, "text": "", "subtitle_text": ""},
        {"start": 1.0, "end": 2.0, "text": "", "subtitle_text": "नमस्ते"},
        {"start": 2.0, "end": 3.0, "text": "नमस्ते", "subtitle_text": ""},
    ]

    output = compute_similarity(segments, threshold=0.75)

    assert output[0]["score"] == pytest.approx(1.0)
    assert output[0]["flagged"] is False
    assert output[0]["status"] == "OK"

    assert output[1]["score"] is None
    assert output[1]["flagged"] is True
    assert output[1]["reason"] == "missing speech"

    assert output[2]["score"] is None
    assert output[2]["flagged"] is True
    assert output[2]["reason"] == "missing subtitle"


def test_compute_similarity_scores_non_empty_text():
    segments = [
        {"start": 0.0, "end": 1.0, "text": "नमस्कार दोस्तों", "subtitle_text": "नमस्कार दोस्तों"},
        {"start": 1.0, "end": 2.0, "text": "भारत की समस्या", "subtitle_text": "भारत की परेशानी"},
    ]

    output = compute_similarity(segments, threshold=0.90)

    assert output[0]["score"] == pytest.approx(1.0)
    assert output[0]["flagged"] is False
    assert output[0]["status"] == "OK"

    assert output[1]["score"] is not None
    assert output[1]["score"] < 0.90
    assert output[1]["flagged"] is True
    assert output[1]["status"] == "REVIEW"
