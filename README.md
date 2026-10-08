# WAN Depth Workflow

An independent, local toolkit for video evidence analysis, depth-map creation, and reference-guided WAN prompts.

The workflow has no SwitchApp account, browser, API, or hosted-analysis dependency. It uses FFmpeg/FFprobe for media operations, OpenCV for deterministic evidence extraction, and an optional Depth Anything V2 ONNX model for local depth generation.

## Evidence, not guesses

`analyze-local` measures facts that software can verify: runtime, canvas, frame rate, audio-stream presence, sampled frames, frame-difference motion, and candidate hard cuts. It does **not** invent identities, relationships, clothing, actions, dialogue, locations, intent, or narrative meaning.

Those semantic details must come from an operator who reviewed the exported frames/source, or from an approved written brief. Unresolved markers such as `NOT SUPPLIED`, `UNKNOWN`, `TODO`, and `TBD` make prompt validation fail.

## Features

- local, provider-independent evidence packs (`analysis.json`, contact sheet, timestamped frames, Markdown report)
- optional local Depth Anything V2 ONNX depth maps
- exact video splitting, audio extraction, and audio remuxing
- WAN-style prompts with explicit material bindings and forbidden transfers
- one primary identity anchor, strict identity/hair continuity, and gap-free timestamp stages
- WAN-only package manifests and validation
- tests and GitHub Actions CI

## Requirements and installation

- Python 3.10+
- FFmpeg and FFprobe on `PATH`
- for local depth generation, a compatible Depth Anything V2 Small ONNX model

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -e ".[analysis]"
```

Install every optional local component:

```bash
python -m pip install -e ".[all]"
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## Quick start

Create an independent evidence pack:

```bash
wandepth analyze-local "Original video.mp4" "analysis"
```

Review `analysis/contact-sheet.jpg`, the timestamped frames, and the source. Replace the `NOT SUPPLIED` observation fields with facts you can verify. If the evidence is insufficient, ask for examples or a written brief; do not fill gaps by inference.

Create a local silent depth map and put the original audio back on it:

```bash
wandepth depth-local "Original video.mp4" "Depth map silent.mp4" --model models/depth-anything-v2-small.onnx
wandepth extract-audio "Original video.mp4" "Original audio.m4a"
wandepth mux-audio "Depth map silent.mp4" "Original audio.m4a" "Depth map.mp4"
```

Validate and render the WAN prompt:

```bash
wandepth validate-prompt examples/sample_prompt.json
wandepth render-prompt examples/sample_prompt.json "WAN prompt.txt"
```

The legacy `switchdepth` command remains as an alias for existing automation.

## WAN prompt contract

Rendered prompts use the production-tested sequence:

1. `Core task:`
2. `Material bindings:` with allowed and forbidden transfers for every reference
3. `Identity and appearance lock:`
4. `Mandatory wardrobe and props:`
5. `Subjects and relationships:`
6. `Shot timeline:` with exact, gap-free timestamps
7. `Environment, camera, and lighting:`
8. `Dialogue, audio, and text:`
9. `Maintain consistency:`

The depth/motion reference may control geometry, choreography, subject spacing, parallax, framing, and timing. It must not control identity, face, hair, skin, body shape, wardrobe, color, texture, lighting, props, people, or background appearance.

## Default package layout

```text
Descriptive Clip Title/
├── manifest.json
├── Original video.mp4
├── Original audio.m4a
├── analysis.json
├── Full analysis.md
├── contact-sheet.jpg
├── analysis-frames/
├── WAN prompt.txt
└── Depth map.mp4
```

## Documentation

- [Independent architecture](docs/INDEPENDENCE.md)
- [End-to-end workflow](docs/WORKFLOW.md)
- [WAN prompt analysis](docs/PROMPT_ANALYSIS.md)
- [Migration from SwitchApp](docs/SWITCHAPP_INTEGRATION.md)
- [Production lessons](docs/LESSONS_FROM_RUNS.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## Tests

```bash
python -m unittest discover -s tests -v
```

## Safety

Use only media and likenesses you are authorized to process. Keep production media under ignored directories such as `work/`, `media/`, or `out/`. Never commit tokens, cookies, signed URLs, private trackers, or identity-reference media.
