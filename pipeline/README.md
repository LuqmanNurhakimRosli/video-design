# Video pipeline: criteria for fast, clean edits

Written for: you, the creator, when you record a new experience.

## Why one run took 50 minutes
- Most of the time went to repeated full re-renders, separate transcription passes, and a slow
  final encode. Each fix re-ran the whole chain.
- The pipeline fixes this: one engine, one config per video (`edit.json`), cached transcript and
  cutaways, and a half-size preview.
- Measured on the SEDIC edit (77 s clip, 17 video segments, 7 cutaways):
  - First preview, including cutaway renders: 3 min 55 s.
  - Cached preview: 64 s.
  - Final 1080x1920 has not been timed through the pipeline yet. Expect several minutes.

## Recording (the biggest time saver)
- Shoot 9:16 at 30 fps, one mic, quiet room. Record each take with a clean breath before and after.
- Say each point once. A retake is cheaper than a long cut.
- Keep the phone at eye level and steady. Shoot 3-6 s of B-roll for each claim
  (a screen, the booth, people, objects). Name files with the timestamp, e.g. `booth_01.mp4`.
- Target 60-120 s per video. Shorter scripts are easier to cut well.

## Editing rules (what the pipeline assumes)
- Pauses: tighten only gaps of 0.3 s or more. Keep about 0.2-0.3 s of air after a sentence.
- Filler words ("uh", "um"): remove them. Keep a short beat before a deliberate pause.
- Cutaways: 2.5-4 s, placed on the line they illustrate. Landscape photos get a blurred background.
- Zoom: switch framing only at a cut, between 1.06x and 1.15x. Don't zoom more than once every 3 s.
- Captions: 2-5 words per line, safe zone above the bottom 430 px (platform UI covers the bottom).
  Highlight at most one or two words per line.
- Audio: about -14 LUFS integrated, true peak -1.5 dBTP. Use only royalty-free music, at about -22 dB
  under the voice, and note its license.
- Design: one accent color (amber here), forest green end card, no effects beyond the crop and fades.

## Speed checklist
1. `--report` once, then write the whole edit config in one pass.
2. Preview once. Fix all problems from that one preview before the next run.
3. Only then run `--final`.
4. Check 4-6 frames plus the loudness of the final file. Don't review every frame.
