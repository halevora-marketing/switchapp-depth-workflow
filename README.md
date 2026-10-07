# SwitchApp Depth Workflow

A media-safe toolkit and runbook for turning reference videos into verified analyses, depth maps, and generation-ready prompts.

This repository consolidates the working rules learned across repeated production runs:

1. verify the exact source clip before processing;
2. analyze before generating a depth map;
3. keep every artifact tied to one stable item key;
4. treat missing report prompts as a failed analysis, not a partial success;
5. split clips longer than 30 seconds without dropping any footage;
6. preserve the original audio on delivery depth maps;
7. lock reference roles, identity, wardrobe, timing, camera, and sound in the final prompt;
8. stop at paid generation gates unless the spend is explicitly authorized; and
9. verify every file, Drive link, and Sheet write before marking an item complete.

No personal media, signed URLs, credentials, browser sessions, API keys, or production spreadsheets are included. The core CLI runs locally and does not upload anything or spend generation credits.

## What the project provides

- FFprobe-based media inspection
- exact 30-second splitting for long clips
- original-audio extraction and depth-map remuxing
- optional local Depth Anything V2 ONNX generation
- structured prompt rendering for Seedance, Kling, Gemini, WAN, and similar models
- validation of reference roles and complete, gap-free stage timing
- package manifests and completeness checks
- examples, tests, CI, and production runbooks

SwitchApp analysis and hosted depth generation remain external service steps. This repo validates and organizes their inputs and outputs; it does not reverse engineer or embed private service APIs.

## Requirements

- Python 3.10+
- FFmpeg and FFprobe on `PATH`
- Optional local depth generation: a compatible Depth Anything V2 Small ONNX model

## Install

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -e .
```

For local ONNX depth generation:

```bash
python -m pip install -e ".[local-depth]"
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## Quick start

Inspect a source:

```bash
switchdepth inspect source.mp4
```

Create a new item folder and manifest:

```bash
switchdepth init work \
  --title "Sunny Plaza Walk" \
  --source-url "https://example.com/source"
```

Extract the source audio:

```bash
switchdepth extract-audio "Original video.mp4" "Original audio.m4a"
```

Split a long source into complete, exact sections:

```bash
switchdepth split "Original video.mp4" "parts" --seconds 30
```

Generate a local silent depth map:

```bash
switchdepth depth-local \
  "Original video.mp4" \
  "Depth map silent.mp4" \
  --model models/depth-anything-v2-small.onnx
```

Put the original audio back on the depth map:

```bash
switchdepth mux-audio \
  "Depth map silent.mp4" \
  "Original audio.m4a" \
  "Depth map.mp4"
```

Validate and render a structured prompt:

```bash
switchdepth validate-prompt examples/sample_prompt.json
switchdepth render-prompt examples/sample_prompt.json out/Finished\ prompt.txt
```

Validate a completed item package after copying `examples/sample_manifest.json`
into a real item folder and filling in its artifacts:

```bash
switchdepth validate-package work/Sunny\ Plaza\ Walk/manifest.json
```

Use `--skip-media-probe` only for manifest/file-layout checks in tests; production
validation should always let FFprobe inspect the media streams.

## Default package layout

```text
Descriptive Clip Title/
├── manifest.json
├── Original video.mp4
├── Original audio.m4a
├── Full analysis.md
├── Seedance prompt.txt
├── Kling prompt.txt
├── Gemini prompt.txt
├── Finished prompt.txt
└── Depth map.mp4
```

For a source longer than 30 seconds, use `Depth map part 01.mp4`, `Depth map part 02.mp4`, and so on. The full source must be covered; never substitute an excerpt.

## Documentation

- [End-to-end workflow](docs/WORKFLOW.md)
- [Prompt analysis and finalization](docs/PROMPT_ANALYSIS.md)
- [Lessons from production runs](docs/LESSONS_FROM_RUNS.md)
- [SwitchApp integration boundary](docs/SWITCHAPP_INTEGRATION.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## Tests

```bash
python -m unittest discover -s tests -v
```

## Safety

Use only media and likenesses you are authorized to process. Keep production media under ignored directories such as `work/`, `media/`, or `out/`. Never commit tokens, cookies, signed CDN URLs, account identifiers, private Sheet/Drive links, or identity-reference media.
