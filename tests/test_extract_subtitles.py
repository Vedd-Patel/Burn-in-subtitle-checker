from unittest.mock import MagicMock, patch

import pytest

from subtitle_mismatch_tool import extract_subtitles


class _DummyFrame:
    shape = (100, 200, 3)

    def __getitem__(self, _key):
        return "crop"


def _mocked_cap_with_frame(frame_ok=True):
    capture = MagicMock()
    if frame_ok:
        capture.read.return_value = (True, _DummyFrame())
    else:
        capture.read.return_value = (False, None)
    return capture


def test_midpoint_calculation():
    segments = [{"start": 10.0, "end": 12.0, "text": "hello"}]
    capture = _mocked_cap_with_frame(frame_ok=False)

    with patch("subtitle_mismatch_tool.extract_subtitles.cv2.VideoCapture", return_value=capture):
        extract_subtitles.extract_subtitles("video.mp4", segments)

    assert capture.set.call_count == 1
    assert capture.set.call_args[0][1] == pytest.approx(11000.0)


def test_failed_frame_sets_empty_string():
    segments = [{"start": 0.0, "end": 1.0, "text": "sample"}]
    capture = _mocked_cap_with_frame(frame_ok=False)

    with patch("subtitle_mismatch_tool.extract_subtitles.cv2.VideoCapture", return_value=capture):
        output = extract_subtitles.extract_subtitles("video.mp4", segments)

    assert output[0]["subtitle_text"] == ""


def test_ocr_result_is_stripped():
    segments = [{"start": 0.0, "end": 1.0, "text": "sample"}]
    capture = _mocked_cap_with_frame(frame_ok=True)

    with (
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.VideoCapture", return_value=capture),
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.cvtColor", return_value="gray"),
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.threshold", return_value=(0, "binary")),
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.resize", return_value="upscaled"),
        patch(
            "subtitle_mismatch_tool.extract_subtitles.pytesseract.image_to_string",
            return_value="  वो कहाँ गई थी  \n",
        ),
    ):
        output = extract_subtitles.extract_subtitles("video.mp4", segments)

    assert output[0]["subtitle_text"] == "वो कहाँ गई थी"


def test_tesseract_not_found_raises_runtime_error():
    segments = [{"start": 0.0, "end": 1.0, "text": "sample"}]
    capture = _mocked_cap_with_frame(frame_ok=True)

    with (
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.VideoCapture", return_value=capture),
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.cvtColor", return_value="gray"),
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.threshold", return_value=(0, "binary")),
        patch("subtitle_mismatch_tool.extract_subtitles.cv2.resize", return_value="upscaled"),
        patch(
            "subtitle_mismatch_tool.extract_subtitles.pytesseract.image_to_string",
            side_effect=EnvironmentError("missing tesseract"),
        ),
    ):
        with pytest.raises(RuntimeError, match="Tesseract"):
            extract_subtitles.extract_subtitles("video.mp4", segments)
