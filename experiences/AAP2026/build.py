"""Build the AAP2026 reel (9:16, 2:00) from the AI stills in footage/ with ffmpeg.

Each still gets a slow camera move and its on-screen text, then the clips are
joined with the transitions from script.md and a music bed is mixed under.
Run: python experiences/AAP2026/build.py  ->  experiences/AAP2026/output/final.mp4
"""
import shutil
import subprocess
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[1]
FOOT, WORK, OUT = EXP / "footage", EXP / "work", EXP / "output"
FPS, W, H = 30, 1080, 1920
FONT = "segoeuib.ttf"
PINK = "0xF7A8BE"
INK = "0x2A1A22"
MUSIC = ROOT / "assets/music/bgm-ForestWalk-320bit(chosic.com)(chill).mp3"

_n = 0


def alpha(t0, t1, f=0.35):
    return (f"if(lt(t,{t0}),0,if(lt(t,{t0 + f}),(t-{t0})/{f},"
            f"if(lt(t,{t1 - f}),1,if(lt(t,{t1}),({t1}-t)/{f},0))))")


def text(s, t0, t1, size=66, y="h*0.70", color="white", x=None, shadow=True):
    """Fade-and-rise text. x=None centres it."""
    global _n
    _n += 1
    name = f"text/t{_n:02d}.txt"
    (WORK / name).write_text(s, encoding="utf-8", newline="\n")  # CRLF draws as a blank line
    xs = "(w-text_w)/2" if x is None else str(x)
    sh = "shadowcolor=black@0.55:shadowx=0:shadowy=3:" if shadow else ""
    return (f"drawtext=fontfile={FONT}:textfile={name}:expansion=none:text_align=C:"
            f"fontsize={size}:fontcolor={color}:line_spacing={size // 5}:{sh}"
            f"x={xs}:y='{y}+22*max(0,1-max(0,t-{t0})/0.4)':alpha='{alpha(t0, t1)}'")


def cap(s, t0, t1):
    return [text(s, t0, t1)]


def bar(x, y, wmax, h, color, t0, t1, steps=20, grow=0.7):
    """Bar that grows from the left with an ease-out (drawbox has no time variable)."""
    dt = grow / steps
    out = []
    for i in range(1, steps + 1):
        w = max(2, round(wmax * (1 - (1 - i / steps) ** 3)))
        end = t1 if i == steps else t0 + i * dt
        out.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color={color}:t=fill:"
                   f"enable='between(t,{t0 + (i - 1) * dt:.3f},{end:.3f})'")
    return out


def stats():
    # Figures from the brief; unverified until checked against DOSM (see brief.md).
    big = 640  # bar width for 30.8%
    return [
        text("Sources: DOSM 2025 · Borgen Project", 0.4, 20, 30, "h-300", "white@0.75"),
        text("0.5%", 0.4, 6.4, 300, "h*0.28"),
        text("of Malaysia's population\nare Orang Asli", 0.9, 6.4, 60, "h*0.28+380"),
        text("30.8%", 6.8, 13.0, 300, "h*0.26", PINK),
        text("of Orang Asli are illiterate", 7.2, 13.0, 60, "h*0.26+380"),
        text("vs 8% nationally", 8.2, 13.0, 72, "h*0.26+480"),
        text("Illiteracy rate", 13.4, 20, 44, "600", "white@0.8", x=140),
        text("Orang Asli", 13.4, 20, 52, "700", x=140),
        *bar(140, 780, big, 96, PINK, 13.6, 20),
        text("30.8%", 14.3, 20, 64, "790", PINK, x=140 + big + 30),
        text("National", 13.7, 20, 52, "960", x=140),
        *bar(140, 1040, round(big * 8 / 30.8), 96, "white", 13.9, 20),
        text("8%", 14.6, 20, 64, "1050", x=140 + round(big * 8 / 30.8) + 30),
    ]


def endcard():
    return [
        f"drawbox=x=0:y=0:w={W}:h=18:color={PINK}:t=fill",
        f"drawbox=x=0:y={H - 18}:w={W}:h=18:color={PINK}:t=fill",
        text("Share this.", 0.2, 9, 128, "h*0.36", INK, shadow=False),
        text("Tag @ayoasean", 0.5, 9, 64, "h*0.36+190", INK, shadow=False),
        text("#AAP2026  #AYOTRACE2026  #ASEANYouth", 0.8, 9, 40, "h*0.36+300", "0xC2577A", shadow=False),
        text("Visuals are AI-generated", 0.8, 9, 30, "h-220", f"{INK}@0.6", shadow=False),
    ]


# Camera moves for zoompan (on = output frame, F = frames in the clip).
CX, CY = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
MOVES = {
    "in": ("1+0.10*on/F", CX, CY),
    "out": ("1.10-0.10*on/F", CX, CY),
    "slow": ("1+0.05*on/F", CX, CY),
    "panup": ("1.10", CX, "(ih-ih/zoom)*(1-on/F)"),
    "shake": ("1.07", f"{CX}+10*sin(on*0.35)", f"{CY}+8*cos(on*0.27)"),
}


def shots():
    # (still, seconds on screen, move, overlays, transition into the next clip)
    return [
        ("1A", 7, "in", cap("Malaysia says\nAI is for everyone.", 0.6, 7.0), ("fade", 0.4)),
        ("1B", 8, "in", [], ("fade", 0.04)),
        ("2A", 6, "out", [], ("fade", 0.04)),
        ("2B", 4, "in", cap("97.1% have internet.", 0.2, 4.0), ("fade", 0.04)),
        ("2C", 5, "shake", cap("Not everyone.", 0.3, 5.0), ("fadewhite", 0.3)),
        ("3BG", 20, "slow", stats(), ("fade", 0.5)),
        ("4A", 8, "out", [], ("fade", 0.3)),
        ("4B", 7, "in", cap("A free AI programme.", 0.5, 7.0), ("fade", 0.3)),
        ("4C", 10, "out", cap("What happens when\nthe signal isn't there?", 0.8, 10.0), ("fadewhite", 0.5)),
        ("5A", 8, "in", cap("Access before AI:\nconnection, devices, training.", 0.6, 8.0), ("fade", 0.3)),
        ("5B", 7, "panup", cap("Training.", 0.4, 7.0), ("fade", 0.3)),
        ("5C", 7, "in", cap("Connection.", 0.4, 7.0), ("fade", 0.3)),
        ("5D", 8, "in", cap("For every\nyoung Malaysian.", 0.5, 8.0), ("fadewhite", 0.8)),
        ("6A", 8, "in", [], ("fade", 0.4)),
        ("6B", 4, "slow", [], ("fadewhite", 0.6)),
        ("END", 3, None, endcard(), None),
    ]


def run(cmd):
    subprocess.run(cmd, cwd=WORK, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def render_clip(name, dur, move, overlays, path):
    frames = round(dur * FPS)
    draw = ",".join(overlays) or "null"
    if move is None:
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0xFFF4F6:s={W}x{H}:r={FPS}:d={dur}",
               "-filter_complex", f"[0:v]{draw}[v]"]
    else:
        z, x, y = (e.replace("F", str(frames)) for e in MOVES[move])
        cmd = ["ffmpeg", "-y", "-i", str(FOOT / f"{name}.png"), "-i", "grad.png", "-filter_complex",
               f"[0:v]scale={W * 2}:{H * 2},zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},"
               f"setsar=1[bg];[bg][1:v]overlay=0:0[g];[g]{draw}[v]"]
    run(cmd + ["-map", "[v]", "-frames:v", str(frames), "-c:v", "libx264", "-crf", "16",
               "-preset", "medium", "-pix_fmt", "yuv420p", str(path)])


def main():
    (WORK / "text").mkdir(parents=True, exist_ok=True)
    (WORK / "clips").mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    shutil.copy(Path("C:/Windows/Fonts") / FONT, WORK / FONT)
    # Bottom gradient so lower-third text stays readable on bright stills.
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=black:s={W}x{H}", "-frames:v", "1", "-vf",
         "format=rgba,geq=r=0:g=0:b=0:a='if(gt(Y,H*0.5),255*0.6*pow((Y-H*0.5)/(H*0.5),1.3),0)'",
         "grad.png"])

    plan = shots()
    clips, total = [], 0
    for name, dur, move, overlays, trans in plan:
        clip_dur = dur + (trans[1] if trans else 0)  # extra length is eaten by the crossfade
        path = WORK / "clips" / f"{name}.mp4"
        print(f"render {name} ({dur}s)")
        render_clip(name, clip_dur, move, overlays, path)
        clips.append((path, clip_dur, trans))
        total += dur

    inputs, chain = [], []
    for path, _, _ in clips:
        inputs += ["-i", str(path)]
    prev, length = "[0:v]", clips[0][1]
    for i in range(1, len(clips)):
        kind, d = clips[i - 1][2]
        chain.append(f"{prev}[{i}:v]xfade=transition={kind}:duration={d}:offset={length - d:.3f}[x{i}]")
        prev, length = f"[x{i}]", length + clips[i][1] - d
    chain.append(f"{prev}noise=alls=4:allf=t,format=yuv420p[v]")
    m = len(clips)
    chain.append(f"[{m}:a]atrim=0:{total},asetpts=N/SR/TB,loudnorm=I=-18:TP=-1.5,"
                 f"afade=t=in:d=1.5,afade=t=out:st={total - 4}:d=4[a]")
    final = OUT / "final.mp4"
    print("join + music")
    run(["ffmpeg", "-y", *inputs, "-i", str(MUSIC), "-filter_complex", ";".join(chain),
         "-map", "[v]", "-map", "[a]", "-t", str(total), "-r", str(FPS), "-c:v", "libx264", "-crf", "18",
         "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
         str(final)])
    print(f"done -> {final} ({total}s)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode(errors="replace")[-3000:])
        raise SystemExit(1)
