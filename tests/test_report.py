from subtitle_mismatch_tool.report import generate_report


def test_generate_report_writes_html(tmp_path):
    segments = [
        {
            "start": 10.0,
            "end": 10.4,
            "text": "वो कहाँ गई थी",
            "subtitle_text": "वो कहाँ गया था",
            "score": 0.61,
            "flagged": True,
            "status": "REVIEW",
            "reason": "low similarity",
        },
        {
            "start": 45.4,
            "end": 46.0,
            "text": "ठीक है भाई",
            "subtitle_text": "ठीक है भाई",
            "score": 1.0,
            "flagged": False,
            "status": "OK",
            "reason": "high similarity",
        },
    ]
    output_path = tmp_path / "report.html"

    generate_report(segments, str(output_path), "demo_clip.mp4", 0.75)

    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8") as report_file:
        html = report_file.read()

    assert "Audio-Subtitle Alignment Report" in html
    assert "demo_clip.mp4" in html
    assert "REVIEW" in html
    assert "OK" in html
