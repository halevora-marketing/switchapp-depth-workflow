# Prompt analysis and finalization

## Preserve the concept

The final prompt improves reliability; it does not invent a different video. Preserve the approved runtime, action order, expressions, dialogue, on-screen text, camera behavior, setting, wardrobe, props, and sound.

## Reference roles

For the common two-image, source-video, and depth-video arrangement:

- `@Image1` is the primary identity anchor.
- `@Image2` is a supporting view of that same identity. If it conflicts with `@Image1`, `@Image1` wins.
- `@Video1` controls choreography, expressions, prop behavior, environment, camera, lighting, timing, and sound. It must not transfer the source performer's identity or appearance.
- `@Video2` controls depth geometry, subject spacing, silhouette motion, parallax, and framing continuity. It must not supply identity, hair, skin, clothing, color, texture, lighting, people, props, or background appearance.

State both allowed uses and forbidden transfers for every reference.

## Identity and hair lock

Lock the following to the primary identity source:

- face and facial proportions;
- eye shape, nose, lips, jawline, and stable marks;
- skin tone, undertone, and texture;
- age appearance and body proportions;
- makeup, jewelry, piercings, and manicure when identity-controlled; and
- hair color, roots, highlights, texture, density, hairline, cut, length, part, bangs, and established styling.

Reject face swapping, identity blending, beautification drift, skin-tone change, body reshaping, and hair transformation.

## Wardrobe and supporting actors

Written wardrobe instructions are authoritative. A motion source may confirm garment motion, fit behavior, coverage, footwear placement, and prop handling, but it cannot control the wearer's identity.

Supporting actors are distinct generated people unless the user explicitly assigns them identity assets. Asset numbering alone never assigns identity.

## Stage timing

Stages must cover the exact runtime:

- begin at `0.0`;
- have no gaps, overlaps, or reversals;
- start each stage from the prior stage's end state; and
- end at the declared runtime.

Lock left/right hands, feet, props, seats, actor relationships, and the final pose. Keep each action achievable inside its time window.

For a continuous take, do not introduce a cut. For intentional cuts, say exactly what changes and what stays constant.

## Quality gate

Reject a prompt when:

- a non-identity asset controls appearance;
- a depth map supplies color, wardrobe, people, environment appearance, or identity;
- identity or hair descriptors conflict with the primary image;
- wardrobe, coverage, handedness, props, or actors change unintentionally;
- timing does not cover the exact runtime;
- camera instructions contradict the intended edit style;
- sound conflicts with supplied dialogue, music, or ambience; or
- on-screen text wording changes.

The CLI enforces the structural subset of these checks. Human review remains required for semantic and visual conflicts.

