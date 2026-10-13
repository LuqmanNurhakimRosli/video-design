"""Edit one talking-head experience from its edit.json into a 9:16 MP4.

  python pipeline/make_video.py experiences/<name>            # 540x960 preview, ~1 min
  python pipeline/make_video.py experiences/<name> --final    # 1080x1920 H.264 + AAC
  python pipeline/make_video.py experiences/<name> --report   # gaps + fillers to plan the cuts

Everything per-video lives in experiences/<name>/edit.json. This file is the same for every video.
Transcript, loudness envelope and cutaway clips are cached in <name>/work/, so a re-run only redoes
what you changed.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "pipeline" / "fonts"
FPS = 30
AMBER = "&H3DC8FF&"  # #FFC83D in ASS (BGR)
WIDE, MID = 1.06, 1.10

args = [a for a in sys.argv[1:] if not a.startswith("--")]
FINAL, REPORT = "--final" in sys.argv, "--report" in sys.argv
exp = Path(args[0]).resolve()
cfg = json.loads((exp / "edit.json").read_text(encoding="utf-8"))
main = (exp / cfg["footage_dir"] / cfg["main"]).resolve()
work, outd = exp / "work", exp / "output"
for d in (work / "broll", outd):
    d.mkdir(parents=True, exist_ok=True)


def sh(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)


def ff(*a, **kw):
    sh(["ffmpeg", "-v", "error", "-y", *a], **kw)


def snap(t):
    return round(t * FPS) / FPS


def get_transcript():
    """Word timings [{text,start,end}]. Put a hand-checked file at cfg['transcript'] to skip ASR."""
    cache = work / "transcript.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    tx = work / "tx"
    sh(f'npx --yes hyperframes transcribe "{main}" -e parakeet -d "{tx}" --json',
       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(tx / "transcript.json", cache)
    return json.loads(cache.read_text(encoding="utf-8"))


def get_db():
    """20 ms loudness envelope in dB of the main clip."""
    wav = work / "voice16.wav"
    if not wav.exists():
        ff("-i", str(main), "-ac", "1", "-ar", "16000", str(wav))
    with wave.open(str(wav)) as f:
        a = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(float) / 32768
    m = len(a) // 320
    return 20 * np.log10(np.sqrt((a[: m * 320].reshape(m, 320) ** 2).mean(1)) + 1e-9)


def quiet_at(db, t, r=0.06):
    k0, k1 = int((t - r) / 0.02), int((t + r) / 0.02) + 1
    return (k0 + int(np.argmin(db[k0:k1]))) * 0.02


def report(words, db):
    print(f"room floor {np.percentile(db, 15):.1f} dB | {len(words)} words | ends {words[-1]['end']:.2f}s")
    prev = None
    for w in words:
        if prev and w["start"] - prev["end"] >= 0.25:
            print(f"  gap {w['start'] - prev['end']:.2f}s after {prev['end']:.2f}: ...{prev['text']} | {w['text']}")
        prev = w
    fill = [(round(w["start"], 2), w["text"]) for w in words if w["text"].lower().strip(",.") in {"uh", "um", "erm", "eh", "ah"}]
    print("filler words:", fill)
    print(" ".join(f"{w['start']:.1f}:{w['text']}" for w in words))


def build_keeps(db):
    """Source-time keep ranges with each pause tightened to its 'keep' breath; fillers removed."""
    sm = np.convolve(db, np.ones(3) / 3, mode="same")
    low = sm < np.percentile(db, 15) + 10
    rem = []
    for wa, wb, keep in cfg.get("pauses", []):
        i0, i1 = int((wa - 0.12) / 0.02), int((wb + 0.12) / 0.02)
        best, i = (0, 0), i0
        while i < i1:
            if low[i]:
                j = i
                while j < i1 and low[j]:
                    j += 1
                best = max(best, (i, j), key=lambda p: p[1] - p[0])
                i = j
            else:
                i += 1
        rs, re_ = best[0] * 0.02, best[1] * 0.02
        if re_ - rs > keep + 0.06:
            rem.append([rs + keep / 2, re_ - keep / 2])
    rem += [[quiet_at(db, a), quiet_at(db, b)] for a, b in cfg.get("fillers", [])]
    rem.sort()
    merged = []
    for r in rem:
        if merged and r[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], r[1])
        else:
            merged.append(r)
    keeps, cur = [], cfg["start"]
    for s, e in merged:
        if s > cur:
            keeps.append([snap(cur), snap(s)])
        cur = e
    keeps.append([snap(cur), snap(cfg["end"])])
    out, o = [], 0.0
    for s, e in keeps:
        if e - s >= 0.2:
            out.append({"src": [s, e], "out": [o, o + e - s]})
            o += e - s
    return out, o


def to_out(keeps, t):
    for k in keeps:
        s, e = k["src"]
        if s - 1e-6 <= t <= e + 1e-6:
            return k["out"][0] + (t - s)
    return None


def cue_out(keeps, t, side):
    """A cue time inside a removed pause snaps to the nearest kept edge."""
    v = to_out(keeps, t)
    if v is not None:
        return v
    for a, b in zip(keeps, keeps[1:]):
        if a["src"][1] < t < b["src"][0]:
            return b["out"][0] if side == "start" else a["out"][1]
    return 0.0


def render_broll(i, c):
    key = hashlib.md5(json.dumps(c, sort_keys=True).encode()).hexdigest()[:8]
    dst = work / "broll" / f"{i:02d}_{key}.mp4"
    if dst.exists():
        return dst
    src = str((exp / cfg["footage_dir"] / c["file"]).resolve())
    d = c["end"] - c["start"]
    n = round(d * FPS)
    if c["kind"] == "video":
        cmd = ["-ss", str(c.get("ss", 0)), "-t", f"{d:.4f}", "-i", src, "-an", "-vf",
               "fps=30,scale=1080:1920:flags=lanczos,eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.4"]
    elif c["kind"] == "pan":
        u, (x0, x1) = f"(t/{d:.4f})", c["pan"]
        cmd = ["-loop", "1", "-framerate", "30", "-t", f"{d:.4f}", "-i", src, "-an", "-vf",
               f"scale=-2:1920:flags=lanczos,crop=1080:1920:x='{x0}+({x1}-{x0})*(3*pow({u},2)-2*pow({u},3))':y=0,"
               "eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.5"]
    elif c["kind"] == "vfit":  # landscape video: full width over its own blurred copy
        fc = ("[0:v]fps=30,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              "gblur=sigma=45,eq=brightness=-0.14:saturation=0.9[bg];"
              "[b]scale=1080:-2:flags=lanczos,eq=contrast=1.04:saturation=1.05[fg];[bg][fg]overlay=0:(H-h)/2[v]")
        cmd = ["-ss", str(c.get("ss", 0)), "-t", f"{d:.4f}", "-i", src, "-an", "-filter_complex", fc, "-map", "[v]"]
    else:  # fit: whole photo over its own blurred copy, slow push-in
        w, h = map(int, subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", src]).decode().split("x"))
        H = round(1080 * h / w / 2) * 2
        z = f"1+{c.get('push', 0.06)}*on/{n}"
        fc = (f"[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"gblur=sigma=45,eq=brightness=-0.14:saturation=0.9[bg];"
              f"[b]scale=3240:-2:flags=lanczos,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x{H}:fps=30,"
              f"eq=contrast=1.03:saturation=1.05[fg];[bg][fg]overlay=0:(H-h)/2:shortest=1[v]")
        cmd = ["-loop", "1", "-framerate", "30", "-t", f"{d:.4f}", "-i", src, "-an",
               "-filter_complex", fc, "-map", "[v]"]
    ff(*cmd, "-frames:v", str(n), "-r", "30", "-c:v", "libx264", "-crf", "13", "-preset", "fast",
       "-pix_fmt", "yuv420p", str(dst))
    return dst


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Segoe UI Black,74,&H00FFFFFF,&H00FFFFFF,&H00121212,&H80000000,0,0,0,0,100,100,0,0,1,5,2,2,100,100,430,1
Style: Name,Segoe UI Black,58,&H00FFFFFF,&H00FFFFFF,&H00121212,&H80000000,0,0,0,0,100,100,1,0,1,3,1,1,84,60,0,1
Style: Sub,Segoe UI Semibold,38,&H00E8E8E8,&H00FFFFFF,&H00121212,&H80000000,0,0,0,0,100,100,0.5,0,1,2,1,1,84,60,0,1
Style: Title,Ink Free,118,&H00D8E8ED,&H00D8E8ED,&H00121212,&H80000000,0,0,0,0,100,100,2,0,1,5,2,5,60,60,0,1
Style: Card1,Segoe UI Black,190,&H00D8E8ED,&H00D8E8ED,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,60,60,0,1
Style: Card2,Segoe UI Semibold,54,&H00D8E8ED,&H00D8E8ED,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,60,60,0,1
Style: Card3,Segoe UI,40,&H00A9B9B4,&H00A9B9B4,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def captions(words, keeps, master_len):
    """Phrase captions from word timings, mapped onto the edited timeline."""
    items = []
    for w in words:
        s, e = to_out(keeps, w["start"]), to_out(keeps, w["end"])
        if s is not None:
            items.append((s, e if e is not None else s + 0.2, w["text"]))
    chunks, cur = [], []
    for it in items:
        if cur and (it[0] - cur[-1][1] > 0.3 or len(cur) >= 5):
            chunks.append(cur)
            cur = []
        cur.append(it)
        if it[2].endswith((".", "?", "!")) or (it[2].endswith(",") and len(cur) >= 3):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    emph = {x.lower() for x in cfg.get("emphasis", [])}
    lines = []
    for k, ch in enumerate(chunks):
        text = " ".join(it[2] for it in ch)
        for a, b in cfg.get("replace", {}).items():
            text = text.replace(a, b)
        parts = []
        for tok in text.split():
            core = tok.strip(".,?!\"'").lower()
            parts.append(f"{{\\c{AMBER}}}{tok}{{\\c&HFFFFFF&}}" if core in emph else tok)
        start = max(ch[0][0] - 0.05, 0)
        nxt = chunks[k + 1][0][0] - 0.02 if k + 1 < len(chunks) else master_len
        end = max(min(ch[-1][1] + 0.12, nxt), start + 0.55)
        lines.append((start, end, " ".join(parts)))
    return lines


def ass_file(keeps, words, master_len):
    out = [HEADER.rstrip("\n")]
    for s, e, text in captions(words, keeps, master_len):
        out.append(f"Dialogue: 1,{ts(s)},{ts(e)},Cap,,0,0,0,,{{\\fad(70,50)\\fscx94\\fscy94\\t(0,120,\\fscx100\\fscy100)}}{text}")
    lt = cfg.get("lower_third")
    if lt:
        a, b = lt["at"]
        out.append(f"Dialogue: 2,{ts(a)},{ts(b)},Name,,0,0,0,,{{\\pos(84,1160)\\fad(180,220)}}{lt['name']}")
        out.append(f"Dialogue: 2,{ts(a)},{ts(b)},Sub,,0,0,0,,{{\\pos(84,1236)\\fad(180,220)}}{lt['sub']}")
        out.append(f"Dialogue: 2,{ts(a)},{ts(b)},Sub,,0,0,0,,{{\\pos(40,1150)\\p1\\c{AMBER}\\fad(180,220)}}m 0 0 l 8 0 l 8 138 l 0 138")
    tt = cfg.get("title")
    if tt:
        out.append(f"Dialogue: 2,{ts(tt['at'][0])},{ts(tt['at'][1])},Title,,0,0,0,,{{\pos(540,{tt.get('y', 330)})\fad(200,250)}}{tt['text']}")
    ec = cfg.get("end_card")
    if ec:
        c0 = master_len - ec["lead"]
        for (style, y), line in zip((("Card1", 860), ("Card2", 1000), ("Card3", 1095)), ec["lines"]):
            out.append(f"Dialogue: 2,{ts(c0 + 0.35)},{ts(master_len + ec['tail'])},{style},,0,0,0,,{{\\pos(540,{y})\\fad(300,0)}}{line}")
    return "\n".join(out) + "\n"


def ensure_fonts():
    FONTS.mkdir(parents=True, exist_ok=True)
    for f in ("seguibl.ttf", "seguisb.ttf", "segoeui.ttf"):
        if not (FONTS / f).exists():
            shutil.copy(Path("C:/Windows/Fonts") / f, FONTS / f)


def main_run():
    words = get_transcript()
    db = get_db()
    if REPORT:
        report(words, db)
        return
    keeps, master_len = build_keeps(db)
    zooms = sorted((float(t), float(z)) for t, z in cfg.get("zooms", []))
    zoom_at = lambda t: next((z for s, z in reversed(zooms) if s <= t + 1e-6), WIDE)

    # atomic video segments: split each keep at zoom changes so every segment has one framing
    segs = []
    for k in keeps:
        s, e = k["src"]
        marks = sorted({s, e, *[t for t, _ in zooms if s < t < e]})
        marks = [round(round(t * FPS) / FPS, 4) for t in marks]
        for a, b in zip(marks, marks[1:]):
            if b - a > 1e-6:
                segs.append((a, b, zoom_at(a)))

    # cutaways, rendered once each (cached), placed on the output timeline
    broll = []
    for i, c in enumerate(cfg.get("broll", [])):
        c = dict(c)
        c["start"] = round(cue_out(keeps, c["cue"][0], "start") * FPS) / FPS
        c["end"] = round(cue_out(keeps, c["cue"][1], "end") * FPS) / FPS
        broll.append((render_broll(i, c), c["start"], c["end"]))

    W, H = (1080, 1920) if FINAL else (540, 960)  # preview does the whole graph at half size
    ensure_fonts()
    (work / "captions.ass").write_text(ass_file(keeps, words, master_len), encoding="utf-8")

    tail = cfg.get("end_card", {}).get("tail", 0)
    total = master_len + tail
    inputs = ["-i", str(main)]
    for f, _, _ in broll:
        inputs += ["-i", str(f)]
    inputs += ["-f", "lavfi", "-i", f"color=c={cfg.get('card_color', '0x335543')}:s={W}x{H}:r=30:d={total}"]
    if cfg.get("music"):
        inputs += ["-stream_loop", "-1", "-i", str((exp / cfg["music"]["file"]).resolve())]
    for sfx in cfg.get("sfx", []):
        inputs += ["-i", str((exp / sfx["file"]).resolve())]
    dood = []
    if cfg.get("doodles"):
        sys.path.insert(0, str(ROOT / "pipeline"))
        import doodles
        for d in cfg["doodles"]:
            st = round(cue_out(keeps, d["cue"], "start") * FPS) / FPS
            dood.append((doodles.render(d["kind"], d["dur"], work / "doodles"), st, d["dur"], d.get("x", 260), d.get("y", 110), d.get("scale", 1.3)))
            inputs += ["-i", str(dood[-1][0])]
    d0 = len(broll) + 2 + (1 if cfg.get("music") else 0) + len(cfg.get("sfx", []))
    card_idx = len(broll) + 1

    g = [f"[0:v]tpad=stop_mode=clone:stop_duration={tail}[base0]"]
    prev = "base0"
    for k, (_, s, e) in enumerate(broll, 1):
        g.append(f"[{k}:v]setpts=PTS-STARTPTS+{s}/TB,scale={W}:{H}[c{k}]")
        g.append(f"[{prev}][c{k}]overlay=eof_action=pass:enable='between(t,{s},{e - 0.001})'[o{k}]")
        prev = f"o{k}"
    if cfg.get("end_card"):
        g.append(f"[{card_idx}:v]format=yuva420p,fade=t=in:st={master_len - cfg['end_card']['lead']}:d=0.4:alpha=1[card]")
        g.append(f"[{prev}][card]overlay=eof_action=pass[withcard]")
        prev = "withcard"
    f = W / 1080
    for j, (_, st, dur, x, y, sc) in enumerate(dood):
        g.append(f"[{d0 + j}:v]format=rgba,setpts=PTS-STARTPTS+{st}/TB,scale=iw*{f * sc}:ih*{f * sc}[dd{j}]")
        g.append(f"[{prev}][dd{j}]overlay={(x - 280 * (sc - 1)) * f}:{(y - 200 * (sc - 1)) * f}:eof_action=pass:enable='between(t,{st},{st + dur})'[od{j}]")
        prev = f"od{j}"
    g.append(f"[{prev}]ass=work/captions.ass:fontsdir={os.path.relpath(FONTS, exp).replace(chr(92), '/')}[vfull]")
    g.append("[vfull]scale=out_range=tv:flags=accurate_rnd,format=yuv420p[v]")

    segv, sega = [], []
    for k, (a, b, z) in enumerate(segs):
        segv.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,fps=30,"
                    f"crop=w=720/{z}:h=1280/{z}:x=(720-720/{z})/2:y=(1280-1280/{z})*0.35,"
                    f"scale={W}:{H}:flags=lanczos,curves=all='0/0 0.20/0.23 0.5/0.55 0.8/0.84 1/1',"
                    f"eq=contrast=1.05:saturation=1.12,colorbalance=rs=0.02:bs=-0.03:rm=0.02:bm=-0.02,"
                    f"unsharp=5:5:0.5[v{k}]")
        sega.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                    f"afade=t=in:d=0.008,afade=t=out:st={b - a - 0.008:.4f}:d=0.008[a{k}]")
    n = len(segs)
    ins = "".join(f"[v{k}][a{k}]" for k in range(n))
    g_base = ";".join(segv + sega) + f";{ins}concat=n={n}:v=1:a=1[mv][ma]"
    audio_sfx = []
    audio = (f"[ma]pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1,highpass=f=80,afftdn=nr=9:nf=-40,"
             f"equalizer=f=250:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2,"
             f"acompressor=threshold=-22dB:ratio=3:attack=10:release=140:makeup=3,"
             f"afade=t=out:st={master_len - 0.25:.3f}:d=0.5[vc]")
    # music bed + sound effects, then one loudness pass over the whole mix (-14 LUFS / -1.3 dBTP)
    mix_in, mix_labels = 1, ["[vc]"]
    for k, sfx in enumerate(cfg.get("sfx", [])):
        idx = len(broll) + 2 + (1 if cfg.get("music") else 0) + k
        at = cue_out(keeps, sfx["cue"], "start") if "cue" in sfx else sfx["at"]
        ms = int(at * 1000)
        audio_sfx.append(f"[{idx}:a]adelay={ms}|{ms},volume={sfx.get('gain_db', -8)}dB[s{k}]")
        mix_labels.append(f"[s{k}]")
    if cfg.get("music"):
        mi = len(broll) + 2
        audio_sfx.insert(0, f"[{mi}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
                            f"volume={cfg['music'].get('gain_db', -20)}dB,"
                            f"afade=t=out:st={total - 1.5:.3f}:d=1.5[mus]")
        mix_labels.insert(1, "[mus]")
    n_mix = len(mix_labels)
    audio = (";".join(audio_sfx) + (";" if audio_sfx else "") + audio[:audio.index("[vc]")] + "[vc];"
             + "".join(mix_labels) + f"amix=inputs={n_mix}:duration=first:normalize=0,"
             f"loudnorm=I=-14:TP=-1.3:LRA=11,alimiter=limit=0.78:level=disabled,apad=whole_dur={total:.3f}[a]")
    graph = ";".join(segv + sega) + f";{ins}concat=n={n}:v=1:a=1[mv][ma];" + ";".join(
        [g[0].replace("[0:v]", "[mv]")] + g[1:]) + ";" + audio
    (work / "graph.txt").write_text(graph, encoding="utf-8")

    out = outd / ("final.mp4" if FINAL else "preview.mp4")
    enc = (["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-level", "4.2"]
           if FINAL else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "26"])
    ff(*inputs, "-filter_complex_script", "work/graph.txt", "-map", "[v]", "-map", "[a]",
       "-r", "30", "-pix_fmt", "yuv420p", "-t", f"{total:.3f}", *enc,
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
       str(out), cwd=exp)
    print(f"{n} segments, {len(broll)} cutaways, master {master_len:.2f}s, total {total:.2f}s -> {out}")


if __name__ == "__main__":
    main_run()
