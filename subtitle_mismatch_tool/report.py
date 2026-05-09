import importlib
import os
from datetime import datetime


def _compute_report_metrics(segments):
    """Compute summary metrics used by the HTML report.

    Parameters:
        segments: Processed segment list with score and flagged fields.

    Returns:
        Dictionary of aggregate counters and similarity metrics.
    """
    flagged_count = sum(1 for segment in segments if segment.get("flagged"))
    ok_count = sum(1 for segment in segments if not segment.get("flagged"))
    missing_subtitles = sum(
        1
        for segment in segments
        if segment.get("score") is None and str(segment.get("text", "")).strip() and not str(segment.get("subtitle_text", "")).strip()
    )
    missing_speech = sum(
        1
        for segment in segments
        if segment.get("score") is None and not str(segment.get("text", "")).strip() and str(segment.get("subtitle_text", "")).strip()
    )
    scored_values = [segment.get("score") for segment in segments if segment.get("score") is not None]
    average_similarity = (sum(scored_values) / len(scored_values)) if scored_values else 0.0
    return {
        "flagged_count": flagged_count,
        "ok_count": ok_count,
        "missing_subtitles": missing_subtitles,
        "missing_speech": missing_speech,
        "average_similarity": average_similarity,
    }


def generate_report(segments, output_path, video_filename, threshold):
    """Render an HTML mismatch report from analyzed subtitle segments.

    Parameters:
        segments: Full list of processed segments with score and flagged fields.
        output_path: Destination path for the generated HTML report.
        video_filename: Source video filename shown in the report header.
        threshold: Similarity threshold used to flag review rows.

    Returns:
        None.
    """
    jinja2 = importlib.import_module("jinja2")

    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )
    template = environment.get_template("report.html")

    report_metrics = _compute_report_metrics(segments)
    rendered_html = template.render(
        segments=segments,
        video_filename=video_filename,
        total_count=len(segments),
        flagged_count=report_metrics["flagged_count"],
        ok_count=report_metrics["ok_count"],
        missing_subtitles=report_metrics["missing_subtitles"],
        missing_speech=report_metrics["missing_speech"],
        average_similarity=report_metrics["average_similarity"],
        threshold=threshold,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    output_directory = os.path.dirname(output_path)
    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as report_file:
        report_file.write(rendered_html)
