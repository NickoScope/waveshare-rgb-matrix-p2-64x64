# -*- coding: utf-8 -*-
"""
Лицевая рамка корпуса C, цельная (до членения на печатные детали).

  - плита CASE_W x CASE_H x WALL_FRONT;
  - окно с фаской, раскрывающейся НАРУЖУ под углом обзора матрицы, а не под
    минимальные 45° из ТЗ: под 45° кромка затенила бы крайний пиксель;
  - канавка под светоизолирующий шнур по периметру окна, со стороны матрицы;
  - отверстие под втулку энкодера справа в полосе.

Z направлена от лица назад: лицевая поверхность в Z = 0, матрица встаёт
за плитой, в Z от WALL_FRONT и глубже. Держит матрицу задняя часть, не эта.
"""

import os
import sys
from math import radians, tan

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import Box, Cylinder, Plane, Pos, Rectangle, export_stl, loft

from case_c_lib import (FIELD_CY as _FCY,
                        BEVEL_RUN, CASE_H, CASE_W, ENC_HOLE_D, ENC_X, ENC_Y,
                        FIELD_H, FIELD_W, OVERLAP, STRIP_H, VIEW_ANGLE,
                        WALL_FRONT)

W, H, T = float(CASE_W), float(CASE_H), float(WALL_FRONT)
AP_W = float(FIELD_W) - 2 * float(OVERLAP)   # кромка окна у матрицы
AP_H = float(FIELD_H) - 2 * float(OVERLAP)
SLOPE = tan(radians(float(VIEW_ANGLE)))      # раскрытие на миллиметр толщины
OVER = 0.5                                   # запас на чистое вычитание

SEAL_W, SEAL_D = 1.6, 0.6                    # канавка светоизолирующего шнура


def _window():
    """Сквозное окно: узкое у матрицы (Z = T), широкое к лицу (Z = 0)."""
    def rect_at(z):
        grow = 2 * (T - z) * SLOPE
        return Plane.XY.offset(z) * Rectangle(AP_W + grow, AP_H + grow)

    return loft([rect_at(-OVER), rect_at(T + OVER)])


def build():
    part = Pos(0, -float(_FCY), T / 2) * Box(W, H, T)
    part -= _window()

    groove = (Pos(0, 0, T - SEAL_D / 2) * Box(AP_W + 2 * SEAL_W, AP_H + 2 * SEAL_W, SEAL_D)
              - Pos(0, 0, T - SEAL_D / 2) * Box(AP_W, AP_H, SEAL_D))
    part -= groove

    part -= Pos(float(ENC_X), float(ENC_Y), T / 2) * Cylinder(
        float(ENC_HOLE_D) / 2, 3 * T)

    part.label = "front_frame"
    return part


part = build()


if __name__ == "__main__":
    bb = part.bounding_box()
    print(f"габарит: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}")
    print(f"объём: {part.volume / 1000:.1f} см3, тел: {len(part.solids())}")
    print(f"окно у лица: {AP_W + 2 * T * SLOPE:.2f} x {AP_H + 2 * T * SLOPE:.2f}")
    print(f"окно у матрицы: {AP_W:.2f} x {AP_H:.2f}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    export_stl(part, os.path.join(out, "front_frame.stl"))
    print("stl записан")
