import importlib
import os
import subprocess
import tempfile


def _extract_audio_to_wav(video_path, wav_path):
    """Extract audio from a video into a mono 16kHz WAV file.

    Parameters:
        video_path: Path to the source video.
        wav_path: Path where the WAV audio should be written.

    Returns:
        None.
    """
    # 16kHz mono WAV matches Whisper's training format, and resampling elsewhere adds an unnecessary conversion step that can introduce artifacts.
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-ar",
        "16000",
        "-ac",
        "1",
        "-vn",
        "-f",
        "wav",
        wav_path,
    ]

    try:
        subprocess.run(
            ffmpeg_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "ffmpeg is not installed or not on PATH. Install it from https://ffmpeg.org and make sure it is accessible from the terminal."
        ) from error
    except subprocess.CalledProcessError as error:
        raise ValueError(
            "Could not extract audio from the video. Run 'ffprobe -i <video>' to check whether an audio stream exists."
        ) from error


def transcribe_audio(video_path, model_size="small"):
    """Transcribe a video's audio into timed text segments.

    Parameters:
        video_path: Path to the input video file.
        model_size: Whisper model size to load.

    Returns:
        A list of dictionaries with start, end, and text values for each segment.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    temp_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name

        _extract_audio_to_wav(video_path, temp_audio_path)

        whisper = importlib.import_module("whisper")
        model = whisper.load_model(model_size)
        # fp16 is half-precision floating point, which needs CUDA and can silently produce incorrect results on CPU-only machines.
        result = model.transcribe(temp_audio_path, fp16=False)
        segments = result.get("segments", [])
        if not segments:
            return []

        # We return only the fields the pipeline needs so later modules do not depend on Whisper's internal segment object structure.
        return [
            {
                "start": float(segment.get("start", 0.0)),
                "end": float(segment.get("end", 0.0)),
                "text": str(segment.get("text", "")),
            }
            for segment in segments
        ]
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
