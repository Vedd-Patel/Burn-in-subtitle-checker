import importlib
import os


def _compute_frame_number(segment, fps, total_frames):
    """Convert a segment midpoint into a clamped frame number.

    Parameters:
        segment: Segment dictionary containing start and end timestamps.
        fps: Frames per second for the opened video.
        total_frames: Total frames reported by the video stream.

    Returns:
        A frame index clamped to valid video bounds.
    """
    # Seek to midpoint rather than segment start because subtitle text may appear slightly after speech starts due to editorial timing offsets.
    midpoint = (segment["start"] + segment["end"]) / 2
    frame_number = int(round(midpoint * fps))
    max_frame = max(total_frames - 1, 0)
    return max(0, min(frame_number, max_frame))


def _prepare_subtitle_region(frame, video_height, cv2, np):
    """Crop and preprocess the subtitle region from a frame for OCR.

    Parameters:
        frame: Frame image returned by OpenCV.
        video_height: Height reported by OpenCV metadata.
        cv2: Imported cv2 module.
        np: Imported numpy module.

    Returns:
        A thresholded subtitle image, or None when the crop is empty.
    """
    effective_height = video_height if video_height > 0 else frame.shape[0]
    # The bottom 15% maps to the subtitle safe zone from EBU R95 that most broadcast subtitle workflows follow.
    subtitle_region = frame[int(effective_height * 0.85) :, :]
    if subtitle_region.size == 0:
        return None

    grayscale_region = cv2.cvtColor(subtitle_region, cv2.COLOR_BGR2GRAY)
    # Tesseract recognizes text more reliably when glyphs are dark on a light background, so bright regions are inverted first.
    mean_brightness = float(np.mean(grayscale_region))
    if mean_brightness > 127:
        grayscale_region = cv2.bitwise_not(grayscale_region)

    _, thresholded_region = cv2.threshold(grayscale_region, 150, 255, cv2.THRESH_BINARY)
    return thresholded_region


def _extract_text_from_frame(cap, frame_number, video_height, cv2, np, pytesseract):
    """Seek to a frame, preprocess subtitle area, and run OCR.

    Parameters:
        cap: OpenCV VideoCapture object.
        frame_number: Frame index to read.
        video_height: Height reported by OpenCV metadata.
        cv2: Imported cv2 module.
        np: Imported numpy module.
        pytesseract: Imported pytesseract module.

    Returns:
        Subtitle text for the frame, or an empty string when read/crop fails.
    """
    seek_ok = cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    if not seek_ok:
        return ""

    read_ok, frame = cap.read()
    if not read_ok or frame is None:
        return ""

    thresholded_region = _prepare_subtitle_region(frame, video_height, cv2, np)
    if thresholded_region is None:
        return ""

    try:
        # PSM 6 treats this crop as one uniform text block, which fits subtitle strips where layout analysis adds little value.
        return pytesseract.image_to_string(
            thresholded_region,
            lang="hin+kan+eng",
            config="--psm 6 --oem 3",
        ).strip()
    except pytesseract.pytesseract.TesseractError as error:
        if "failed loading language" in str(error).lower():
            raise RuntimeError(
                "A required Tesseract language pack is missing. Install with: sudo apt-get install tesseract-ocr-hin tesseract-ocr-kan "
                f"Original error: {error}"
            ) from error
        raise


def extract_subtitle_text(video_path, segments):
    """Extract subtitle text from midpoint frames for each transcript segment.

    Parameters:
        video_path: Path to the input video file.
        segments: List of segment dictionaries with start and end timestamps.

    Returns:
        The same segments list with subtitle_text added to each segment dictionary.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    cv2 = importlib.import_module("cv2")
    np = importlib.import_module("numpy")
    pytesseract = importlib.import_module("pytesseract")

    try:
        pytesseract.get_tesseract_version()
    except (EnvironmentError, FileNotFoundError) as error:
        raise RuntimeError(
            "Tesseract is not installed. Install it and the Hindi and Kannada language packs before running this tool."
        ) from error

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(
            "Could not open video file for subtitle extraction. Verify it with 'ffprobe -i <video>'."
        )

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0.0:
            raise ValueError(
                "Could not read video FPS. The video file may be corrupted. Verify it with 'ffprobe -i <video>'."
            )

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        for segment in segments:
            frame_number = _compute_frame_number(segment, fps, total_frames)
            segment["subtitle_text"] = _extract_text_from_frame(
                cap,
                frame_number,
                video_height,
                cv2,
                np,
                pytesseract,
            )

        return segments
    finally:
        cap.release()
