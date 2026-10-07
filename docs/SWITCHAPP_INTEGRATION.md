# SwitchApp integration boundary

This repository intentionally separates deterministic local work from authenticated service work.

## Local responsibilities

- inspect and normalize source media;
- split long clips;
- extract and remux audio;
- optionally create a local ONNX depth map;
- render and validate structured prompts;
- create manifests and validate package completeness; and
- keep production media ignored by Git.

## Authenticated SwitchApp responsibilities

- analyze the source and return the full report;
- provide model-specific recreation prompts;
- create hosted depth maps when requested;
- enhance prompts in the signed-in browser when requested; and
- stage or generate video only within the user's authorization.

Discover available authenticated capabilities at runtime rather than hard-coding private tool names. Never store API keys, OAuth tokens, cookies, signed URLs, or browser data in manifests or logs.

## Recommended state machine

```text
new
  -> source_verified
  -> analysis_running
  -> analysis_complete
  -> depth_running
  -> depth_complete
  -> prompt_finalized
  -> staged
  -> generated (optional)
  -> uploaded (optional)
  -> complete
```

An item moves forward only when the current state is verified. A failed item retains its completed outputs and error details; it is not rewritten as complete.

