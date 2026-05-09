import argparse
import os
import sys

from subtitle_mismatch_tool.compare import compute_similarity
from subtitle_mismatch_tool.extract_subtitles import extract_subtitle_text
from subtitle_mismatch_tool.report import generate_report
from subtitle_mismatch_tool.transcribe import transcribe_audio


def build_parser():
    """Create and return the command-line argument parser.

    Parameters:
        None.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Flag likely mismatches between spoken audio and burned-in subtitles."
    )
    parser.add_argument(
        "video",
        help="Path to the video file to analyze. MP4, MKV, AVI, and MOV are supported.",
    )
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size. Larger models are more accurate but slower. The small model works well for Hindi and Kannada without requiring a GPU.",
    )
    parser.add_argument(
        "--threshold",
        default=0.75,
        type=float,
        help="Similarity score below which a segment is flagged for review. Value between 0.0 and 1.0. Lower values flag only obvious mismatches, higher values catch subtle ones at the cost of more false positives.",
    )
    parser.add_argument(
        "--output",
        default="mismatch_report.html",
        help="Output path for the HTML report.",
    )
    return parser


def main():
    """Run the audio-subtitle mismatch detection pipeline from the CLI.

    Parameters:
        None.

    Returns:
        None.
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        print("[1/4] Transcribing audio with Whisper...")
        segments = transcribe_audio(args.video, model_size=args.model)
        print(f"Found {len(segments)} segments from audio transcription.")

        print("[2/4] Extracting subtitle text with OCR...")
        segments = extract_subtitle_text(args.video, segments)
        print(f"Processed {len(segments)} frames for subtitle OCR.")

        print("[3/4] Computing similarity scores...")
        segments = compute_similarity(segments, threshold=args.threshold)

        print("[4/4] Generating HTML report...")
        video_filename = os.path.basename(args.video)
        generate_report(
            segments=segments,
            output_path=args.output,
            video_filename=video_filename,
            threshold=args.threshold,
        )
        print(f"Report saved to: {args.output}")

        total_segments = len(segments)
        flagged_segments = sum(1 for segment in segments if segment.get("flagged"))
        flagged_percentage = (flagged_segments / total_segments * 100.0) if total_segments else 0.0
        print(
            f"Summary: {total_segments} segments analyzed, {flagged_segments} flagged ({flagged_percentage:.1f}%)."
        )
    except RuntimeError as error:
        print(str(error))
        sys.exit(1)
    except ValueError as error:
        print(str(error))
        sys.exit(1)
    except FileNotFoundError as error:
        print(str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
