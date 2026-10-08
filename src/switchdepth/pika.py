from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse


BASE_URL = "https://api.dev.pika.art"
WAN_PATH = "/v1/media/alibaba/wan3.0-video/omni-video"
RESOLUTIONS = {"480p", "720p", "1080p"}
RATIOS = {"adaptive", "16:9", "4:3", "1:1", "3:4", "9:16"}
PRICE_MICRO_USD_PER_SECOND = {"480p": 32_500, "720p": 65_000, "1080p": 130_000}
TERMINAL_STATUSES = {"completed", "failed"}

Transport = Callable[[str, str, Mapping[str, str], bytes | None], tuple[int, Mapping[str, str], bytes]]


class PikaApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        retry_after: str | None = None,
        job: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.retry_after = retry_after
        self.job = job


@dataclass(frozen=True)
class WanRequest:
    prompt: str = ""
    resolution: str = "1080p"
    ratio: str = "adaptive"
    duration: int | str = 5
    audio: bool = True
    seed: int | None = None
    watermark: bool = False
    reference_image_urls: list[str] = field(default_factory=list)
    reference_video_urls: list[str] = field(default_factory=list)
    reference_audio_urls: list[str] = field(default_factory=list)
    file_url: str | None = None
    web_url: str | None = None

    def validate(self) -> None:
        if len(self.prompt) > 20_000:
            raise ValueError("prompt must not exceed 20,000 characters")
        if self.resolution not in RESOLUTIONS:
            raise ValueError(f"resolution must be one of: {', '.join(sorted(RESOLUTIONS))}")
        if self.ratio not in RATIOS:
            raise ValueError(f"ratio must be one of: {', '.join(sorted(RATIOS))}")
        if self.duration != "auto":
            if isinstance(self.duration, bool) or not isinstance(self.duration, int):
                raise ValueError("duration must be an integer from 2 to 30, or 'auto'")
            if not 2 <= self.duration <= 30:
                raise ValueError("duration must be between 2 and 30 seconds")
        if not isinstance(self.audio, bool) or not isinstance(self.watermark, bool):
            raise ValueError("audio and watermark must be booleans")
        if self.seed is not None:
            if isinstance(self.seed, bool) or not 0 <= self.seed <= 2_147_483_647:
                raise ValueError("seed must be an integer from 0 to 2147483647")
        self._validate_urls("reference_image_urls", self.reference_image_urls, 10)
        self._validate_urls("reference_video_urls", self.reference_video_urls, 5)
        self._validate_urls("reference_audio_urls", self.reference_audio_urls, 5)
        if self.file_url:
            _require_https_url("file_url", self.file_url)
        if self.web_url:
            _require_https_url("web_url", self.web_url)

    def to_payload(self) -> dict[str, Any]:
        self.validate()
        payload: dict[str, Any] = {
            "resolution": self.resolution,
            "ratio": self.ratio,
            "duration": self.duration,
            "audio": self.audio,
            "watermark": self.watermark,
        }
        optional = {
            "prompt": self.prompt or None,
            "seed": self.seed,
            "reference_image_urls": self.reference_image_urls or None,
            "reference_video_urls": self.reference_video_urls or None,
            "reference_audio_urls": self.reference_audio_urls or None,
            "file_url": self.file_url,
            "web_url": self.web_url,
        }
        payload.update({key: value for key, value in optional.items() if value is not None})
        return payload

    @staticmethod
    def _validate_urls(name: str, values: list[str], limit: int) -> None:
        if len(values) > limit:
            raise ValueError(f"{name} accepts at most {limit} items")
        for index, value in enumerate(values):
            _require_public_url(f"{name}[{index}]", value)


class PikaClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout_seconds: float = 60.0,
        transport: Transport | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Pika API key is required")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport or self._urllib_transport

    @classmethod
    def from_env(cls) -> "PikaClient":
        key = os.environ.get("PIKA_API_KEY", "")
        if not key:
            raise ValueError("Set PIKA_API_KEY in the environment; do not put API keys in project files")
        return cls(key)

    def get_balance(self) -> dict[str, Any]:
        return self._json("GET", "/billing/balance")

    def ensure_affordable(self, request: WanRequest) -> dict[str, Any]:
        cost = estimate_cost_micro_usd(request)
        if cost is None:
            raise ValueError("duration='auto' cannot be pre-priced; use a numeric duration for the balance guard")
        balance = self.get_balance()
        available = _available_micro_usd(balance)
        if available is None:
            raise PikaApiError("Pika balance response did not expose prepaid or postpaid available funds")
        if available < cost:
            raise PikaApiError(
                f"Insufficient Pika balance: need ${cost / 1_000_000:.4f}, "
                f"available ${available / 1_000_000:.4f}",
                code="insufficient_balance",
            )
        return {"estimated_cost_micro_usd": cost, "available_micro_usd": available, "balance": balance}

    def upload_file(self, path: Path, *, content_type: str | None = None) -> str:
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        mime = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        size = path.stat().st_size
        ticket = self._json(
            "POST",
            "/v1/media/uploads",
            {"content_type": mime, "size_bytes": size},
        )
        upload_url = str(ticket.get("upload_url") or "")
        permanent_url = str(ticket.get("url") or "")
        headers = ticket.get("headers") or {}
        if not upload_url or not permanent_url or not isinstance(headers, dict):
            raise PikaApiError("Pika upload response omitted upload_url, url, or headers")
        signed_headers = {str(key): str(value) for key, value in headers.items()}
        _setdefault_header(signed_headers, "Content-Type", mime)
        _setdefault_header(signed_headers, "Content-Length", str(size))
        body = path.read_bytes()
        status, _, response = self.transport("PUT", upload_url, signed_headers, body)
        if not 200 <= status < 300:
            raise PikaApiError(
                f"Pika storage upload failed with HTTP {status}: {response.decode('utf-8', 'replace')}",
                status=status,
            )
        return permanent_url

    def submit_wan(self, request: WanRequest, *, idempotency_key: str | None = None) -> dict[str, Any]:
        key = idempotency_key or str(uuid.uuid4())
        return self._json("POST", WAN_PATH, request.to_payload(), extra_headers={"Idempotency-Key": key})

    def get_job(self, request_id: str) -> dict[str, Any]:
        return self._json("GET", f"/v1/media/jobs/{request_id}")

    def get_content_url(self, request_id: str) -> str:
        result = self._json("GET", f"/v1/media/jobs/{request_id}/content")
        url = str(result.get("url") or "")
        if not url:
            raise PikaApiError("Completed job did not return a content URL")
        return url

    def wait_for_job(
        self,
        request_id: str,
        *,
        poll_interval_seconds: float = 3.0,
        timeout_seconds: float = 1_800.0,
    ) -> dict[str, Any]:
        if poll_interval_seconds <= 0 or timeout_seconds <= 0:
            raise ValueError("poll interval and timeout must be positive")
        deadline = time.monotonic() + timeout_seconds
        while True:
            job = self.get_job(request_id)
            status = str(job.get("status") or "")
            if status in TERMINAL_STATUSES:
                return job
            if status not in {"queued", "running"}:
                raise PikaApiError(f"Pika returned an unknown job status: {status!r}", job=job)
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for Pika job {request_id}")
            time.sleep(min(poll_interval_seconds, max(0.0, deadline - time.monotonic())))

    def download(self, url: str, output: Path) -> Path:
        _require_public_url("download URL", url)
        headers: dict[str, str] = {}
        if url.startswith(self.base_url + "/"):
            headers["X-API-Key"] = self.api_key
        status, _, body = self.transport("GET", url, headers, None)
        if not 200 <= status < 300:
            raise PikaApiError(f"Video download failed with HTTP {status}", status=status)
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(body)
        return output

    def _json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        url = path if path.startswith("http") else self.base_url + path
        headers = {"X-API-Key": self.api_key, "Accept": "application/json"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        if extra_headers:
            headers.update(extra_headers)
        status, response_headers, raw = self.transport(method, url, headers, body)
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PikaApiError(f"Pika returned non-JSON data with HTTP {status}", status=status) from exc
        if not isinstance(data, dict):
            raise PikaApiError("Pika response must be a JSON object", status=status)
        if not 200 <= status < 300:
            error = data.get("error") if isinstance(data.get("error"), dict) else {}
            message = str(error.get("message") or data.get("message") or f"Pika request failed with HTTP {status}")
            raise PikaApiError(
                message,
                status=status,
                code=str(error.get("code") or "") or None,
                retry_after=_header(response_headers, "Retry-After"),
                job=data if data.get("id") else None,
            )
        return data

    def _urllib_transport(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
    ) -> tuple[int, Mapping[str, str], bytes]:
        request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return response.status, dict(response.headers.items()), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers.items()), exc.read()
        except urllib.error.URLError as exc:
            raise PikaApiError(f"Pika network request failed: {exc.reason}") from exc


def estimate_cost_micro_usd(request: WanRequest) -> int | None:
    request.validate()
    if request.duration == "auto":
        return None
    return PRICE_MICRO_USD_PER_SECOND[request.resolution] * request.duration


def _available_micro_usd(balance: dict[str, Any]) -> int | None:
    postpaid = balance.get("postpaid")
    if isinstance(postpaid, dict):
        cycle = postpaid.get("cycle")
        if isinstance(cycle, dict) and cycle.get("remaining_micro_usd") is not None:
            return int(cycle["remaining_micro_usd"])
    value = balance.get("balance_micro_usd")
    return int(value) if value is not None else None


def _require_public_url(name: str, value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be a public HTTP(S) URL")


def _require_https_url(name: str, value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{name} must be a public HTTPS URL")


def _header(headers: Mapping[str, str], name: str) -> str | None:
    return next((str(value) for key, value in headers.items() if key.lower() == name.lower()), None)


def _setdefault_header(headers: dict[str, str], name: str, value: str) -> None:
    if not any(key.lower() == name.lower() for key in headers):
        headers[name] = value
