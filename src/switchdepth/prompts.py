from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def load_prompt(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Prompt file must contain a JSON object")
    return data


def validate_prompt(data: dict[str, Any], *, tolerance: float = 0.02) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    runtime = _number(data.get("runtime_seconds"))
    if runtime is None or runtime <= 0:
        issues.append(ValidationIssue("runtime.invalid", "runtime_seconds must be positive"))

    assets = data.get("reference_assets")
    if not isinstance(assets, list) or not assets:
        issues.append(ValidationIssue("assets.missing", "reference_assets must be a non-empty list"))
        assets = []
    names: set[str] = set()
    identity_anchors = 0
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            issues.append(ValidationIssue("asset.invalid", f"reference_assets[{index}] must be an object"))
            continue
        name = str(asset.get("name") or "").strip()
        role = str(asset.get("role") or "").strip()
        allowed = str(asset.get("allowed") or "").strip()
        forbidden = str(asset.get("forbidden") or "").strip()
        if not name or name in names:
            issues.append(ValidationIssue("asset.name", f"reference_assets[{index}] needs a unique name"))
        names.add(name)
        if not role or not allowed or not forbidden:
            issues.append(ValidationIssue("asset.role", f"{name or index} needs role, allowed, and forbidden text"))
        if asset.get("primary_identity") is True:
            identity_anchors += 1
        if role.lower() == "depth geometry":
            leaked = _contains_any(allowed, [
                "identity", "face", "hair", "skin", "wardrobe", "clothing",
                "color", "texture", "lighting", "background appearance",
            ])
            if leaked:
                issues.append(ValidationIssue(
                    "asset.depth-role-leak",
                    f"{name} assigns appearance or identity control to a depth reference",
                ))
    if identity_anchors != 1:
        issues.append(ValidationIssue(
            "assets.identity-anchor",
            "exactly one reference asset must set primary_identity to true",
        ))

    lock = data.get("identity_lock")
    if not isinstance(lock, list) or not any(str(item).strip() for item in lock):
        issues.append(ValidationIssue("identity.missing", "identity_lock must contain explicit constraints"))

    stages = data.get("stages")
    if not isinstance(stages, list) or not stages:
        issues.append(ValidationIssue("stages.missing", "stages must cover the full runtime"))
    elif runtime and runtime > 0:
        cursor = 0.0
        for index, stage in enumerate(stages):
            if not isinstance(stage, dict):
                issues.append(ValidationIssue("stage.invalid", f"stages[{index}] must be an object"))
                continue
            start = _number(stage.get("start"))
            end = _number(stage.get("end"))
            action = str(stage.get("action") or "").strip()
            if start is None or end is None or end <= start:
                issues.append(ValidationIssue("stage.range", f"stages[{index}] has an invalid time range"))
                continue
            if abs(start - cursor) > tolerance:
                issues.append(ValidationIssue(
                    "stage.coverage",
                    f"stages[{index}] starts at {start:g}s; expected {cursor:g}s",
                ))
            if not action:
                issues.append(ValidationIssue("stage.action", f"stages[{index}] needs an action"))
            cursor = end
        if abs(cursor - runtime) > tolerance:
            issues.append(ValidationIssue(
                "stage.runtime",
                f"stages end at {cursor:g}s; runtime is {runtime:g}s",
            ))

    for field in ("goal", "camera_and_lighting", "sound_design"):
        if not str(data.get(field) or "").strip():
            issues.append(ValidationIssue(f"{field}.missing", f"{field} is required"))
    return issues


def render_prompt(data: dict[str, Any]) -> str:
    issues = validate_prompt(data)
    if issues:
        joined = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(f"Prompt validation failed: {joined}")

    lines = ["【Generation Goal】", str(data["goal"]).strip(), "", "【Reference Asset Roles】"]
    for asset in data["reference_assets"]:
        primary = " Primary identity anchor." if asset.get("primary_identity") else ""
        lines.append(
            f"{asset['name']} — {asset['role']}. Allowed: {asset['allowed']}. "
            f"Forbidden: {asset['forbidden']}.{primary}"
        )
    lines.extend(["", "【Identity and Appearance Lock】"])
    lines.extend(f"- {str(item).strip()}" for item in data["identity_lock"])

    wardrobe = str(data.get("wardrobe_and_props") or "").strip()
    if wardrobe:
        lines.extend(["", "【Mandatory Wardrobe and Props】", wardrobe])
    subjects = str(data.get("subjects_and_relationships") or "").strip()
    if subjects:
        lines.extend(["", "【Subjects and Relationships】", subjects])

    for index, stage in enumerate(data["stages"], start=1):
        lines.extend([
            "",
            f"【Stage {index} {_fmt(stage['start'])}–{_fmt(stage['end'])}】",
            str(stage["action"]).strip(),
        ])
    lines.extend([
        "", "【Camera and Lighting】", str(data["camera_and_lighting"]).strip(),
        "", "【Sound Design】", str(data["sound_design"]).strip(),
    ])
    return "\n".join(lines).rstrip() + "\n"


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _contains_any(text: str, words: list[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in words)


def _fmt(value: Any) -> str:
    return f"{float(value):g}s"

