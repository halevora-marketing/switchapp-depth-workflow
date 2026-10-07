# Independent architecture

The core pipeline has three local boundaries:

1. **Evidence:** FFprobe and OpenCV measure media properties, export samples, calculate frame differences, and flag possible cuts.
2. **Depth:** Depth Anything V2 runs through ONNX Runtime and writes a silent grayscale video. FFmpeg restores approved source audio when needed.
3. **Prompt:** a deterministic validator and renderer produces WAN-style text from explicit structured facts.

No stage calls SwitchApp or another hosted analysis service. No stage sends media to a network endpoint.

## Epistemic boundary

Machine measurements and operator observations are stored separately. The analyzer never claims who a person is, what they are wearing, what they say, what an action means, or where a scene is located. Those fields remain marked `NOT SUPPLIED` until supported by a reviewed source or approved brief.

The prompt validator rejects unresolved fields. This preserves a useful rule: missing information causes a question, not a plausible-sounding invention.
