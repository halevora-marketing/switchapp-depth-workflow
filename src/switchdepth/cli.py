from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .analysis import analyze_local
from .local_depth import create_local_depth
from .media import MediaError, extract_audio, mux_audio, probe, split_video
from .packages import create_item, validate_package
from .pika import PikaApiError, PikaClient, WanRequest, estimate_cost_micro_usd
from .prompts import load_prompt, render_prompt, validate_prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wandepth")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="Inspect media with FFprobe")
    inspect.add_argument("path", type=Path)

    analyze = sub.add_parser("analyze-local", help="Create a local, non-semantic evidence pack")
    analyze.add_argument("source", type=Path)
    analyze.add_argument("output_dir", type=Path)
    analyze.add_argument("--samples", type=int, default=9)
    analyze.add_argument("--scene-threshold", type=float, default=0.35)

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

    balance = sub.add_parser("pika-balance", help="Read the Pika organization balance")

    upload = sub.add_parser("pika-upload", help="Upload one local reference to Pika")
    upload.add_argument("path", type=Path)
    upload.add_argument("--content-type")

    status = sub.add_parser("pika-status", help="Read a Pika media job")
    status.add_argument("request_id")

    wan = sub.add_parser("pika-wan", help="Preview or submit a Wan 3.0 Omni Video job")
    prompt_group = wan.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", default="")
    prompt_group.add_argument("--prompt-file", type=Path)
    wan.add_argument("--image", action="append", type=Path, default=[], help="Local image reference; repeatable")
    wan.add_argument("--video", action="append", type=Path, default=[], help="Local video reference; repeatable")
    wan.add_argument("--audio-ref", action="append", type=Path, default=[], help="Local audio reference; repeatable")
    wan.add_argument("--image-url", action="append", default=[], help="Public image URL; repeatable")
    wan.add_argument("--video-url", action="append", default=[], help="Public video URL; repeatable")
    wan.add_argument("--audio-url", action="append", default=[], help="Public audio URL; repeatable")
    wan.add_argument("--file-url")
    wan.add_argument("--web-url")
    wan.add_argument("--resolution", choices=("480p", "720p", "1080p"), default="1080p")
    wan.add_argument("--ratio", choices=("adaptive", "16:9", "4:3", "1:1", "3:4", "9:16"), default="adaptive")
    wan.add_argument("--duration", type=_duration, default=5, help="2-30 seconds, or auto")
    wan.add_argument("--model-audio", action=argparse.BooleanOptionalAction, default=True)
    wan.add_argument("--seed", type=int)
    wan.add_argument("--watermark", action=argparse.BooleanOptionalAction, default=False)
    wan.add_argument("--idempotency-key", help="Reuse only when retrying the exact same submission")
    wan.add_argument("--skip-balance-check", action="store_true", help="Required for duration=auto; removes the local cost guard")
    wan.add_argument("--poll-interval", type=float, default=3.0)
    wan.add_argument("--timeout", type=float, default=1800.0)
    wan.add_argument("--output", type=Path, help="Download the completed MP4 here")
    wan.add_argument("--submit", action="store_true", help="Upload references and create the paid job")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            print(json.dumps(probe(args.path), indent=2))
        elif args.command == "analyze-local":
            result = analyze_local(args.source, args.output_dir, samples=args.samples, scene_threshold=args.scene_threshold)
            print(json.dumps({"analysis": str((args.output_dir / 'analysis.json').resolve()), "samples": len(result["samples"])}, indent=2))
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
        elif args.command == "pika-balance":
            print(json.dumps(PikaClient.from_env().get_balance(), indent=2))
        elif args.command == "pika-upload":
            url = PikaClient.from_env().upload_file(args.path, content_type=args.content_type)
            print(json.dumps({"url": url}, indent=2))
        elif args.command == "pika-status":
            print(json.dumps(PikaClient.from_env().get_job(args.request_id), indent=2))
        elif args.command == "pika-wan":
            return _run_pika_wan(args)
    except (ValueError, FileNotFoundError, MediaError, PikaApiError, RuntimeError, TimeoutError) as exc:
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


def _duration(value: str) -> int | str:
    if value == "auto":
        return value
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("duration must be 2-30 or auto") from exc


def _run_pika_wan(args: argparse.Namespace) -> int:
    prompt = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else args.prompt
    for path in [*args.image, *args.video, *args.audio_ref]:
        if not path.is_file():
            raise FileNotFoundError(path)
    if len(args.image) + len(args.image_url) > 10:
        raise ValueError("Wan 3.0 accepts at most 10 reference images")
    if len(args.video) + len(args.video_url) > 5:
        raise ValueError("Wan 3.0 accepts at most 5 reference videos")
    if len(args.audio_ref) + len(args.audio_url) > 5:
        raise ValueError("Wan 3.0 accepts at most 5 reference audio clips")

    preview = _wan_request(args, prompt, args.image_url, args.video_url, args.audio_url)
    cost = estimate_cost_micro_usd(preview)
    if not args.submit:
        print(json.dumps({
            "mode": "preview_only",
            "estimated_cost_micro_usd": cost,
            "estimated_cost_usd": cost / 1_000_000 if cost is not None else None,
            "local_files_to_upload": {
                "images": [str(path.resolve()) for path in args.image],
                "videos": [str(path.resolve()) for path in args.video],
                "audio": [str(path.resolve()) for path in args.audio_ref],
            },
            "request": preview.to_payload(),
        }, indent=2))
        return 0

    client = PikaClient.from_env()
    preflight = None if args.skip_balance_check else client.ensure_affordable(preview)
    image_urls = list(args.image_url) + [client.upload_file(path) for path in args.image]
    video_urls = list(args.video_url) + [client.upload_file(path) for path in args.video]
    audio_urls = list(args.audio_url) + [client.upload_file(path) for path in args.audio_ref]
    request = _wan_request(args, prompt, image_urls, video_urls, audio_urls)
    idempotency_key = args.idempotency_key or str(uuid.uuid4())
    print(json.dumps({"event": "submitting", "idempotency_key": idempotency_key, "preflight": preflight}), file=sys.stderr)
    submitted = client.submit_wan(request, idempotency_key=idempotency_key)
    request_id = str(submitted.get("id") or "")
    if not request_id:
        raise PikaApiError("Pika submit response did not include a job id")
    job = submitted if submitted.get("status") in {"completed", "failed"} else client.wait_for_job(
        request_id,
        poll_interval_seconds=args.poll_interval,
        timeout_seconds=args.timeout,
    )
    if job.get("status") == "completed" and args.output:
        output = job.get("output") if isinstance(job.get("output"), dict) else {}
        video = output.get("video") if isinstance(output.get("video"), dict) else {}
        url = str(video.get("url") or "") or client.get_content_url(request_id)
        job["downloaded_to"] = str(client.download(url, args.output))
    print(json.dumps(job, indent=2))
    return 0 if job.get("status") == "completed" else 1


def _wan_request(
    args: argparse.Namespace,
    prompt: str,
    image_urls: list[str],
    video_urls: list[str],
    audio_urls: list[str],
) -> WanRequest:
    return WanRequest(
        prompt=prompt,
        resolution=args.resolution,
        ratio=args.ratio,
        duration=args.duration,
        audio=args.model_audio,
        seed=args.seed,
        watermark=args.watermark,
        reference_image_urls=list(image_urls),
        reference_video_urls=list(video_urls),
        reference_audio_urls=list(audio_urls),
        file_url=args.file_url,
        web_url=args.web_url,
    )
