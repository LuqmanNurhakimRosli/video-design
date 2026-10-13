# Brief — AAP2026

- Goal / topic: Digital access for Orang Asli youth. Access before AI: connectivity, devices, training.
- Platform + length: Reel, 9:16, 1080x1920, ~120 s (six segments, 0:00–2:00)
- Footage: none. AI-generated clips (Veo / Sora / Runway / Kling). Stat cards, numbers and end card built in CapCut or hyperframes. Clips go in `footage/`.
- Script: have (script.md, with per-shot AI generation prompts)
- Style: Claude picks (documentary, soft pink and white grade, see script.md master style)
- Captions / music / SFX / B-roll / voiceover: captions burned in CapCut; low-volume ambient music; voice-over recorded by the user (not generated); B-roll = the montage shots in 5B–5D
- Checkpoints: approve script (done) / approve preview / approve final
- Names and numbers to spell right: ayoasean, AAP2026, AYOTRACE2026, ASEANYouth, DOSM 2025, Borgen Project. Figures "0.5%", "30.8%", "8%", "97.1%" are unverified: check against DOSM before posting.

## Build (2026-10-13)
- Stills: 15 Canva AI images (no video API on this PC), exported 1080x1920 into `footage/`.
  Canva scratch design "AAP2026 reel stills (scratch export)" holds them; safe to delete.
- Render: `python experiences/AAP2026/build.py` -> `output/final.mp4` (2:00, camera moves, captions, transitions, music).
- Music: ForestWalk (chosic.com), license NOT VERIFIED in assets/music/LICENSES.md. Verify or swap before posting.
- Voice-over not recorded yet. Captions carry the message without it.

## Notes
- Name is a default (from the hashtag #AAP2026). Rename the folder if you prefer another.
- Pipeline note: `make_video.py` expects talking-head footage. For AI-generated clips, assemble in CapCut and use the pipeline only if the footage is cut from your own recording.
- Before posting: community review of depictions; label as AI-generated.
