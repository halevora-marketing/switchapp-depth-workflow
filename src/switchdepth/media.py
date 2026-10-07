from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any


class MediaError(RuntimeError):
    pass


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, check=True, text=True, capture_output=True)
    except FileNotFoundError as exc:
        raise MediaError(f"Required executable not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown error").strip()
        raise MediaError(f"{args[0]} failed: {detail}") from exc


def probe(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise MediaError(f"Media file does not exist: {path}")
    result = _run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ])
    raw = json.loads(result.stdout)
    streams = raw.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration = float(raw.get("format", {}).get("duration") or 0.0)
    return {
        "path": str(path),
        "duration_seconds": duration,
        "size_bytes": int(raw.get("format", {}).get("size") or path.stat().st_size),
        "video": video,
        "audio": audio,
    }


def extract_audio(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source),
        "-vn", "-c:a", "aac", "-b:a", "192k", str(output),
    ])


def mux_audio(depth_video: Path, source_audio: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(depth_video), "-i", str(source_audio),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(output),
    ])


def split_video(source: Path, output_dir: Path, *, seconds: float = 30.0) -> list[Path]:
    if seconds <= 0:
        raise ValueError("Split duration must be positive")
    duration = probe(source)["duration_seconds"]
    if duration <= 0:
        raise MediaError("Source duration could not be measured")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    count = math.ceil(duration / seconds)
    for index in range(count):
        start = index * seconds
        length = min(seconds, duration - start)
        output = output_dir / f"source part {index + 1:02d}.mp4"
        _run([
            "ffmpeg", "-y", "-v", "error", "-ss", f"{start:.6f}",
            "-i", str(source), "-t", f"{length:.6f}", "-map", "0:v:0",
            "-map", "0:a?", "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-b:a", "192k", "-movflags", "+faststart", str(output),
        ])
        outputs.append(output)
    return outputs

