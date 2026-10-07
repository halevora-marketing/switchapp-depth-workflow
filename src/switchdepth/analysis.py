from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .media import MediaError, probe


MISSING = "NOT SUPPLIED — add an operator observation; do not infer from pixels"


def analyze_local(
    source: Path,
    output_dir: Path,
    *,
    samples: int = 9,
    scene_threshold: float = 0.35,
) -> dict[str, Any]:
    """Create a deterministic evidence pack without semantic AI inference."""
    try:
        import cv2
        import numpy as np
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError(
            'Local analysis requires: pip install -e ".[analysis]"'
        ) from exc

    if samples < 2:
        raise ValueError("samples must be at least 2")
    if not 0 < scene_threshold <= 1:
        raise ValueError("scene_threshold must be in (0, 1]")

    source = source.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "analysis-frames"
    frames_dir.mkdir(exist_ok=True)

    media = probe(source)
    if not media.get("video"):
        raise MediaError("Source has no video stream")
    duration = float(media.get("duration_seconds") or 0)
    if duration <= 0:
        raise MediaError("Source duration could not be measured")

    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise MediaError(f"OpenCV could not open: {source}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    last_decodable_time = max(0.0, duration - (1.0 / fps if fps > 0 else 0.001))
    sample_times = [last_decodable_time * index / (samples - 1) for index in range(samples)]
    saved_frames: list[dict[str, Any]] = []
    thumbs: list[Any] = []
    for index, timestamp in enumerate(sample_times):
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        filename = f"frame-{index + 1:02d}-{timestamp:.2f}s.jpg"
        path = frames_dir / filename
        cv2.imwrite(str(path), frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        thumbs.append(Image.fromarray(rgb))
        saved_frames.append({"timestamp_seconds": round(timestamp, 3), "file": str(path.relative_to(output_dir))})

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    previous = None
    motion: list[dict[str, Any]] = []
    cuts: list[dict[str, Any]] = []
    stride = max(1, int(round(fps / 4))) if fps > 0 else 1
    index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if index % stride == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA)
            if previous is not None:
                score = float(np.mean(cv2.absdiff(gray, previous)) / 255.0)
                timestamp = index / fps if fps > 0 else 0.0
                motion.append({"timestamp_seconds": round(timestamp, 3), "frame_difference": round(score, 6)})
                if score >= scene_threshold:
                    cuts.append({"timestamp_seconds": round(timestamp, 3), "frame_difference": round(score, 6)})
            previous = gray
        index += 1
    cap.release()

    contact_sheet = output_dir / "contact-sheet.jpg"
    if thumbs:
        tile_width = 320
        tile_height = max(1, round(tile_width * height / width)) if width and height else 180
        rows = math.ceil(len(thumbs) / 3)
        canvas = Image.new("RGB", (tile_width * 3, (tile_height + 28) * rows), "white")
        draw = ImageDraw.Draw(canvas)
        for index, (thumb, item) in enumerate(zip(thumbs, saved_frames)):
            thumb.thumbnail((tile_width, tile_height))
            x = (index % 3) * tile_width
            y = (index // 3) * (tile_height + 28)
            canvas.paste(thumb, (x, y))
            draw.text((x + 6, y + tile_height + 5), f"{item['timestamp_seconds']:.2f}s", fill="black")
        canvas.save(contact_sheet, quality=92)

    values = [item["frame_difference"] for item in motion]
    evidence = {
        "schema_version": 1,
        "analysis_method": "local deterministic sampling; no semantic AI inference",
        "source": str(source),
        "media": {
            "duration_seconds": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count,
            "has_audio": bool(media.get("audio")),
        },
        "samples": saved_frames,
        "contact_sheet": contact_sheet.name if contact_sheet.is_file() else None,
        "scene_cut_candidates": cuts,
        "motion_measurements": motion,
        "motion_summary": {
            "sample_count": len(values),
            "mean_frame_difference": round(float(np.mean(values)), 6) if values else None,
            "max_frame_difference": round(float(np.max(values)), 6) if values else None,
        },
        "operator_observations": {
            "visual_summary": MISSING,
            "subjects_and_relationships": MISSING,
            "wardrobe_and_props": MISSING,
            "timeline_actions": MISSING,
            "camera_and_environment": MISSING,
            "dialogue_audio_and_text": MISSING,
        },
    }
    (output_dir / "analysis.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    (output_dir / "Full analysis.md").write_text(_render_report(evidence), encoding="utf-8")
    return evidence


def _render_report(evidence: dict[str, Any]) -> str:
    media = evidence["media"]
    cuts = evidence["scene_cut_candidates"]
    cut_text = ", ".join(f"{item['timestamp_seconds']:.2f}s" for item in cuts) or "None above threshold"
    return f"""# Full analysis

## Provenance

- Method: {evidence['analysis_method']}
- Source: `{evidence['source']}`
- Semantic claims: deliberately not generated

## Measured media facts

- Runtime: {media['duration_seconds']:.3f}s
- Canvas: {media['width']} × {media['height']}
- Frame rate: {media['fps']:.3f} fps
- Frames: {media['frame_count']}
- Audio stream present: {'yes' if media['has_audio'] else 'no'}
- Candidate hard cuts: {cut_text}
- Contact sheet: `{evidence.get('contact_sheet') or 'not created'}`

## Operator observations required

These fields must come from a human-reviewed source or approved written brief. The tool does not identify people, clothing, actions, dialogue, setting, intent, or relationships from pixels.

- Visual summary: {MISSING}
- Subjects and relationships: {MISSING}
- Wardrobe and props: {MISSING}
- Timeline actions: {MISSING}
- Camera and lighting: {MISSING}
- Dialogue, audio, and text: {MISSING}

## Evidence files

- `analysis.json` contains all measurements.
- `analysis-frames/` contains timestamped review frames.
- `contact-sheet.jpg` provides a visual review surface.
"""
