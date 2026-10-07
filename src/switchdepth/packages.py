from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .media import MediaError, probe
from .titles import safe_title, slug


@dataclass(frozen=True)
class PackageIssue:
    code: str
    message: str


def create_item(root: Path, *, title: str, source_url: str = "") -> Path:
    canonical = safe_title(title)
    item_dir = root.resolve() / canonical
    item_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "version": 1,
        "item_key": slug(canonical),
        "title": canonical,
        "source_url": source_url,
        "expected_duration_seconds": None,
        "analysis": {"status": "pending", "file": "Full analysis.md", "evidence": "analysis.json"},
        "prompts": {"wan": "WAN prompt.txt"},
        "media": {
            "original": "Original video.mp4",
            "audio": "Original audio.m4a",
            "depth_maps": ["Depth map.mp4"],
        },
        "status": "pending",
    }
    (item_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return item_dir


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Manifest must contain a JSON object")
    return data


def validate_package(manifest_path: Path, *, probe_media: bool = True) -> list[PackageIssue]:
    manifest_path = manifest_path.resolve()
    root = manifest_path.parent
    data = load_manifest(manifest_path)
    issues: list[PackageIssue] = []

    if data.get("version") != 1:
        issues.append(PackageIssue("manifest.version", "version must be 1"))
    if not str(data.get("item_key") or "").strip():
        issues.append(PackageIssue("manifest.item-key", "item_key is required"))
    if not str(data.get("title") or "").strip():
        issues.append(PackageIssue("manifest.title", "title is required"))

    analysis = data.get("analysis") if isinstance(data.get("analysis"), dict) else {}
    _require_file(root, analysis.get("file"), "analysis.file", issues)
    _require_file(root, analysis.get("evidence"), "analysis.evidence", issues)
    if analysis.get("status") != "complete":
        issues.append(PackageIssue("analysis.status", "analysis status must be complete"))

    prompts = data.get("prompts") if isinstance(data.get("prompts"), dict) else {}
    for model in ("wan",):
        _require_file(root, prompts.get(model), f"prompts.{model}", issues)

    media = data.get("media") if isinstance(data.get("media"), dict) else {}
    media_files: list[tuple[str, Path]] = []
    for field in ("original", "audio"):
        path = _require_file(root, media.get(field), f"media.{field}", issues)
        if path:
            media_files.append((field, path))
    depth_maps = media.get("depth_maps")
    if not isinstance(depth_maps, list) or not depth_maps:
        issues.append(PackageIssue("media.depth-maps", "at least one depth map is required"))
    else:
        for index, value in enumerate(depth_maps):
            path = _require_file(root, value, f"media.depth_maps[{index}]", issues)
            if path:
                media_files.append((f"depth_maps[{index}]", path))

    if probe_media:
        for label, path in media_files:
            try:
                info = probe(path)
            except MediaError as exc:
                issues.append(PackageIssue("media.probe", f"{label}: {exc}"))
                continue
            if not info["video"] and label != "audio":
                issues.append(PackageIssue("media.video", f"{label} has no video stream"))
            if label.startswith("depth_maps"):
                if not info["audio"]:
                    issues.append(PackageIssue("media.depth-audio", f"{label} has no audio stream"))
                if info["duration_seconds"] > 30.05:
                    issues.append(PackageIssue("media.depth-duration", f"{label} exceeds 30 seconds"))
    if data.get("status") != "complete":
        issues.append(PackageIssue("manifest.status", "package status must be complete"))
    return issues


def _require_file(
    root: Path,
    value: Any,
    label: str,
    issues: list[PackageIssue],
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        issues.append(PackageIssue("file.missing-field", f"{label} is required"))
        return None
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        issues.append(PackageIssue("file.outside-root", f"{label} points outside the package"))
        return None
    if not path.is_file():
        issues.append(PackageIssue("file.not-found", f"{label} not found: {value}"))
        return None
    return path
