"""ATB Plays logo v2: ATB character face (calm frame from FMM's atb_22_calm_explain.mp4), big, no text,
Miami sunset bg, neon ring. Run: E:/Claude/FMM/.venv312/Scripts/python.exe brand/make_logo.py (reads FMM files only)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from rembg import remove, new_session

HERE = Path(__file__).parent
S = 1024


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


cut = HERE / "atb_char_cutout.png"
if not cut.exists():
    remove(Image.open(HERE / "atb_char_frame.png"), session=new_session("isnet-general-use")).save(cut)
person = Image.open(cut).convert("RGBA")
person = ImageEnhance.Brightness(person).enhance(1.12)  # ATB rule: a bit brighter, never darker
person = person.crop(person.getbbox())
# head + neck only (hides the FMM jersey logo): top 62% of the cut-out height
person = person.crop((0, 0, person.width, int(person.height * 0.70)))

bg = grad(S, S, [(0, (40, 10, 80)), (0.45, (190, 40, 140)), (0.75, (255, 120, 70)), (1, (255, 190, 80))]).convert("RGBA")
sun = grad(640, 640, [(0, (255, 230, 90)), (1, (255, 60, 140))]).convert("RGBA")
mask = Image.new("L", (640, 640), 0)
md = ImageDraw.Draw(mask)
md.ellipse((0, 0, 639, 639), fill=255)
for i, y in enumerate(range(340, 640, 46)):
    md.rectangle((0, y, 640, y + 8 + i * 3), fill=0)
bg.paste(sun, (192, 80), mask)

ph = 800  # big face
person = person.resize((int(person.width * ph / person.height), ph), Image.LANCZOS)
glow = Image.new("RGBA", person.size, (0, 255, 230, 0))
glow.putalpha(person.getchannel("A").filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(5)))
# centre on the head (top 35% of the cut-out), not on the shoulders
a = person.getchannel("A").crop((0, 0, person.width, int(ph * 0.35)))
hx0, _, hx1, _ = a.getbbox()
px, py = S // 2 - (hx0 + hx1) // 2, S - ph
bg.alpha_composite(glow, (px, py))
bg.alpha_composite(person, (px, py))

# circle crop + neon ring (pink outer glow, cyan inner line)
out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
m = Image.new("L", (S, S), 0)
ImageDraw.Draw(m).ellipse((0, 0, S - 1, S - 1), fill=255)
out.paste(bg, (0, 0), m)
def neon(box, color, width, blur):
    r = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(r).ellipse(box, outline=color, width=width)
    g = r.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(g)
    out.alpha_composite(g)  # twice = stronger glow
    core = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(core).ellipse(box, outline=(255, 255, 255, 255), width=max(3, width // 3))
    out.alpha_composite(r)
    out.alpha_composite(core)  # white-hot centre line, like a real neon tube


out.alpha_composite(Image.new("RGBA", (S, S), (0, 0, 0, 0)))
neon((20, 20, S - 21, S - 21), (255, 30, 180, 255), 22, 14)   # hot pink outer tube
neon((62, 62, S - 63, S - 63), (0, 235, 255, 255), 12, 10)    # cyan inner tube
# keep glow inside the circle
final = Image.new("RGBA", (S, S), (0, 0, 0, 0))
final.paste(out, (0, 0), m)
out = final
out.save(HERE / "logo_atb_plays.png")
flat = Image.new("RGB", (S, S), (255, 255, 255))
flat.paste(out, (0, 0), out)
flat.resize((400, 400), Image.LANCZOS).save(HERE / "logo_preview_circle.png")
print("ok")
