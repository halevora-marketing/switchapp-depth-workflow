# Lessons from production runs

These rules come from repeated failures and recoveries, not theoretical preferences.

## Exact-post verification matters

A social post page can load multiple media streams. The largest or most recently observed stream may belong to a suggested reel. Match the canonical post, visible primary media, duration, and frames before analysis.

## Segmented streams can be incomplete

Observed URLs may include `bytestart` and `byteend` parameters for a middle range. Downloading that URL directly can produce a file without an MP4 header. Obtain the complete asset or reconstruct all required ranges before running FFprobe.

## Analysis and depth are not interchangeable

Analysis defines the title, action, timing, and prompt. The depth map supplies geometry. Running depth first increases the chance of attaching the wrong output or losing the semantic link between artifacts.

## Job acceptance is not completion

Some hosted depth workflows report success when a job is accepted. Completion is the appearance of a final depth-video result that can be downloaded and probed.

## History panels can contain stale results

When a depth panel contains older jobs, match the result to the current item key, source duration, and report context. Never assume the top or newest-looking card is correct.

## Promptless analysis is a failed run

A readable report without structured recreation prompts is incomplete. Rerun the analysis; do not conceal the missing data with an improvised prompt.

## Long clips require full coverage

Depth generation becomes unreliable around 30 seconds in some workflows. Split the full clip into consecutive parts and retain them all. Skipping or excerpting changes the requested source.

## Audio belongs on delivered depth maps

Silent grayscale media is hard to align. Keep the source audio on final depth-map files while retaining a silent intermediate if the generation service requires one.

## Enhancement has a real completion state

Do not read prompt text while the UI still says it is enhancing. Wait for the editor-level control to return to its idle state, then capture the complete result exactly once.

## Paid stages need separate gates

Preparing files, running analysis, generating a depth map, and generating a video can have different costs. A request to prepare or stage is not permission to click a paid Generate button.

## Verification closes the loop

Probe every media output, verify Drive metadata and links, read back Sheet cells, and keep incomplete items visibly incomplete. A confident summary is not a substitute for evidence.

