import argparse
import json
import os
import sys

try:
    from subtitle_mismatch_tool.compare import compute_similarity
    from subtitle_mismatch_tool.report import generate_report
except ImportError:
    from compare import compute_similarity
    from report import generate_report


def build_parser():
    """Build the CLI parser for Module 3 demo execution.

    Parameters:
        None.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Run Module 3 demo: mismatch detection and HTML report generation."
    )
    parser.add_argument(
        "segments_json",
        help="Path to JSON containing timed segments with text and subtitle_text fields.",
    )
    parser.add_argument(
        "--video-name",
        default="demo_clip.mp4",
        help="Video filename label shown in the generated report.",
    )
    parser.add_argument(
        "--threshold",
        default=0.75,
        type=float,
        help="Similarity score below which a segment is flagged for review. Value between 0.0 and 1.0.",
    )
    parser.add_argument(
        "--output",
        default="mismatch_report.html",
        help="Output path for the HTML report.",
    )
    return parser


def _load_segments(path):
    """Load segments from a JSON file and ensure it is a list.

    Parameters:
        path: File path for the segments JSON file.

    Returns:
        Segment list loaded from JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as input_file:
        loaded = json.load(input_file)

    if not isinstance(loaded, list):
        raise ValueError("Input JSON must be a list of segment objects.")
    for index, segment in enumerate(loaded):
        if not isinstance(segment, dict):
            raise ValueError(f"Segment at index {index} is not a JSON object.")
        for key_name in ["start", "end", "text", "subtitle_text"]:
            if key_name not in segment:
                raise ValueError(f"Segment at index {index} is missing required key '{key_name}'.")
    return loaded


def main():
    """Run the Module 3 demo pipeline from the command line.

    Parameters:
        None.

    Returns:
        None.
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.threshold < 0.0 or args.threshold > 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0.")

        print("[1/3] Loading segment input...")
        segments = _load_segments(args.segments_json)
        print(f"Loaded {len(segments)} segments.")

        print("[2/3] Computing similarity scores...")
        segments = compute_similarity(segments, threshold=args.threshold)

        print("[3/3] Generating HTML report...")
        generate_report(
            segments=segments,
            output_path=args.output,
            video_filename=args.video_name,
            threshold=args.threshold,
        )
        print(f"Report saved to: {args.output}")

        flagged_segments = sum(1 for segment in segments if segment.get("flagged"))
        total_segments = len(segments)
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
