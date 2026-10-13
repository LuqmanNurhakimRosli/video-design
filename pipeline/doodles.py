"""Hand-drawn maritime doodles as transparent clips (qtrle .mov, alpha), drawn on stroke by stroke.

render(kind, dur, out_dir) -> Path of a 560x400 clip at 30 fps. Palette only: cream ink, amber accent,
slate-blue secondary. Shapes are simple geometry with a seeded wobble, so they look sketched, not clip-art.
"""
import hashlib
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

FPS, BW, BH, SS = 30, 560, 400, 2  # box size, supersample
CREAM, AMBER, BLUE = (237, 232, 216), (255, 200, 61), (91, 127, 166)
INK = (18, 18, 18, 120)  # soft dark under-stroke so thin lines stay readable on video


def arc(cx, cy, rx, ry, a0, a1, n=60):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def wave(x0, x1, y, amp, waves, n=80):
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin(2 * math.pi * waves * i / n)) for i in range(n + 1)]


def poly(*pts, close=False):
    return list(pts) + ([pts[0]] if close else [])


# each stroke: (points, color, width, dotted)
def shapes(kind):
    if kind == "ship":
        return [
            (poly((110, 235), (450, 235), (410, 300), (150, 300), close=True), CREAM, 4, False),
            (poly((235, 235), (235, 190), (335, 190), (335, 235)), CREAM, 4, False),
            (poly((370, 235), (370, 205), (400, 205), (400, 235)), CREAM, 3, False),
            (poly((190, 235), (190, 120)), CREAM, 3, False),
            (poly((190, 120), (250, 142), (190, 164), close=True), AMBER, 4, False),
            (wave(60, 500, 330, 7, 5), BLUE, 3, False),
            (wave(90, 470, 362, 6, 4), BLUE, 3, False),
            (poly((80, 270), (30, 270)), CREAM, 3, True),
        ]
    if kind == "compass":
        s = [(arc(280, 200, 140, 140, 0, 360, 90), CREAM, 4, False), (arc(280, 200, 108, 108, 0, 360, 80), CREAM, 2, False)]
        for k in range(16):
            a = math.radians(k * 22.5)
            r0 = 140 if k % 2 == 0 else 130
            s.append((poly((280 + 140 * math.cos(a), 200 + 140 * math.sin(a)),
                           (280 + (r0 - 16) * math.cos(a), 200 + (r0 - 16) * math.sin(a))), CREAM, 2, False))
        s += [(poly((280, 200), (255, 200), (280, 60), (305, 200), close=True), AMBER, 4, False),
              (poly((280, 200), (255, 200), (280, 340), (305, 200), close=True), CREAM, 3, False),
              (poly((140, 200), (420, 200)), CREAM, 2, False)]
        return s
    if kind == "lighthouse":
        s = [(poly((240, 350), (320, 350), (305, 130), (255, 130), close=True), CREAM, 4, False),
             (poly((246, 270), (314, 270)), CREAM, 3, False), (poly((251, 200), (309, 200)), CREAM, 3, False),
             (poly((250, 130), (250, 98), (310, 98), (310, 130)), CREAM, 4, False),
             (poly((244, 98), (280, 66), (316, 98), close=True), CREAM, 4, False),
             (wave(70, 490, 372, 6, 5), BLUE, 3, False)]
        for dx, dy in ((-1, -0.25), (-1, 0.35), (1, -0.25), (1, 0.35)):
            s.append((poly((280, 114), (280 + dx * 210, 114 + dy * 120)), AMBER, 3, True))
        return s
    if kind == "anchor":
        return [
            (arc(280, 72, 24, 24, 0, 360, 40), CREAM, 4, False),
            (poly((280, 96), (280, 318)), CREAM, 5, False),
            (poly((232, 140), (328, 140)), CREAM, 4, False),
            (arc(280, 232, 120, 96, 8, 172, 50), CREAM, 5, False),
            (poly((160, 236), (140, 206), (186, 214), close=True), AMBER, 4, False),
            (poly((400, 236), (420, 206), (374, 214), close=True), AMBER, 4, False),
            (wave(150, 410, 360, 6, 3), BLUE, 3, False),
        ]
    if kind == "waves":
        return [(wave(30, 530, 110, 12, 4), CREAM, 4, False), (wave(60, 500, 180, 12, 3.5), BLUE, 4, False),
                (wave(30, 530, 250, 12, 4), CREAM, 4, False), (wave(70, 490, 320, 10, 3), BLUE, 3, False),
                (arc(470, 60, 22, 22, 0, 360, 36), AMBER, 4, False)]
    if kind == "route":  # dotted sea route between two coast sketches, amber X marks the spot
        rnd = random.Random(7)
        coast = [(20 + i * 22, 340 - 28 * math.sin(i / 2.2) + rnd.uniform(-9, 9)) for i in range(25)]
        route = [(60 + 440 * t, 250 - 150 * math.sin(math.pi * t) * (1 - 0.3 * t)) for t in [i / 60 for i in range(61)]]
        x, y = route[-1]
        return [(coast, CREAM, 4, False), (route, CREAM, 3, True),
                (poly((x - 18, y - 18), (x + 18, y + 18)), AMBER, 5, False), (poly((x - 18, y + 18), (x + 18, y - 18)), AMBER, 5, False)]
    if kind == "coast_title":  # underline-style coastline for the intro title
        rnd = random.Random(11)
        return [([(20 + i * 12, 200 + 16 * math.sin(i / 3.1) + rnd.uniform(-6, 6)) for i in range(45)], CREAM, 4, False),
                (wave(60, 500, 262, 6, 6), BLUE, 3, False)]
    raise ValueError(kind)


def wobble(pts, seed, amp=1.6):
    """Resample every ~7 px and add smooth low-frequency noise: reads as hand-drawn."""
    out, p0 = [], pts[0]
    for p1 in pts[1:]:
        d = math.dist(p0, p1)
        n = max(1, int(d / 7))
        out += [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n)]
        p0 = p1
    out.append(p0)
    r = random.Random(seed)
    f = [(r.uniform(0.02, 0.05), r.uniform(0, 6.28), r.uniform(0.02, 0.05), r.uniform(0, 6.28)) for _ in range(2)]
    return [(x + amp * sum(math.sin(x * a + b) for a, b, _, _ in f), y + amp * sum(math.sin(y * c + d) for _, _, c, d in f))
            for x, y in out]


def partial(pts, length):
    out, acc = [pts[0]], 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if acc + d >= length:
            t = (length - acc) / d if d else 0
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            return out
        out.append(b)
        acc += d
    return out


def render(kind, dur, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mov = out_dir / f"{kind}_{dur:.2f}.mov"
    if mov.exists():
        return mov
    seed = int(hashlib.md5(kind.encode()).hexdigest()[:6], 16)
    strokes = [(wobble(p, seed + i), c, w, dot) for i, (p, c, w, dot) in enumerate(shapes(kind))]
    lens = [sum(math.dist(a, b) for a, b in zip(p, p[1:])) for p, *_ in strokes]
    total, draw = sum(lens), min(0.9, dur * 0.4)
    frames = out_dir / f"{kind}_frames"
    frames.mkdir(exist_ok=True)
    n = round(dur * FPS)
    for fi in range(n):
        t = fi / FPS
        head = (1 - (1 - min(t / draw, 1)) ** 3) * total  # ease-out
        img = Image.new("RGBA", (BW * SS, BH * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cum = 0.0
        for (pts, col, w, dot), ln in zip(strokes, lens):
            take = min(max(head - cum, 0), ln)
            cum += ln
            if take <= 0:
                continue
            seg = [(x * SS, y * SS) for x, y in partial(pts, take)]
            if dot:  # dotted: dots every ~16 px along the path
                step, acc = 16 * SS, 0.0
                for a, b in zip(seg, seg[1:]):
                    dd = math.dist(a, b)
                    while acc < dd:
                        k = acc / dd if dd else 0
                        x, y = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
                        d.ellipse([x - 3.2 * SS, y - 3.2 * SS, x + 3.2 * SS, y + 3.2 * SS], fill=col + (255,))
                        acc += step
                    acc -= dd
            else:
                for width, fill in ((w + 4, INK), (w, col + (255,))):
                    d.line(seg, fill=fill, width=int(width * SS), joint="curve")
                    for x, y in (seg[0], seg[-1]):
                        r = width * SS / 2
                        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
        fade = min(1.0, max((dur - t) / 0.35, 0))
        a = img.getchannel("A").point(lambda v: int(v * fade))
        img.putalpha(a)
        img.resize((BW, BH), Image.LANCZOS).save(frames / f"{fi:04d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(frames / "%04d.png"),
                    "-c:v", "qtrle", "-pix_fmt", "argb", str(mov)], check=True)
    for f in frames.glob("*.png"):
        f.unlink()
    frames.rmdir()
    return mov


if __name__ == "__main__":  # python pipeline/doodles.py <kind> <dur> <out_dir>
    import sys
    print(render(sys.argv[1], float(sys.argv[2]), sys.argv[3]))
