from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .local_depth import create_local_depth
from .media import MediaError, extract_audio, mux_audio, probe, split_video
from .packages import create_item, validate_package
from .prompts import load_prompt, render_prompt, validate_prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="switchdepth")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="Inspect media with FFprobe")
    inspect.add_argument("path", type=Path)

    init = sub.add_parser("init", help="Create an item folder and manifest")
    init.add_argument("root", type=Path)
    init.add_argument("--title", required=True)
    init.add_argument("--source-url", default="")

    audio = sub.add_parser("extract-audio", help="Extract AAC audio")
    audio.add_argument("source", type=Path)
    audio.add_argument("output", type=Path)

    mux = sub.add_parser("mux-audio", help="Put source audio on a depth map")
    mux.add_argument("depth_video", type=Path)
    mux.add_argument("source_audio", type=Path)
    mux.add_argument("output", type=Path)

    split = sub.add_parser("split", help="Split a full source into exact sections")
    split.add_argument("source", type=Path)
    split.add_argument("output_dir", type=Path)
    split.add_argument("--seconds", type=float, default=30.0)

    depth = sub.add_parser("depth-local", help="Create a silent local ONNX depth map")
    depth.add_argument("source", type=Path)
    depth.add_argument("output", type=Path)
    depth.add_argument("--model", type=Path, required=True)

    validate = sub.add_parser("validate-prompt", help="Validate a structured prompt")
    validate.add_argument("path", type=Path)

    render = sub.add_parser("render-prompt", help="Validate and render a prompt")
    render.add_argument("source", type=Path)
    render.add_argument("output", type=Path)

    package = sub.add_parser("validate-package", help="Validate a package manifest and files")
    package.add_argument("manifest", type=Path)
    package.add_argument("--skip-media-probe", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            print(json.dumps(probe(args.path), indent=2))
        elif args.command == "init":
            print(create_item(args.root, title=args.title, source_url=args.source_url))
        elif args.command == "extract-audio":
            extract_audio(args.source, args.output)
            print(args.output.resolve())
        elif args.command == "mux-audio":
            mux_audio(args.depth_video, args.source_audio, args.output)
            print(args.output.resolve())
        elif args.command == "split":
            for output in split_video(args.source, args.output_dir, seconds=args.seconds):
                print(output.resolve())
        elif args.command == "depth-local":
            frames = create_local_depth(args.source, args.output, args.model)
            print(f"completed {frames} frames -> {args.output.resolve()}")
        elif args.command == "validate-prompt":
            return _print_issues(validate_prompt(load_prompt(args.path)))
        elif args.command == "render-prompt":
            rendered = render_prompt(load_prompt(args.source))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(args.output.resolve())
        elif args.command == "validate-package":
            return _print_issues(validate_package(
                args.manifest, probe_media=not args.skip_media_probe
            ))
    except (ValueError, FileNotFoundError, MediaError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _print_issues(issues: list[object]) -> int:
    if not issues:
        print("valid")
        return 0
    for issue in issues:
        print(f"{getattr(issue, 'code')}: {getattr(issue, 'message')}")
    return 1

