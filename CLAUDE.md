# Video-Design — video production hub

This folder is the one place for making videos. Skills are already installed here
(`.claude/skills/`). Do not reinstall them for a new experience.

## Folder map (where everything goes)
```
Video-Design/
  experiences/
    _template/            ← never edit; copied for every new video
    <Name>/               ← ONE FOLDER PER VIDEO (an "experience")
      footage/            ← raw videos + photos go HERE
      brief.md            ← answers from the intake (goal, style, who does what)
      script.md           ← the script (user's or Claude's)
      edit.json           ← the only config edited per video
      work/               ← cache (transcript, cutaways). Safe to delete
      output/             ← RESULT: preview.mp4 and final.mp4 appear HERE
  assets/music, assets/sfx  ← shared licensed audio (+ LICENSES.md)
  pipeline/               ← the render engine (do not touch)
  REEL_PLAYBOOK.md        ← step-by-step render path
```
Legacy SEDIC leftovers at the root (`SEDIC-experience/`, `output/`, `work/`) are old; leave them
alone unless the user asks to tidy them. New work never goes in the root.

## INTAKE RULE (mandatory, every time)
Whenever the user says they want to make, edit, or create a video (any wording), do this FIRST,
before touching any file or running anything:

1. **Ask the intake questions** with AskUserQuestion (max 4 per call, two calls if needed).
   Skip any question the user already answered. Each question has these options:
   *Have it* / *Don't have it, you do it* / *Don't have it, skip*.
   - **Footage:** do they have raw video/photos? (If yes: they drop it in `experiences/<Name>/footage/`
     or tell me the path. If no: screen-record, motion-graphics-only, or stock?)
   - **Script:** have one (paste it) / rough idea (Claude writes it) / nothing (Claude writes it from the topic).
   - **Style:** `adaptive-glass`, `paper-grid`, `breakout-card`, `text-over-footage`, a reference
     reel (user supplies a downloaded file), or Claude picks.
   - **Platform + length:** Reel/TikTok/Short, target seconds (default 9:16, 30–60 s).
   - **Captions, music, SFX, B-roll, voiceover:** have / want Claude to add / none.
   - **Checkpoints:** Claude does everything, or pause for approval at script / preview / final.
2. **Create the experience:** copy `experiences/_template/` to `experiences/<Name>/` (short name, no spaces),
   save the answers to `brief.md`, and save any script to `script.md`.
3. **Tell the user the exact folder** to drop footage in and where the result will appear
   (`experiences/<Name>/output/`). If footage is missing and is needed, STOP and wait.
4. Only then run the stage skills and the pipeline below.
5. At the end, report the output path, duration, and anything uncertain (names, numbers).

Never guess answers to the intake. If the user says "you decide", choose the defaults and list them.

## Which skill for which stage
- **Idea / research:** `find-ideas` (proven reels to adapt, saved inspiration), `ig-viral`.
- **Script:** `short-form-script` (structure) then `write-script` (hook variants, one body in the user's voice).
  Score hooks with `python ~/.claude/skills/ig-reel/hookscore.py hooks.txt` (use `python`, not `python3`).
  Run `ig-human` over any script or caption before showing it. Voice profile: `~/.claude/instagram/voice.md`.
- **Edit (talking head + B-roll):** `edit-video` (base) plus one style: `adaptive-glass`, `paper-grid`,
  `breakout-card`, `text-over-footage`. `editing-videos` is extra editing judgment (pacing, LUFS, captions).
  Pipeline work still goes through `REEL_PLAYBOOK.md`.
- **Motion graphics / animation:** `hyperframes` (HTML in, MP4 out), `remotion-*`, `embedded-captions`.
- **Audio / talking head recut:** `hyperframes-audio`, `talking-head-recut`.
- **Caption / hashtags / plan:** `ig-caption`, `ig-plan`, `ig-carousel`.
- **Publish:** `publish-and-analyze`. Never post or schedule without the user's approval of the exact file, caption, account and time.
- **Engineering on the pipeline or tools:** Addy's `*-and-*` skills (e.g. `debugging-and-error-recovery`,
  `code-review-and-quality`, `planning-and-task-breakdown`). Use them only when changing code, not for cutting a reel.

Pick the stage's skill, not all of them. Load one style skill per video.

## Rendering a video (after intake)
1. Plan the cuts: `python pipeline/make_video.py experiences/<Name> --report`
   (prints transcript gaps, fillers, room-noise floor). Then fill `pauses`, `fillers`,
   `zooms`, `broll`, `replace`, `emphasis` in `edit.json`.
2. Preview (about 1 min): `python pipeline/make_video.py experiences/<Name>`
   -> `experiences/<Name>/output/preview.mp4`.
3. Final (1080x1920): `python pipeline/make_video.py experiences/<Name> --final`
   -> `experiences/<Name>/output/final.mp4`.

## Rules for working here
- Edit `edit.json`, not the pipeline. Only change `pipeline/make_video.py` for a bug or a new feature.
- Re-run the preview after each config change. The cutaway clips and transcript are cached in `work/`.
- Don't generate contact sheets of every frame. Sample 4-6 frames at the points you changed.
- Captions: only the wording in `replace` is corrected. Check the names and numbers in the transcript.
- The transcript comes from Parakeet (fast, local). For better names, run
  `pipeline/transcribe_fw.py` (faster-whisper, slower) and copy its output to `experiences/<Name>/work/transcript.json`.
- Footage stays where it is. Don't move or delete the user's original files.
- Music and SFX must be licensed and recorded in `assets/*/LICENSES.md`.

Full step-by-step for making a reel: see REEL_PLAYBOOK.md. Use it as the default path.
