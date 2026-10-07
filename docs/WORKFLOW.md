# End-to-end workflow

## 1. Ground the batch

Record the ordered source URLs, target destination, naming convention, expected Sheet/tab when applicable, and whether prompt files should be preserved, versioned, or updated in place. Never reuse a prior batch folder, row range, or account merely because it was used last time.

Assign one stable item key per source URL. Keep the source, audio, analysis, prompts, depth maps, Drive IDs, Sheet row, runtime, and status associated with that key.

## 2. Verify the exact source

Social pages often show suggested clips beside the requested post, and segmented streams may expose a middle byte range without an MP4 header. Before analysis:

- confirm the canonical post identifier;
- inspect the visible primary media, not a suggested card;
- download or reconstruct the complete stream;
- run `switchdepth inspect`;
- review a contact sheet or representative frames; and
- confirm that the action and duration match the request.

If the wrong source was used, discard only the derived staging artifacts and rebuild from the correct source. Do not spend generation credits while correcting the input.

## 3. Analyze first

Run the full video analysis before requesting a depth map. Retain the complete report and derive a short, descriptive title from the primary action, setting, and narrative beat.

A successful report must contain the requested recreation prompts. If structured recreation data is absent, empty, or missing model variants, treat the run as failed and rerun it. Do not silently hand-write replacements and call the analysis complete.

## 4. Create the depth map

Use SwitchApp's completed analysis context or the optional local ONNX fallback. Hosted depth jobs may acknowledge acceptance before media is ready; wait for the final downloadable result.

For sources longer than 30 seconds:

1. split the complete source into consecutive sections of at most 30 seconds;
2. generate one depth map per section;
3. keep all parts under the same item key; and
4. verify that their durations cover the full source without gaps.

Never replace a long source with an excerpt.

## 5. Preserve audio and package

Extract the original audio once. Put that audio back on each delivered depth map so editors can align the grayscale reference on a timeline.

Use the same descriptive title everywhere. A complete default package contains:

- original video;
- original audio;
- full analysis;
- Seedance, Kling, and Gemini prompts;
- a finalized generation prompt; and
- one audio-bearing depth map, or numbered depth-map parts.

## 6. Finalize the prompt

Validate explicit reference roles, identity and hair locks, wardrobe, supporting actors, complete stage timing, camera continuity, and sound. See `PROMPT_ANALYSIS.md`.

If using a browser Enhance action, run it exactly once per prompt and wait for the UI to leave its in-progress state before reading the result. Preserve the pre-enhancement prompt until the enhanced and refined version is safely stored.

## 7. Stage generation safely

Load references in the documented order, confirm that every prompt reference points to the intended asset, choose the requested model/settings, and stop at the paid Generate button unless spending was explicitly authorized.

Analysis approval, depth-map approval, and generation approval are separate when they incur separate costs.

## 8. Upload and track

When Drive and Sheets are in scope:

1. upload files and retain returned IDs/links;
2. read the intended Sheet cells immediately before writing;
3. update the coherent row fields together;
4. preserve formulas, formatting, validation, chips, and unrelated columns; and
5. read back every changed cell exactly.

Use only a status value allowed by the live Sheet. Mark an item complete only after every required artifact and verification succeeds.

