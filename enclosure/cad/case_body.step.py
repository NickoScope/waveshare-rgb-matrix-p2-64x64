# -*- coding: utf-8 -*-
"""
Корпус корпуса C: лицевая плита с окном и борта по периметру.

Снимается ЗАДНЯЯ крышка, а не эта деталь. Так обслуживание не трогает ни
фаску, ни светоизоляцию, ни посадку матриц к лицевой плоскости — то есть
всё то, от чего зависит внешний вид.

  - плита CASE_W x CASE_H x WALL_FRONT с окном под фаску по углу обзора;
  - борта по периметру, назад до глубины корпуса;
  - канавка под светоизолирующий шнур вокруг окна;
  - двенадцать бобышек под втулки M3: за них притягивается крышка;
  - посадка энкодера: отверстие втулки и две стойки его платы.

Z от лица назад: лицевая поверхность в Z = 0.
"""

import os
import sys
from math import radians, tan

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import Box, Cylinder, Plane, Pos, Rectangle, export_stl, loft

from case_c_lib import (BEVEL_RUN, CASE_H, CASE_W, COVER_BOSS_D, COVER_GAP,
                        COVER_LIP, DEPTH, ENC_BODY_T, ENC_BODY_W, ENC_HOLE_D,
                        ENC_X, ENC_Y, FIELD_CY, FIELD_H, FIELD_W, INSERT_M25_D,
                        INSERT_M25_L, INSERT_M3_D, INSERT_M3_L, OVERLAP,
                        VIEW_ANGLE, WALL_BACK, WALL_FRONT, WALL_SIDE,
                        cover_points)

W, H = float(CASE_W), float(CASE_H)
T, TS, TB = float(WALL_FRONT), float(WALL_SIDE), float(WALL_BACK)
D = float(DEPTH)
CY = float(FIELD_CY)
AP_W = float(FIELD_W) - 2 * float(OVERLAP)
AP_H = float(FIELD_H) - 2 * float(OVERLAP)
SLOPE = tan(radians(float(VIEW_ANGLE)))
OVER = 0.5
SEAL_W, SEAL_D = 1.6, 0.6

Z_LIP = D - TB - float(COVER_LIP)        # где кончается полка под крышку
STAND_D = 6.0


def _window():
    def rect_at(z):
        grow = 2 * (T - z) * SLOPE
        return Plane.XY.offset(z) * Rectangle(AP_W + grow, AP_H + grow)
    return loft([rect_at(-OVER), rect_at(T + OVER)])


def build():
    # плита с бортами
    part = Pos(0, -CY, D / 2) * Box(W, H, D)
    part -= Pos(0, -CY, (T + D) / 2 + 0.001) * Box(W - 2 * TS, H - 2 * TS, D - T)

    # четверть под крышку: она садится заподлицо с задней кромкой бортов
    part -= Pos(0, -CY, (Z_LIP + D) / 2) * Box(
        W - 2 * TS + 2 * (TS - float(COVER_LIP)) - 2 * float(COVER_GAP),
        H - 2 * TS + 2 * (TS - float(COVER_LIP)) - 2 * float(COVER_GAP),
        D - Z_LIP)

    part -= _window()

    groove = (Pos(0, 0, T - SEAL_D / 2) * Box(AP_W + 2 * SEAL_W, AP_H + 2 * SEAL_W, SEAL_D)
              - Pos(0, 0, T - SEAL_D / 2) * Box(AP_W, AP_H, SEAL_D))
    part -= groove

    # бобышки под втулки M3: растут от тыльной стороны плиты до полки крышки
    L = Z_LIP - T
    for x, y in cover_points():
        part += Pos(x, y, T + L / 2) * Cylinder(float(COVER_BOSS_D) / 2, L)
    for x, y in cover_points():
        part -= Pos(x, y, Z_LIP - float(INSERT_M3_L) / 2) * Cylinder(
            float(INSERT_M3_D) / 2, float(INSERT_M3_L) + 0.1)

    # энкодер: отверстие втулки и стойки его платы
    part -= Pos(float(ENC_X), float(ENC_Y), T / 2) * Cylinder(
        float(ENC_HOLE_D) / 2, 3 * T)
    z_board = T + float(ENC_BODY_T)
    for sx in (-1, 1):
        x = float(ENC_X) + sx * (float(ENC_BODY_W) / 2 + 4.0)
        part += Pos(x, float(ENC_Y), (T + z_board) / 2) * Cylinder(
            STAND_D / 2, z_board - T)
        part -= Pos(x, float(ENC_Y), z_board - float(INSERT_M25_L) / 2) * Cylinder(
            float(INSERT_M25_D) / 2, float(INSERT_M25_L) + 0.1)

    part.label = "case_body"
    return part


part = build()


if __name__ == "__main__":
    bb = part.bounding_box()
    print(f"габарит: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}")
    print(f"объём: {part.volume / 1000:.1f} см3, тел: {len(part.solids())}")
    print(f"полка под крышку с Z = {Z_LIP:.2f}, точек притяжки {len(cover_points())}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    export_stl(part, os.path.join(out, "case_body.stl"))
    print("stl записан")
