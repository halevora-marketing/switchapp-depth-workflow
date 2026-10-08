import json
import tempfile
import unittest
from pathlib import Path

from switchdepth.pika import PikaApiError, PikaClient, WanRequest, estimate_cost_micro_usd


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, dict(headers), body))
        return self.responses.pop(0)


def response(data, status=200, headers=None):
    return status, headers or {}, json.dumps(data).encode("utf-8")


class WanRequestTests(unittest.TestCase):
    def test_cost_and_payload(self):
        request = WanRequest(
            prompt="Keep identity stable.",
            resolution="1080p",
            ratio="9:16",
            duration=10,
            reference_image_urls=["https://example.com/identity.png"],
            reference_video_urls=["https://example.com/depth.mp4"],
            reference_audio_urls=["https://example.com/audio.m4a"],
        )
        self.assertEqual(estimate_cost_micro_usd(request), 1_300_000)
        self.assertEqual(request.to_payload()["ratio"], "9:16")

    def test_auto_duration_cannot_be_prepriced(self):
        self.assertIsNone(estimate_cost_micro_usd(WanRequest(duration="auto")))

    def test_invalid_duration_and_reference_limit_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "between 2 and 30"):
            WanRequest(duration=31).validate()
        with self.assertRaisesRegex(ValueError, "at most 5"):
            WanRequest(reference_video_urls=[f"https://example.com/{i}.mp4" for i in range(6)]).validate()


class PikaClientTests(unittest.TestCase):
    def test_balance_guard_rejects_shortfall_before_submit(self):
        transport = FakeTransport([response({"balance_micro_usd": 100_000})])
        client = PikaClient("test-key", transport=transport)
        with self.assertRaises(PikaApiError) as raised:
            client.ensure_affordable(WanRequest(duration=10, resolution="1080p"))
        self.assertEqual(raised.exception.code, "insufficient_balance")
        self.assertEqual(len(transport.calls), 1)

    def test_upload_uses_exact_signed_headers_and_bytes(self):
        ticket = {
            "upload_url": "https://upload.example/signed",
            "url": "https://cdn.example/reference.bin",
            "headers": {"content-type": "application/octet-stream", "x-signed": "yes"},
        }
        transport = FakeTransport([response(ticket), (200, {}, b"")])
        client = PikaClient("test-key", transport=transport)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "reference.bin"
            path.write_bytes(b"abc123")
            url = client.upload_file(path)
        self.assertEqual(url, ticket["url"])
        put = transport.calls[1]
        self.assertEqual(put[0], "PUT")
        self.assertEqual(put[2]["content-type"], "application/octet-stream")
        self.assertEqual(put[2]["Content-Length"], "6")
        self.assertNotIn("X-API-Key", put[2])
        self.assertEqual(put[3], b"abc123")

    def test_submit_and_poll_complete_job(self):
        transport = FakeTransport([
            response({"id": "media_1", "status": "queued"}),
            response({"id": "media_1", "status": "running"}),
            response({
                "id": "media_1",
                "status": "completed",
                "output": {"media_type": "video", "video": {"url": "https://example.com/out.mp4"}},
                "billing": {"state": "settled", "charge_micro_usd": 650_000},
            }),
        ])
        client = PikaClient("test-key", transport=transport)
        submitted = client.submit_wan(WanRequest(duration=10, resolution="720p"), idempotency_key="same-body-key")
        job = client.wait_for_job(submitted["id"], poll_interval_seconds=0.001, timeout_seconds=1)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(transport.calls[0][2]["Idempotency-Key"], "same-body-key")

    def test_http_error_preserves_machine_code_and_retry_after(self):
        transport = FakeTransport([
            response(
                {"id": "media_2", "status": "failed", "error": {"code": "rate_limited", "message": "queue full"}},
                status=429,
                headers={"Retry-After": "12"},
            )
        ])
        client = PikaClient("test-key", transport=transport)
        with self.assertRaises(PikaApiError) as raised:
            client.submit_wan(WanRequest())
        self.assertEqual(raised.exception.status, 429)
        self.assertEqual(raised.exception.code, "rate_limited")
        self.assertEqual(raised.exception.retry_after, "12")
        self.assertEqual(raised.exception.job["id"], "media_2")


if __name__ == "__main__":
    unittest.main()
