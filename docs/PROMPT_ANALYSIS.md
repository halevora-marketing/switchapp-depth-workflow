# WAN prompt analysis

The renderer is intentionally WAN-specific. It follows the style established by successful production prompts: direct paragraph labels, explicit material bindings, strict reference-role boundaries, an identity lock, and a fully timed shot timeline.

## Required evidence

Before writing semantic prompt content, obtain explicit facts for:

- approved concept and runtime;
- identity reference and any supporting identity views;
- wardrobe and props;
- subjects and relationships;
- action at every point in the runtime;
- environment, camera, and lighting;
- dialogue/audio handling and on-screen text; and
- user-supplied negatives or consistency constraints.

If any necessary fact is missing, ask for an example, reference, or written instruction. Do not infer it from filenames, depth data, or ambiguous frames.

## Reference roles

Every asset declares what it controls and what it cannot transfer. Exactly one asset must be the primary identity anchor. A depth/motion reference is restricted to geometry, silhouette motion, choreography, spacing, parallax, framing, and timing. It cannot supply identity or appearance.

## Timing

Stages must begin at 0, touch without gaps or overlaps, and end at the declared runtime. The renderer combines them into one `Shot timeline:` paragraph with exact ranges.

## Validation gate

Validation fails on unresolved markers including `NOT SUPPLIED`, `UNKNOWN`, `TODO`, `TBD`, fill-in tokens, and question-mark placeholders. This makes missing information visible instead of turning it into fabricated prompt detail.
