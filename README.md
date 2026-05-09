# Lightweight Audio-Subtitle Mismatch Flagging Tool

This submission is a focused demo for PlanetRead DMP 2026 and implements **Module 3: Mismatch Detection and HTML Report Generation**.

## What This Demo Includes

1. Executable Module 3 scripts:
   - `subtitle_mismatch_tool/compare.py`
   - `subtitle_mismatch_tool/report.py`
   - `subtitle_mismatch_tool/main.py`
   - `subtitle_mismatch_tool/templates/report.html`
2. Sample input artifact:
   - `subtitle_mismatch_tool/sample_output/module3_sample_segments_input.json`
3. Corresponding sample output artifact:
   - `subtitle_mismatch_tool/sample_output/module3_sample_report_output.html`

## Run the Demo

Install dependencies:

```bash
pip install -r subtitle_mismatch_tool/requirements.txt
```

Run Module 3 on the sample input:

```bash
python3 subtitle_mismatch_tool/main.py subtitle_mismatch_tool/sample_output/module3_sample_segments_input.json --video-name demo_clip.mp4 --threshold 0.75 --output mismatch_report.html
```

## Input Format

The input file must be a JSON list where each item has:

1. `start` (float, seconds)
2. `end` (float, seconds)
3. `text` (audio transcript string)
4. `subtitle_text` (OCR subtitle string)

## Known Limitations

1. Similarity scoring is lexical and may still flag semantically equivalent paraphrases.
2. Token sorting reduces order sensitivity, but does not model context or speaker intent.
3. The demo assumes upstream transcription and OCR text are already available.

## Next Improvements

1. Add optional semantic similarity scoring to reduce lexical false positives.
2. Add confidence-weighted rules for empty-text edge cases.
3. Add regression tests for multilingual normalization and score thresholds.
