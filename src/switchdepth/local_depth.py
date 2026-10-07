from __future__ import annotations

import json
import subprocess
from pathlib import Path


def create_local_depth(source: Path, output: Path, model: Path) -> int:
    try:
        import numpy as np
        import onnxruntime as ort
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Local depth extras are missing; install with pip install -e .[local-depth]"
        ) from exc

    source = source.resolve()
    output = output.resolve()
    model = model.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if not model.is_file():
        raise FileNotFoundError(model)

    raw_probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
        "-of", "json", str(source),
    ], text=True)
    stream = json.loads(raw_probe)["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])
    numerator, denominator = stream["avg_frame_rate"].split("/")
    fps = float(numerator) / float(denominator)
    total = int(stream.get("nb_frames") or 0)
    model_width, model_height = _model_size(width, height)

    session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)

    output.parent.mkdir(parents=True, exist_ok=True)
    decoder = subprocess.Popen([
        "ffmpeg", "-v", "error", "-i", str(source),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ], stdout=subprocess.PIPE)
    encoder = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", f"{fps:.8f}", "-i", "-", "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ], stdin=subprocess.PIPE)
    if decoder.stdout is None or encoder.stdin is None:
        raise RuntimeError("Unable to open FFmpeg pipes")

    frame_bytes = width * height * 3
    previous = None
    index = 0
    try:
        while True:
            raw = decoder.stdout.read(frame_bytes)
            if len(raw) < frame_bytes:
                break
            frame = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3)
            small = np.asarray(
                Image.fromarray(frame).resize((model_width, model_height), Image.Resampling.BICUBIC),
                dtype=np.float32,
            )
            tensor = ((small / 255.0 - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
            depth = np.squeeze(session.run(None, {input_name: tensor})[0])
            low, high = np.percentile(depth, (2.0, 98.0))
            normalized = np.clip((depth - low) / max(high - low, 1e-6), 0.0, 1.0)
            full = np.asarray(
                Image.fromarray(normalized.astype(np.float32), mode="F").resize(
                    (width, height), Image.Resampling.BICUBIC
                ),
                dtype=np.float32,
            )
            if previous is not None:
                full = 0.78 * full + 0.22 * previous
            previous = full
            gray = (np.power(np.clip(full, 0.0, 1.0), 0.90) * 255.0 + 0.5).astype(np.uint8)
            encoder.stdin.write(np.repeat(gray[:, :, None], 3, axis=2).tobytes())
            index += 1
            if index == 1 or index % 15 == 0:
                suffix = f"/{total}" if total else ""
                print(f"processed {index}{suffix} frames", flush=True)
    finally:
        decoder.stdout.close()
        decoder.wait()
        encoder.stdin.close()
        encoder.wait()
    if decoder.returncode != 0 or encoder.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: decode={decoder.returncode}, encode={encoder.returncode}")
    return index


def _model_size(width: int, height: int, target: int = 518) -> tuple[int, int]:
    if height >= width:
        return max(14, round((width / height) * target / 14) * 14), target
    return target, max(14, round((height / width) * target / 14) * 14)

