# Motion design references and assets: checked guide

Checked 2026-10-13. Written for: you, when picking sources for a reel. Each entry says what was verified and what wasn't.

## Rules for this project
1. **Study, don't copy.** Use references to learn a technique (timing, easing, layout, type), then rebuild it in our pipeline. Don't reuse someone else's frames, footage or project files in a published reel.
2. **Every music or SFX track gets a row in `assets/*/LICENSES.md`** before posting. Free does not mean no-credit; check the credit rule.
3. **Paid marketplaces (Motion Array, VideoHive, Envato) need their own licence check** for social ads. Don't assume a subscription covers sponsored posts.

## Free assets

| Source | What it gives | Licence status | Use here? |
|---|---|---|---|
| **Uppbeat** | Music, SFX | Free tier: credit required, one credit per download; reuse needs a new download. Sources disagree on commercial and sponsored use. Premium removes the credit requirement. Redistribution and remixing banned. | Music only, and only after checking the current licence page. Could not load it directly (certificate error). |
| **Mixkit** | Stock video, music, SFX, video templates | Separate licence per item type ("Stock Video Free", "Stock Video Restricted", "Stock Music Free", etc.). Read the per-item licence before use. | Good for B-roll and SFX. Check each item's licence. |

## Paid marketplaces

| Source | Verified | Not verified |
|---|---|---|
| **Motion Array** | Everything plan about $25/mo billed yearly ($40 monthly); Video Templates about $16/mo yearly. Templates and presets come with Video Templates; stock, music and plugins only on Everything. Team plan $27/member/mo. | Could not load their site (403). Prices come from third-party sources, so confirm before paying. |
| **VideoHive** | Not checked. | Check pricing and licence before buying. |

## Learning and references (study, don't download)

| Source | Verified | Use |
|---|---|---|
| **Art of the Title** | Active. Covers film and TV title sequences with written breakdowns (e.g. *Babystar*, *Liaison*). | Reference for title and caption motion. |
| **landing.love** | Active, updated 2026. Full-page video recordings of about 2,100 animated sites. | Reference for web-style motion and UI transitions. |
| **School of Motion** | Active. Free items include a blog and a free course, "A Motion Design Masterpiece". Paid All-Access courses. | Tutorials. Free project files not confirmed. |
| **Holdframe** | Now run by School of Motion. Sells project files, bundled with video walkthroughs from the artists. | Paid. The old Holdframe domain doesn't resolve; go through School of Motion. |
| **Ordinary Folk** | The domain did not resolve. The only related match is a School of Motion course. | **Not confirmed.** Don't treat the free project files in the original list as real until checked. |
| **Awwwards, Dribbble, Behance, Stash, Motiongrapher, Inspiration Grid, CG Society** | Not checked in this pass. | Browse for ideas. |

## Reel creation tools from the original list (not checked)
CapCut, Canva, InVideo, HeyGen, OpusClip, Pictory, Klap, Runway, Pika. Not checked for pricing, licence, or whether output can be used in sponsored posts. Check before relying on them.

## Influencer list (not checked)
The follower counts and niches in the original list are unverified. Use creators as study material only. Don't quote their numbers.

## What applies to this system

Our pipeline is already set up for the motion work these sources cover:

| Need | Our tool | Reference to study |
|---|---|---|
| Animated stat cards, lower-thirds, title cards | `hyperframes` (HTML to MP4) and `remotion-*` | Art of the Title, landing.love |
| AI stills with camera moves and captions | `experiences/AAP2026/build.py` (ffmpeg) | Reel examples from School of Motion courses |
| Caption timing and pacing | `editing-videos`, `embedded-captions` | School of Motion blog |
| Music and SFX | `assets/music`, `assets/sfx` with LICENSES.md | Mixkit, Uppbeat (after licence check) |

## Decisions (2026-10-13)
- **Uppbeat: not used.** Its licence page could not be read from here (certificate error, then not reachable). We already have music in `assets/music`, so nothing depends on Uppbeat. Revisit only if we need a track we don't have, and then read the licence on their site first.
- **Motion Array: not bought.** Its official site returned 403. No purchase until pricing and the social-media licence are confirmed on the official site.
- **Ordinary Folk project files: dropped.** The domain didn't resolve, and the one live lead (a School of Motion course) doesn't say its files are free. Nothing in the pipeline needs them.
- No paid asset has been bought or downloaded.

## Still to do (only if the need comes up)
- Confirm Uppbeat's licence and Motion Array pricing from a browser, before using either.
- Check the reel tools (CapCut, Canva, InVideo, Runway, etc.) for licence and pricing only when we pick one for a real project.
