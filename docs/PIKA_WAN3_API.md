# Pika Wan 3.0 API

This project includes a dependency-free Python client for Pika's stable Alibaba Wan 3.0 Omni Video endpoint:

```text
POST https://api.dev.pika.art/v1/media/alibaba/wan3.0-video/omni-video
```

The API key is read only from `PIKA_API_KEY`. Never place it in source, request JSON, frontend code, or a committed `.env` file.

```powershell
$env:PIKA_API_KEY = "your_key_here"
```

## Safe CLI workflow

Check authentication and the organization balance:

```bash
wandepth pika-balance
```

Preview a job locally:

```bash
wandepth pika-wan \
  --prompt-file "WAN prompt.txt" \
  --image "identity-front.png" \
  --image "identity-side.png" \
  --video "Depth map.mp4" \
  --audio-ref "Original audio.m4a" \
  --resolution 1080p \
  --ratio 9:16 \
  --duration 10
```

Preview mode validates all limits and prints the request plus its estimated cost. It does not need an API key, upload files, or create a paid job.

Submit and download only after reviewing the preview:

```bash
wandepth pika-wan \
  --prompt-file "WAN prompt.txt" \
  --image "identity-front.png" \
  --video "Depth map.mp4" \
  --audio-ref "Original audio.m4a" \
  --resolution 1080p \
  --ratio 9:16 \
  --duration 10 \
  --submit \
  --output "Wan result.mp4"
```

The submit path performs these steps in order:

1. validate prompt length, enums, duration, seed, URLs, and reference counts;
2. calculate the expected price and check the prepaid or postpaid balance;
3. obtain a presigned URL for every local reference;
4. upload the exact bytes with the signed headers and byte length;
5. submit with a newly generated `Idempotency-Key`;
6. poll until `completed` or `failed`; and
7. optionally download the MP4.

The generated idempotency key is printed before submission. If the connection drops before the submit response arrives, retry the exact same body with that same key. A known failed job must be retried with a fresh key.

## Direct Python use

```python
from pathlib import Path

from switchdepth.pika import PikaClient, WanRequest

client = PikaClient.from_env()
identity_url = client.upload_file(Path("identity.png"))
depth_url = client.upload_file(Path("Depth map.mp4"))
audio_url = client.upload_file(Path("Original audio.m4a"))

request = WanRequest(
    prompt=Path("WAN prompt.txt").read_text(encoding="utf-8"),
    resolution="1080p",
    ratio="9:16",
    duration=10,
    audio=True,
    reference_image_urls=[identity_url],
    reference_video_urls=[depth_url],
    reference_audio_urls=[audio_url],
)

client.ensure_affordable(request)
submitted = client.submit_wan(request, idempotency_key="persist-this-per-exact-body")
job = client.wait_for_job(submitted["id"])

if job["status"] == "completed":
    client.download(job["output"]["video"]["url"], Path("result.mp4"))
else:
    raise RuntimeError(job["error"])
```

## Limits encoded by the client

| Field | Accepted value |
| --- | --- |
| prompt | at most 20,000 characters |
| resolution | `480p`, `720p`, `1080p` |
| ratio | `adaptive`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` |
| duration | integer 2–30, or `auto` |
| seed | integer 0–2,147,483,647 |
| reference images | at most 10 |
| reference videos | at most 5 |
| reference audio clips | at most 5 |

Numeric-duration estimates use the published prices: $0.0325/sec at 480p, $0.065/sec at 720p, and $0.13/sec at 1080p. Successful generations are charged; the terminal job's settled `billing.charge_micro_usd` is authoritative.

## Error handling

`PikaApiError` preserves:

- HTTP status;
- stable `error.code` when present;
- `Retry-After` when present; and
- the failed job envelope when Pika created a job before rejecting it.

Branch on `error.code`, not the diagnostic message. Do not reuse an idempotency key after a known failure.

## Provider boundary

Pika is an optional generation provider. Local analysis, depth generation, WAN prompt rendering, and package validation remain independent and work without Pika or SwitchApp.
