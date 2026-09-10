# -*- coding: utf-8 -*-
"""Лист членения: каждая печатная деталь и как она ложится на стол."""

import os
import subprocess
import sys

import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import case_c_lib as L
from render import render

OUT = os.path.join(HERE, "out")
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
INK, MUTE, OK, WARN = (22, 33, 44), (92, 108, 122), (47, 107, 58), (168, 53, 31)

PARTS = [
    ("body_top", "Планка верхняя", "шов лёг на верхнюю кромку поля"),
    ("body_bottom", "Планка нижняя", "шов на границе поля и полосы; здесь энкодер"),
    ("body_side_L", "Борт левый", "ложится плашмя"),
    ("body_side_R", "Борт правый", "ложится плашмя"),
    ("cover_L", "Крышка, часть левая", "шов мимо ребра стыка"),
    ("cover_R", "Крышка, часть правая", "здесь площадка контроллера"),
]


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.load_default()


def main():
    subprocess.run([sys.executable, os.path.join(HERE, "split.py")],
                   check=True, cwd=HERE)

    tiles = []
    for key, title, note in PARTS:
        f = os.path.join(OUT, f"split_{key}.stl")
        m = trimesh.load(f)
        img = render([(m, (186, 202, 214))], 20.0, 208.0, size=(720, 460),
                     mirror=True)
        b = m.bounds
        size = (b[1] - b[0])
        ok, how = L.fits_plate(size[0], size[1])
        tiles.append((title, note, img, size, how, ok))

    cols, tw, th = 3, 720, 460
    pad, head, cap = 18, 84, 62
    rows = (len(tiles) + cols - 1) // cols
    W = cols * tw + (cols + 1) * pad
    H = head + rows * (th + cap) + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), (251, 252, 253))
    d = ImageDraw.Draw(sheet)
    d.text((pad + 4, 20), "Корпус C — членение под печать", font=font(30), fill=INK)
    d.text((pad + 4, 56),
           f"Стол {float(L.PLATE):.0f} × {float(L.PLATE):.0f}; деталь ложится по "
           f"диагонали, если L + W ≤ {float(L.DIAG):.0f}. "
           "Швы лежат на границах изображения, поперёк поля не идёт ни один.",
           font=font(16), fill=MUTE)

    for i, (title, note, img, size, how, ok) in enumerate(tiles):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = head + pad + r * (th + cap + pad)
        sheet.paste(img, (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline=(214, 220, 226))
        d.text((x + 2, y + th + 6), title, font=font(20), fill=INK)
        d.text((x + 2, y + th + 30),
               f"{size[0]:.0f} × {size[1]:.0f} × {size[2]:.0f} — {how}",
               font=font(15), fill=OK if ok else WARN)
        d.text((x + 2, y + th + 48), note, font=font(14), fill=MUTE)

    f = os.path.join(OUT, "M2_chlenenie.png")
    sheet.save(f)
    print("записан", f, sheet.size)


if __name__ == "__main__":
    main()
