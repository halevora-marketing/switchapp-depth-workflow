# End-to-end workflow

1. Verify the exact source clip and record its provenance.
2. Run `wandepth analyze-local` to export measured evidence, review frames, and a contact sheet.
3. Review the source and record only observations supported by the media or approved brief. Leave uncertainty explicit and ask for examples when evidence is insufficient.
4. Generate the silent depth map locally with `wandepth depth-local`.
5. Extract and preserve the original audio separately.
6. Write the structured WAN prompt with exact reference roles, one primary identity anchor, gap-free timing, camera/environment direction, and audio/text rules.
7. Run `validate-prompt`; unresolved placeholders are a hard failure.
8. Render `WAN prompt.txt`, remux the source audio when required, and validate the completed package.

## Independent analysis outputs

`analyze-local` creates:

- `analysis.json`: machine-readable measured facts and unresolved observation fields;
- `Full analysis.md`: readable evidence summary and observation checklist;
- `analysis-frames/`: timestamped JPEG samples; and
- `contact-sheet.jpg`: a review surface.

Candidate cuts and motion scores are signals, not semantic conclusions. They can guide review but do not prove an action, subject, location, or story beat.

## Long sources

Split sources over 30 seconds into exact, contiguous sections. Cover the full runtime without gaps or substituted excerpts. Keep each section tied to the same item key and document its time range.
