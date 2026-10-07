# Migration from SwitchApp

SwitchApp is not required by this project.

Version 0.2 replaces the previous hosted-analysis boundary with local deterministic evidence extraction and uses local ONNX depth generation. The command-line workflow runs without a SwitchApp account, session, browser, or private API.

Existing automation may continue to call the `switchdepth` executable; it is retained as an alias for `wandepth`. Existing multi-model prompt manifests must be migrated to a single `prompts.wan` entry and should add `analysis.evidence: analysis.json`.

Third-party services can still be used voluntarily as replaceable providers, but their output is untrusted input. Copy only verified facts into the observation fields and run local validation before accepting an artifact.
