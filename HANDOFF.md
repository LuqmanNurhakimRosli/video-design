# Handoff — Video-Design

Read this and `CLAUDE.md` first. This file holds the current state; `CLAUDE.md` holds the rules.

## Done
- Repo: https://github.com/LuqmanNurhakimRosli/video-design (private to confirm), branch `main`.
- Instagram skills (13 `ig-*`) installed globally (`~/.claude/skills/`) and in `.claude/skills/`.
- Voice profile template at `~/.claude/instagram/voice.md`, still blank (local to the PC).
- Video pack `editing-videos` installed (globally and in `.claude/skills/`).
- Folder layout: one folder per video in `experiences/<Name>/` (footage, output, brief.md, script.md, edit.json).
- Intake rule in `CLAUDE.md`: ask footage / script / style / platform / captions / music / checkpoints before any work.
- Old SEDIC files moved into `experiences/SEDIC/` (footage, output, work). `edit.json` uses `footage_dir: "footage"`.
- GitHub CLI 2.67.0 installed at `~/.local/bin/gh.exe`.

## Decisions
- Footage and renders stay out of git (`.gitignore`). Git holds code, rules and skills only.
- Phone use needs footage in cloud storage. Plan: Google Drive folder for footage and outputs.
- Rendering in the cloud is unverified. Test with one short clip before moving more footage.
- The pipeline runs `python`, not `python3`, on this PC.

## Open
1. Create a Google Drive folder for footage and outputs. Confirm which Google account.
2. Test cloud rendering: one short clip, run `make_video.py` in a cloud session. Check ffmpeg and speech-model availability.
3. Fill in `~/.claude/instagram/voice.md` (or send three of your own reels).
4. Make the first real video through the intake rule.

## Next step
Open item 1 or 2, whichever the user picks first.
