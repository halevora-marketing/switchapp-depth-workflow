# Contributing

1. Keep service-specific browser automation out of the core package.
2. Add a regression test for every validator or media-command change.
3. Do not commit personal media, model weights, signed URLs, credentials, or production manifests.
4. Keep subprocess calls argument-based; do not invoke a shell.
5. Preserve the workflow invariants documented in `docs/WORKFLOW.md`.

Run before opening a pull request:

```bash
python -m unittest discover -s tests -v
```

