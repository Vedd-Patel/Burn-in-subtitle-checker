import importlib
import os
from datetime import datetime


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

    flagged_count = sum(1 for segment in segments if segment.get("flagged"))
    rendered_html = template.render(
        segments=segments,
        video_filename=video_filename,
        total_count=len(segments),
        flagged_count=flagged_count,
        threshold=threshold,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    with open(output_path, "w", encoding="utf-8") as report_file:
        report_file.write(rendered_html)
