"""Render assets/selftest.txt jadi PNG gaya terminal Termux (output asli)."""
from PIL import Image, ImageDraw, ImageFont

SRC = "assets/selftest.txt"
OUT = "assets/preview-terminal.png"

lines = []
for ln in open(SRC, encoding="utf-8").read().splitlines():
    if not ln.strip():
        continue
    if ln.strip().startswith("waiting"):
        continue                      # baris countdown (\r) tidak informatif
    lines.append(ln)

FONT = "/c/Windows/Fonts/consola.ttf"
fs = 15
f = ImageFont.truetype(FONT, fs)
lh = 22
pad = 28
W = 1100

# hitung tinggi
tmp = Image.new("RGB", (10, 10))
d = ImageDraw.Draw(tmp)
widths = [d.textlength(ln, font=f) for ln in lines]
W = int(max(widths) + pad * 2)
H = lh * len(lines) + pad * 2 + 34

img = Image.new("RGB", (W, H), "#0d1117")
d = ImageDraw.Draw(img)

# judul jendela terminal
d.rectangle([0, 0, W, 30], fill="#161b22")
d.ellipse([14, 11, 22, 19], fill="#ff5f56")
d.ellipse([28, 11, 36, 19], fill="#ffbd2e")
d.ellipse([42, 11, 50, 19], fill="#27c93f")
d.text((62, 7), "Termux — keris", font=f, fill="#8b949e")

TAG = {                          # warna per tag
    "dns": "#79c0ff", "ntp": "#a5d6ff", "test": "#d2a8ff",
    "lane": "#7ee787", "measure": "#ffa657", "snipe": "#ff7b72",
    "fire": "#f0f6fc", "KERIS": "#58a6ff",
}
y = 44
for ln in lines:
    color = "#c9d1d9"
    if ln.startswith("=="):
        color = "#30363d"
    else:
        for tag, c in TAG.items():
            if ln.startswith(tag) and ln[len(tag):len(tag) + 1] in (" ", "") \
               and ln[:len(tag)].strip() == tag:
                color = c
                break
    d.text((pad, y), ln, font=f, fill=color)
    y += lh

img.save(OUT)
print(f"{OUT}  {img.size[0]}x{img.size[1]}  {len(lines)} baris")
