import json
import os

import pytest

from subtitle_mismatch_tool import main


def test_load_segments_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        main._load_segments("does-not-exist.json")


def test_load_segments_rejects_invalid_shape(tmp_path):
    invalid_file = os.path.join(tmp_path, "invalid.json")
    with open(invalid_file, "w", encoding="utf-8") as test_file:
        json.dump({"not": "a-list"}, test_file)

    with pytest.raises(ValueError):
        main._load_segments(invalid_file)


def test_main_generates_output_report(tmp_path, monkeypatch):
    input_file = os.path.join(tmp_path, "segments.json")
    output_file = os.path.join(tmp_path, "result.html")
    segments = [
        {"start": 0.0, "end": 0.5, "text": "नमस्ते", "subtitle_text": "नमस्ते"},
        {"start": 1.0, "end": 1.5, "text": "भारत की समस्या", "subtitle_text": "भारत की परेशानी"},
    ]
    with open(input_file, "w", encoding="utf-8") as test_file:
        json.dump(segments, test_file, ensure_ascii=False)

    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            input_file,
            "--video-name",
            "demo.mp4",
            "--threshold",
            "0.75",
            "--output",
            output_file,
        ],
    )

    main.main()
    assert os.path.exists(output_file)
