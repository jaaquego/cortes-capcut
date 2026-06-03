# -*- coding: utf-8 -*-
"""Gera um icone (.ico) bonito pro atalho: quadrado arredondado com gradiente,
furos de filme nas laterais, um play branco e uma tesourinha (corte)."""
import math
from PIL import Image, ImageDraw

S = 512  # desenha grande e reamostra (bordas suaves)
SS = 4   # supersampling
W = S * SS

img = Image.new("RGBA", (W, W), (0, 0, 0, 0))

# --- fundo com gradiente diagonal (teal -> azul) ---
top = (22, 205, 195)
bot = (45, 108, 230)
grad = Image.new("RGB", (W, W))
gd = grad.load()
for y in range(W):
    for x in range(0, W, 1):
        t = (x / W * 0.35 + y / W * 0.65)
        gd[x, y] = (
            int(top[0] * (1 - t) + bot[0] * t),
            int(top[1] * (1 - t) + bot[1] * t),
            int(top[2] * (1 - t) + bot[2] * t),
        )

mask = Image.new("L", (W, W), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, W - 1], radius=int(W * 0.22), fill=255)
img.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(img)

# --- brilho sutil no topo ---
gloss = Image.new("L", (W, W), 0)
ImageDraw.Draw(gloss).rounded_rectangle([0, 0, W - 1, int(W * 0.5)], radius=int(W * 0.22), fill=40)
img.paste(Image.new("RGB", (W, W), (255, 255, 255)), (0, 0),
          Image.composite(gloss, Image.new("L", (W, W), 0), mask))

# --- furos de filme nas laterais ---
hole_w, hole_h = int(W * 0.045), int(W * 0.07)
for side_x in (int(W * 0.085), int(W * 0.87)):
    for i in range(4):
        y0 = int(W * 0.16) + i * int(W * 0.18)
        d.rounded_rectangle([side_x, y0, side_x + hole_w, y0 + hole_h],
                            radius=int(hole_w * 0.35), fill=(255, 255, 255, 235))

# --- play branco no centro ---
cx, cy = W * 0.52, W * 0.46
r = W * 0.17
tri = [(cx - r * 0.62, cy - r * 0.82),
       (cx - r * 0.62, cy + r * 0.82),
       (cx + r * 0.92, cy)]
d.polygon(tri, fill=(255, 255, 255, 245))

# --- tesourinha (corte) embaixo, branca ---
sx, sy = W * 0.5, W * 0.78
bl = W * 0.085
# dois aneis
ring = int(W * 0.035)
d.ellipse([sx - bl - ring, sy + bl - ring, sx - bl + ring, sy + bl + ring], outline=(255, 255, 255, 240), width=int(W * 0.013))
d.ellipse([sx + bl - ring, sy + bl - ring, sx + bl + ring, sy + bl + ring], outline=(255, 255, 255, 240), width=int(W * 0.013))
# duas laminas cruzando
lw = int(W * 0.016)
d.line([sx - bl, sy + bl, sx + bl * 0.9, sy - bl * 1.1], fill=(255, 255, 255, 245), width=lw)
d.line([sx + bl, sy + bl, sx - bl * 0.9, sy - bl * 1.1], fill=(255, 255, 255, 245), width=lw)

# reamostra pra suavizar
img = img.resize((S, S), Image.LANCZOS)
img.save("icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save("icon_preview.png")
print("ok")
