"""Countdown Reel (1080x1920): ATB clip on top, our own fact card below, facts pop in one by one.
python make/countdown.py 2  -> out/countdown_2.mp4 + out/countdown_2_cover.jpg
Reads ATB clips / music / sfx / font from E:/Claude/FMM/assets (read-only, never written)."""
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FMM = Path("E:/Claude/FMM/assets")
FONT = str(FMM / "fonts/Anton-Regular.ttf")
OUT = ROOT / "out"
W, H, TOP = 1080, 1920, 770  # top panel = ATB
DUR = 10.0
FACT_T = [2.2, 3.7, 5.2, 6.7]  # when each fact pops in

# Per day: facts (each confirmed by 2+ sources, checked 16 Nov 2026) and ATB clips (calm/hype, no phone screens).
# Sources: Variety, VICE, Engadget, GameDeveloper, TweakTown, Rockstar Support via Yahoo Tech + eGamersWorld.
DAYS = {
    2: (["THURSDAY 19 NOVEMBER", "PS5 + XBOX SERIES X|S", "$79.99 STANDARD EDITION", "NO PC VERSION (YET)"],
        ["24_wait_for_it", "49_nodding_hype"]),
    1: (["UNLOCKS MIDNIGHT LOCAL TIME", "NEW ZEALAND PLAYS FIRST", "PRE-LOAD IS ALREADY OPEN", "BOXED COPY = CODE, NO DISC"],
        ["49_nodding_hype", "24_wait_for_it"]),
    0: (["PS5 + XBOX SERIES X|S", "STANDARD $79.99", "ULTIMATE $99.99", "NO PC VERSION (YET)"],
        ["21_screaming_hype", "49_nodding_hype"]),
}


def font(n):
    return ImageFont.truetype(FONT, n)


def grad(w, h, stops):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / (h - 1)
        for a, b in zip(stops, stops[1:]):
            if a[0] <= t <= b[0]:
                k = (t - a[0]) / (b[0] - a[0])
                d.line([(0, y), (w, y)], fill=tuple(int(a[1][j] + (b[1][j] - a[1][j]) * k) for j in range(3)))
                break
    return im


def neon_text(img, xy, text, f, color, anchor="mm"):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text(xy, text, font=f, fill=color + (255,), anchor=anchor, stroke_width=10, stroke_fill=color + (255,))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow)
    img.alpha_composite(glow)
    ImageDraw.Draw(img).text(xy, text, font=f, fill=(255, 255, 255, 255), anchor=anchor, stroke_width=4, stroke_fill=color + (255,))


def base_card(days):
    """Bottom panel without facts (H-TOP tall)."""
    h = H - TOP
    card = grad(W, h, [(0, (25, 6, 50)), (0.6, (90, 15, 90)), (1, (200, 60, 90))]).convert("RGBA")
    d = ImageDraw.Draw(card)
    d.rectangle((0, 0, W, 10), fill=(255, 30, 180))  # neon seam under ATB
    d.rectangle((0, 10, W, 16), fill=(0, 235, 255))
    neon_text(card, (W // 2, 85), "GTA 6", font(100), (255, 30, 180))
    if days:
        neon_text(card, (W // 2, 235), str(days), font(250), (0, 235, 255))
        sub = "DAY LEFT" if days == 1 else "DAYS LEFT"
    else:
        neon_text(card, (W // 2, 235), "OUT NOW", font(190), (0, 235, 255))
        sub = "THURSDAY 19 NOVEMBER"
    d = ImageDraw.Draw(card)
    d.text((W // 2, 390), sub, font=font(72), fill=(255, 225, 90), anchor="mm")
    return card


def fact_layer(i, facts):
    """One fact pill, full-panel transparent layer."""
    layer = Image.new("RGBA", (W, H - TOP), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 460 + i * 98
    d.rounded_rectangle((90, y, W - 90, y + 84), radius=42, fill=(15, 5, 35, 225), outline=(0, 235, 255), width=4)
    d.text((W // 2, y + 42), facts[i], font=font(52), fill=(255, 255, 255), anchor="mm")
    return layer


def main(days):
    OUT.mkdir(exist_ok=True)
    tmp = OUT / f"_cd{days}"
    tmp.mkdir(exist_ok=True)
    FACTS, names = DAYS[days]
    base_card(days).save(tmp / "card.png")
    for i in range(len(FACTS)):
        fact_layer(i, FACTS).save(tmp / f"fact{i}.png")
    # ATB clips; crop out the FMM shirt logo (keep top 500 of 608 px)
    clips = [FMM / f"atb_clips/{n}.mp4" for n in names]
    music = FMM / "music/Racecar - The Grey Room _ Density & Time.mp3"
    pop, whoosh = FMM / "sfx/pop.wav", FMM / "sfx/whoosh.wav"
    cw = int(500 * W / TOP)  # crop width that keeps the panel ratio
    vf_top = f"crop={cw}:500:(iw-{cw})/2:0,scale={W}:{TOP},setsar=1,eq=brightness=0.04"
    inputs = ["-i", str(clips[0]), "-i", str(clips[1]), "-loop", "1", "-i", str(tmp / "card.png")]
    for i in range(len(FACTS)):
        inputs += ["-loop", "1", "-i", str(tmp / f"fact{i}.png")]
    inputs += ["-i", str(music), "-i", str(whoosh)] + sum((["-i", str(pop)] for _ in DAYS[days][0]), [])
    n = 3 + len(DAYS[days][0])  # index of music
    f = [
        f"[0:v]{vf_top},fps=30[a0]", f"[1:v]{vf_top},fps=30[a1]",
        "[a0][a1]concat=n=2:v=1:a=0,trim=0:%s,setpts=PTS-STARTPTS[atb]" % DUR,
        f"color=black:s={W}x{H}:d={DUR}:r=30[bg]",
        "[bg][atb]overlay=0:0[v0]", f"[v0][2:v]overlay=0:{TOP}:shortest=1[v1]",
    ]
    last = "v1"
    for i, t in enumerate(FACT_T):
        f.append(f"[{last}][{3 + i}:v]overlay=0:{TOP}:enable='gte(t,{t})'[v{i + 2}]")
        last = f"v{i + 2}"
    f.append(f"[{last}]fade=t=out:st={DUR - 0.4}:d=0.4,format=yuv420p[vout]")
    # audio: music low, whoosh at start, a pop for each fact
    a = [f"[{n}:a]atrim=0:{DUR},volume=0.35,afade=t=out:st={DUR - 1}:d=1[m]", f"[{n + 1}:a]volume=0.8[w]"]
    mix = ["[m]", "[w]"]
    for i, t in enumerate(FACT_T):
        a.append(f"[{n + 2 + i}:a]adelay={int(t * 1000)}|{int(t * 1000)},volume=0.9[p{i}]")
        mix.append(f"[p{i}]")
    a.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0,atrim=0:{DUR}[aout]")
    mp4 = OUT / f"countdown_{days}.mp4"
    cmd = ["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(f + a),
           "-map", "[vout]", "-map", "[aout]", "-t", str(DUR), "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(mp4)]
    subprocess.run(cmd, check=True)
    # cover = full card with all facts (never black)
    cover = OUT / f"countdown_{days}_cover.jpg"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(FACT_T[-1] + 1), "-i", str(mp4),
                    "-frames:v", "1", "-q:v", "2", str(cover)], check=True)
    assert Image.open(cover).convert("L").getextrema()[1] > 60, "cover is black"
    print(mp4, cover)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
