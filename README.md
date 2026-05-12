# Lightweight Audio-Subtitle Mismatch Flagging Tool

This submission is a focused on implementing **Module 3: Mismatch Detection and HTML Report Generation**. 

Designed with the needs of real-world video editors and literacy learners in mind, this module goes beyond basic lexical comparison by generating an **Interactive QA Studio** for rapid validation.

## What This Web App Does

This tool takes extracted audio transcripts and OCR subtitles, compares them for accuracy, and generates an interactive, offline-first HTML dashboard. It allows Quality Assurance (QA) teams to instantly pinpoint and verify subtitle errors without manually scrubbing through video files.

### Key Features

* **Interactive Local Video Sync:** Reviewers can load a local `.mp4` video directly into the browser. Clicking any flagged row instantly jumps the video to that exact millisecond for immediate verification. The video is never uploaded to the internet.
* **Accessibility Flagging (CPS):** Calculates Characters Per Second (CPS) and warns if a subtitle flashes too quickly (> 20 CPS), directly supporting PlanetRead's Same Language Subtitling (SLS) literacy goals.
* **Inline Word-Level Diffing:** Isolates and highlights the exact mismatched words using sequence matching, allowing reviewers to instantly spot the error instead of reading the entire sentence twice.
* **NLE Integration (CSV Export):** Editors can export flagged timestamps directly to CSV to be used as timeline markers in editing software like Premiere Pro or DaVinci Resolve.
* **Real-time Filtering & Search:** Instantly filter by `Review Only`, `Missing Data`, or search for specific Hindi/Kannada dialogue without reloading the page.

## How It Works (The Pipeline)

1.  **Data Ingestion:** The Python backend (`main.py`) reads a JSON array containing timestamps, ASR text (e.g., from Whisper), and OCR text (e.g., from Tesseract).
2.  **Smart Normalization:** The comparison engine (`compare.py`) normalizes Indic scripts to NFC form to prevent byte-layout mismatches. It intentionally strips common punctuation and Devanagari Dandas (`।`, `॥`) to reduce false positives.
3.  **Algorithmic Scoring:** * Uses an **O(1) short-circuit** to instantly approve identical strings, saving CPU cycles.
    * Falls back to `rapidfuzz` (token sort ratio) to score strings regardless of word-order artifacts caused by OCR layout issues.
4.  **Dashboard Generation:** The results are piped through a Jinja2 templating engine (`report.py`) to generate a standalone HTML file powered by Vanilla JavaScript and CSS variables (no external dependencies required).

## How to Run and Test the Application

### 1. Installation
Ensure you have Python 3.10+ installed, then install the required dependencies:
```bash
pip install -r subtitle_mismatch_tool/requirements.txt
```
### 2. Generate the QA Report
Run Module 3 on the provided sample input (which includes Hindi, Kannada, missing data, and CPS speed warnings):
```bash
python3 subtitle_mismatch_tool/main.py subtitle_mismatch_tool/sample_output/module3_sample_segments_input.json --video-name demo_clip.mp4 --threshold 0.75 --output mismatch_report.html
```
### 3. Test the Interactive UI
1. Open the generated `mismatch_report.html` in your web browser.
2. Click **Load Local Video for QA** and select a test video from your computer.
3. Click on any row labeled `REVIEW`. The video will instantly jump to that timestamp and play the clip.
4. Test the Search bar by typing Kannada or Hindi text, and click **Export CSV** to verify the data export feature.

## Automated Testing & Security

This repository maintains strict CI/CD standards. You can run the entire test and security suite locally:

```bash
pip install pytest bandit pip-audit
pytest -q
bandit -q -r subtitle_mismatch_tool -x subtitle_mismatch_tool/sample_output
pip-audit -r subtitle_mismatch_tool/requirements.txt
```
## Input Data Format

The input file must be a JSON list where each item has:

1. `start` (float, seconds)
2. `end` (float, seconds)
3. `text` (audio transcript string)
4. `subtitle_text` (OCR subtitle string)

## Known Limitations & Next Steps

1. **Purely Lexical:** Similarity scoring is currently lexical and may still flag semantically equivalent paraphrases (e.g., changing tense). Future improvements could integrate a lightweight multilingual model (like `sentence-transformers`) for semantic validation.
2. **Modular Isolation:** The demo assumes upstream transcription (Module 1) and OCR text (Module 2) are already extracted and available in the JSON format.
3. **OCR Sensitivity:** Module 2 OCR accuracy is sensitive to subtitle font colour and video resolution. Pre-processing (grayscale + Otsu threshold + 2x upscale) is applied automatically. For very low-contrast subtitles, manual preprocessing may be needed.
