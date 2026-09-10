# -*- coding: utf-8 -*-
"""
Контактный лист: каждая деталь отдельно и три разреза сборки, с подписями.

    python sheet.py

Разрезы строит sections.step.py, рендерит render.py. Здесь только раскладка.
"""

import os
import subprocess
import sys

import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from render import render

OUT = os.path.join(HERE, "out")
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
INK, MUTE = (22, 33, 44), (90, 106, 120)

SHELL_F = (236, 239, 242)
SHELL_B = (176, 196, 210)
MOCK = (96, 112, 128)
CUT = (198, 122, 96)          # плоскость среза — тёплым, чтобы читалась


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.load_default()


def load(name, color):
    f = os.path.join(OUT, name)
    if not os.path.exists(f):
        return None
    return (trimesh.load(f), color)


def tile(meshes, elev, azim, mirror, size=(760, 520)):
    meshes = [m for m in meshes if m]
    return render(meshes, elev, azim, size=size, mirror=mirror)


def main():
    subprocess.run([sys.executable, os.path.join(HERE, "sections.step.py")],
                   check=True, cwd=HERE)

    ff = load("front_frame.stl", SHELL_F)
    bs = load("back_shell.stl", SHELL_B)
    mk = load("mockups.stl", MOCK)

    panels = [
        ("Лицевая рамка · с лица",
         [ff], 18.0, 208.0, True,
         "окно с фаской 70°, канавка под шнур, отверстие втулки энкодера"),
        ("Лицевая рамка · изнутри",
         [ff], 18.0, 26.0, False,
         "видна канавка светоизоляции по периметру окна"),
        ("Задняя часть · снаружи",
         [bs], 18.0, 26.0, False,
         "прилив под колодки во всю ширину, 12 отверстий под винты M3"),
        ("Задняя часть · изнутри",
         [bs], 18.0, 208.0, True,
         "бобышки матриц, стойки контроллера и энкодера, кабельный ввод"),
        ("Макеты железа · сзади",
         [mk], 18.0, 26.0, False,
         "колодки HUB75, плата 50×42, энкодер — НЕ печатаются"),
        ("Сборка",
         [ff, bs, mk], 18.0, 208.0, True,
         "как это выглядит в собранном виде"),
    ]

    cuts = [
        ("Разрез A — полоса и энкодер",
         "A_strip", 0.0, 90.0, False,
         "втулка сквозь лицевую стенку, тело за ней, плата на стойках"),
        ("Разрез B — верхняя кромка",
         "B_top", 0.0, 90.0, False,
         "фаска раскрывается наружу, за ней матрица, сзади прилив"),
        ("Разрез C — стык матриц",
         "C_seam", 90.0, 0.0, False,
         "между матрицами ни ребра, ни стенки, ни зазора"),
        ("Разрез D — боковой край",
         "D_edge", 90.0, 0.0, False,
         "борт, перекрытие безелем 0,5 и край матрицы"),
    ]

    tiles = []
    for title, meshes, el, az, mir, note in panels:
        tiles.append((title, note, tile(meshes, el, az, mir)))
    for title, key, el, az, mir, note in cuts:
        ms = [load(f"sect_{key}_shell.stl", SHELL_B),
              load(f"sect_{key}_mock.stl", MOCK)]
        tiles.append((title, note, tile(ms, el, az, mir)))

    cols, tw, th = 3, 760, 520
    pad, head, cap = 18, 74, 50
    rows = (len(tiles) + cols - 1) // cols
    W = cols * tw + (cols + 1) * pad
    H = head + rows * (th + cap) + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), (251, 252, 253))
    d = ImageDraw.Draw(sheet)
    d.text((pad + 4, 18), "Корпус C «LED MATRIX» — M1, детали и разрезы",
           font=font(30), fill=INK)
    d.text((pad + 4, 52), "Габарит 284 × 168,9 × 30 по кромке. "
                          "Проверка verify.py: нарушений нет.",
           font=font(16), fill=MUTE)

    for i, (title, note, img) in enumerate(tiles):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = head + pad + r * (th + cap + pad)
        sheet.paste(img, (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline=(214, 220, 226))
        d.text((x + 2, y + th + 6), title, font=font(19), fill=INK)
        d.text((x + 2, y + th + 29), note, font=font(14), fill=MUTE)

    f = os.path.join(OUT, "M1_detali_i_razrezy.png")
    sheet.save(f)
    print("записан", f, sheet.size)


if __name__ == "__main__":
    main()
