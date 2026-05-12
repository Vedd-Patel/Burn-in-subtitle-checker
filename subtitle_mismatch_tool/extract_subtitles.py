"""Subtitle extraction via OCR from midpoint video frames."""

from types import SimpleNamespace

try:
    import cv2
except ImportError:
    cv2 = SimpleNamespace(
        CAP_PROP_POS_MSEC=0,
        COLOR_BGR2GRAY=0,
        THRESH_BINARY=0,
        THRESH_OTSU=0,
        INTER_CUBIC=0,
        VideoCapture=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            EnvironmentError("OpenCV not found.")
        ),
        cvtColor=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            EnvironmentError("OpenCV not found.")
        ),
        threshold=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            EnvironmentError("OpenCV not found.")
        ),
        resize=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            EnvironmentError("OpenCV not found.")
        ),
    )

try:
    import pytesseract
except ImportError:
    pytesseract = SimpleNamespace(
        image_to_string=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            EnvironmentError("Tesseract not found.")
        )
    )


_TESSERACT_INSTALL_MESSAGE = (
    "Tesseract not found. Install it and the hin+kan language packs.\n"
    "Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-kan\n"
    "macOS:  brew install tesseract && brew install tesseract-lang"
)


def _segment_midpoint(segment: dict) -> float:
    """Compute midpoint time for a segment.

    Parameters:
        segment: Segment dictionary containing start and end timestamps.

    Returns:
        Midpoint timestamp in seconds.
    """
    return (float(segment["start"]) + float(segment["end"])) / 2.0


def _preprocess_frame(frame):
    """Prepare subtitle-region frame for OCR.

    Parameters:
        frame: Video frame read from OpenCV.

    Returns:
        Processed 2x-upscaled binary image focused on subtitle region.
    """
    frame_height = frame.shape[0]
    crop = frame[int(frame_height * 0.85) : frame_height, :]
    grayscale = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _threshold, binary = cv2.threshold(
        grayscale, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return cv2.resize(binary, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)


def _raise_tesseract_runtime_error(_error: Exception) -> None:
    raise RuntimeError(_TESSERACT_INSTALL_MESSAGE)


def extract_subtitles(video_path: str, segments: list[dict]) -> list[dict]:
    """Extract burned-in subtitle text for each segment via OCR.

    Parameters:
        video_path: Path to the source video file.
        segments: Segment list containing at least start, end, and text keys.

    Returns:
        Same segment list with subtitle_text added to each segment.
    """
    capture = cv2.VideoCapture(video_path)
    total_segments = len(segments)
    extracted_count = 0

    try:
        for segment in segments:
            midpoint_seconds = _segment_midpoint(segment)
            print(f"  Extracting subtitle from frame at {midpoint_seconds:.2f}s ...")

            capture.set(cv2.CAP_PROP_POS_MSEC, midpoint_seconds * 1000.0)
            ok, frame = capture.read()
            if not ok or frame is None:
                segment["subtitle_text"] = ""
                continue

            processed_frame = _preprocess_frame(frame)
            try:
                ocr_text = pytesseract.image_to_string(
                    processed_frame, lang="hin+kan+eng", config="--psm 6"
                )
            except EnvironmentError as error:
                _raise_tesseract_runtime_error(error)

            segment["subtitle_text"] = ocr_text.strip()
            extracted_count += 1
    finally:
        capture.release()

    print(f"Extracted subtitles from {extracted_count}/{total_segments} frames.")
    return segments
