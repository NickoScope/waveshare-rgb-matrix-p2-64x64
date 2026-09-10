# -*- coding: utf-8 -*-
"""
Полный вертикальный разрез сборки — отдельным листом, с выносками.

Панель 169 мм высотой против 37 мм глубины: на общем листе такой разрез
превращается в полоску, поэтому он живёт отдельно и во весь размер.

    python full_section.py
"""

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
INK, MUTE, ACC = (22, 33, 44), (92, 108, 122), (47, 107, 138)


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.load_default()


def main():
    subprocess.run([sys.executable, os.path.join(HERE, "sections.step.py")],
                   check=True, cwd=HERE)
    shell = trimesh.load(os.path.join(OUT, "sect_F_full_shell.stl"))
    mock = trimesh.load(os.path.join(OUT, "sect_F_full_mock.stl"))

    img = render([(shell, (186, 202, 214)), (mock, (92, 108, 124))],
                 elev=0.0, azim=90.0, size=(560, 1420), pad=0.04)

    W, H = 1000, 1530
    sheet = Image.new("RGB", (W, H), (251, 252, 253))
    d = ImageDraw.Draw(sheet)
    d.text((26, 20), "Корпус C — полный разрез по вертикали", font=font(30), fill=INK)
    d.text((26, 56), "Плоскость через контроллер. Светлое — корпус и крышка, "
                     "тёмное — покупное железо.", font=font(16), fill=MUTE)
    sheet.paste(img, (10, 96))

    rows = [
        ("сверху вниз по разрезу", None),
        ("борт корпуса, лицевая плита %.1f" % float(L.WALL_FRONT), INK),
        ("фаска %.0f°, раскрытие %.2f на сторону" % (float(L.BEVEL_ANGLE),
                                                     float(L.BEVEL_RUN)), INK),
        ("ребро гнезда: %.1f вглубь, %.1f толщиной"
         % (float(L.SEAT_RIB_H), float(L.SEAT_RIB_W)), INK),
        ("матрица %.1f — единый модуль" % float(L.PANEL_T), ACC),
        ("полость за матрицей %.1f" % float(L.CAVITY_BEHIND), INK),
        ("прилив под колодки: +%.1f" % L.relief_depth(), INK),
        ("контроллер %g × %g, высота %.1f"
         % (float(L.CTRL_W), float(L.CTRL_H), float(L.CTRL_T)), ACC),
        ("крышка %.1f, винт заподлицо" % float(L.WALL_BACK), INK),
        ("", None),
        ("свободная полоса %.1f" % float(L.STRIP_FREE), INK),
        ("энкодер по её середине, вал наружу", ACC),
        ("глубина по кромке %.0f, в приливе %.0f"
         % (float(L.DEPTH), float(L.DEPTH) + L.relief_depth()), INK),
    ]
    y = 120
    for text, col in rows:
        if not text:
            y += 12
            continue
        if col is None:
            d.text((600, y), text, font=font(19), fill=INK)
            y += 34
            continue
        d.ellipse([600, y + 6, 608, y + 14], fill=col)
        d.text((620, y), text, font=font(16), fill=col)
        y += 30

    f = os.path.join(OUT, "M1_polnyj_razrez.png")
    sheet.save(f)
    print("записан", f, sheet.size)


if __name__ == "__main__":
    main()
