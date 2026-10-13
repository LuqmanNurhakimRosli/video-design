# Reel playbook (for the AI agent)

Goal: an Instagram Reel from talking-head footage, B-roll and photos, in one config-driven pass.
Read this file and `pipeline/README.md` only. Do not re-read the skills or the old scripts.

## Output spec (fixed)
- 1080×1920 (9:16), 30 fps, H.264 High, yuv420p, faststart.
- AAC 48 kHz stereo, about -14 LUFS integrated, true peak ≤ -1.3 dBTP.
- Length 15–90 s. Safe zone: keep captions above the bottom 430 px.

## Folder layout
```
Video-Design/
  REEL_PLAYBOOK.md        ← this file
  CLAUDE.md               ← hub rules
  pipeline/make_video.py  ← the one engine (do not change per video)
  assets/music/           ← royalty-free tracks   + LICENSES.md
  assets/sfx/             ← sound effects          + LICENSES.md
  experiences/<Name>/
    footage/              ← your raw clips and photos (or set footage_dir)
    edit.json             ← the only file you edit per video
    work/                 ← cache (transcript, cutaways). Safe to delete.
    output/final.mp4      ← deliverable; preview.mp4 while iterating
```

## Tools (already installed, do not reinstall)
- FFmpeg 8.x, Node 22, Python 3.11, uv, Git.
- HyperFrames CLI (`npx hyperframes`) with the Parakeet ASR model.
- Skills in `.claude/skills/`: hyperframes-*, embedded-captions, talking-head-recut, remotion-*, video-editing.
- Optional: faster-whisper (better names and numbers) via
  `uv run --python 3.12 --with faster-whisper` — only if the user asks for higher caption accuracy.

## Steps
1. **Set up.** `copy experiences/_template experiences/<Name>`. Put footage in `experiences/<Name>/footage/`.
2. **Music and SFX (optional).** Put a track in `assets/music/`, a sound in `assets/sfx/`.
   Record its source and license in that folder's `LICENSES.md`. Never use unlicensed audio.
   Music is looped and faded automatically; target -20 to -22 dB under the voice.
3. **Plan.** `python pipeline/make_video.py experiences/<Name> --report`
   Read the gaps, the filler list and the word timings. Do not read the whole transcript twice.
4. **Write edit.json** in one pass:
   - `main`, `start`, `end`
   - `pauses` as `[start, end, keep_seconds]` for gaps of 0.3 s or more
   - `fillers` as `[start, end]` for "uh"/"um"
   - `zooms` as `[time, 1.06|1.10|1.15]`, changed only at cuts
   - `broll` items: `{file, kind: video|pan|fit, cue:[start,end], ss|pan|push}`
   - `replace` for caption corrections, `emphasis` for amber words
   - `lower_third`, `end_card`, `music`, `sfx`
5. **Preview.** `python pipeline/make_video.py experiences/<Name>` (about 1 min when cached).
   Check 4–6 sampled frames at the places you changed, not every frame.
6. **Fix and re-preview** only the parts that failed.
7. **Final.** `python pipeline/make_video.py experiences/<Name> --final`
   Then verify: `ffprobe` for 1080×1920 / 30 fps / H.264 / AAC 48 kHz, and
   `ffmpeg -af loudnorm=I=-14:TP=-1.3:print_format=summary -f null -` for loudness.
8. **Report to the user:** output path, duration, measured LUFS and dBTP, and any caption
   words you were not sure about.

## Token rules
- Use `--report` output instead of reading transcript files.
- Do not open video files or images in full. Use ffprobe and single-frame extracts.
- Never produce a contact sheet of every frame. One sheet of 4–6 frames is enough.
- Don't re-transcribe a clip that already has `work/transcript.json`.
- Edit config, not code. Change `pipeline/make_video.py` only for a bug.
- Ask the user only when a fact is missing: names, numbers, which take to use, music choice.

## Known limits
- Parakeet mishears names and numbers. Check captions against the user's notes, or switch to faster-whisper.
- The 720p footage is upscaled to 1080p; expect softness. Don't zoom more than 1.15x.
- A first run with new cutaways takes a few minutes (each is encoded once and cached).
- Single-pass loudness: measured results can sit about 0.3 LU from target.
