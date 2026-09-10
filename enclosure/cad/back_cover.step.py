# -*- coding: utf-8 -*-
"""
Задняя крышка корпуса C — съёмная деталь.

Она же монтажная пластина (ТЗ §5 предпочитает именно этот вариант) и она же
несёт матрицы: все шесть точек M3 лежат внутри контура матрицы, добраться до
них можно только сзади, и стойка с лицевой стороны сквозь матрицу не пройдёт.
Поэтому крышка вынимается вместе с блоком матриц, а прижим матриц к лицевой
плите даёт затяжка крышки по периметру — через светоизолирующий шнур, он же
выбирает допуск по длине стоек.

  - плита, садится в четверть бортов корпуса заподлицо;
  - 12 отверстий с зенковкой: головки заподлицо, панель висит на стене;
  - 12 стоек под матрицы по сетке M3 из заводского чертежа;
  - площадка контроллера на четырёх стойках;
  - прилив под колодки во всю ширину;
  - кабельный ввод снизу.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import Box, Cylinder, Pos, export_stl

from case_c_lib import (CASE_H, CASE_W, CLAMP_PRELOAD, CLAMP_T, CLAMP_TOOTH,
                        CLAMP_W, COVER_GAP, COVER_HEAD_D, COVER_HEAD_H,
                        PANEL_BOARD, clamp_positions, seat_bounds,
                        COVER_LIP, COVER_SCREW_D, CTRL_H, CTRL_T, CTRL_W,
                        DEPTH, FIELD_CY, INSERT_M25_D, INSERT_M25_L, M3_POINTS,
                        PANEL_FRAME, PANEL_T, RELIEF_BAND_H, RELIEF_BAND_Y,
                        WALL_BACK, WALL_FRONT, WALL_SIDE, cover_points,
                        relief_depth)

W, H, D = float(CASE_W), float(CASE_H), float(DEPTH)
TB, TS, TF = float(WALL_BACK), float(WALL_SIDE), float(WALL_FRONT)
CY = float(FIELD_CY)
PT, PF = float(PANEL_T), float(PANEL_FRAME)

Z_LIP = D - TB - float(COVER_LIP)       # передняя поверхность крышки
Z_PANEL_BACK = TF + PT                  # задняя плоскость матрицы

PLATE_W = W - 2 * TS + 2 * (TS - float(COVER_LIP)) - 2 * float(COVER_GAP)
PLATE_H = H - 2 * TS + 2 * (TS - float(COVER_LIP)) - 2 * float(COVER_GAP)

BOSS_D, BOSS_HOLE = 7.0, 3.4
STANDOFF_D = 6.0
CTRL_CX, CTRL_CY = 60.0, -50.0
CABLE_W, CABLE_H = 22.0, 8.0
PANEL_CX = [-PF / 2, PF / 2]


def _relief():
    dz = relief_depth()
    if dz <= 0:
        return None, None
    y0, hh = float(RELIEF_BAND_Y), float(RELIEF_BAND_H)
    outer = Pos(0, y0, D + dz / 2) * Box(PLATE_W, hh, dz)
    z_end = D + dz - TB
    inner = Pos(0, y0, (Z_LIP + z_end) / 2) * Box(
        PLATE_W - 2 * TS, hh - 2 * TS, z_end - Z_LIP)
    return outer, inner


def _clamps():
    """Прижимные языки: гонят матрицы к центру, с четырёх сторон.

    Зуб стоит там, где торец матрицы окажется в САМОМ дальнем от края случае
    (узкий кандидат, 127.8), плюс натяг. При широком кандидате язык отжимается
    сильнее — на то он и пружина. Так стык закрыт при любом исходе обмера.
    """
    x0, x1, y0, y1 = seat_bounds()
    big = float(PANEL_BOARD)
    narrow_x = 2 * min(float(PANEL_BOARD), float(PANEL_FRAME)) / 2
    narrow_y = min(float(PANEL_BOARD), float(PANEL_FRAME)) / 2
    t, w = float(CLAMP_T), float(CLAMP_W)
    tooth, pre = float(CLAMP_TOOTH), float(CLAMP_PRELOAD)
    z0, z1 = TF + 1.0, Z_PANEL_BACK - 1.0        # зуб работает по торцу матрицы
    L = Z_LIP - z0
    out = []

    def leg(cx, cy, horizontal, sign):
        """Ножка от крышки вперёд плюс зуб, выступающий к центру."""
        if horizontal:
            body = Pos(cx + sign * (t / 2), cy, z0 + L / 2) * Box(t, w, L)
            face = narrow_x - pre                 # куда достаёт зуб
            depth = abs(cx) - face
            th = Pos(cx - sign * depth / 2, cy, (z0 + z1) / 2) * Box(
                depth, w, z1 - z0)
        else:
            body = Pos(cx, cy + sign * (t / 2), z0 + L / 2) * Box(w, t, L)
            face = narrow_y - pre
            depth = abs(cy) - face
            th = Pos(cx, cy - sign * depth / 2, (z0 + z1) / 2) * Box(
                w, depth, z1 - z0)
        return [body, th]

    for cx, cy, horizontal, sign in clamp_positions():
        out += leg(cx, cy, horizontal, sign)
    return out


def build():
    part = Pos(0, -CY, (Z_LIP + D) / 2) * Box(PLATE_W, PLATE_H, D - Z_LIP)

    for piece in _clamps():
        part += piece

    relief_out, relief_in = _relief()
    if relief_out is not None:
        part += relief_out
        part -= relief_in

    # стойки матриц: от крышки вперёд, до задней плоскости матрицы
    L = Z_LIP - Z_PANEL_BACK
    for cx in PANEL_CX:
        for mx, my in M3_POINTS:
            part += Pos(cx + mx, my, Z_PANEL_BACK + L / 2) * Cylinder(BOSS_D / 2, L)
    for cx in PANEL_CX:
        for mx, my in M3_POINTS:
            part -= Pos(cx + mx, my, D / 2) * Cylinder(BOSS_HOLE / 2, 3 * D)

    # контроллер
    lc = Z_LIP - (Z_PANEL_BACK + 1.0)
    dx, dy = float(CTRL_W) / 2 - 3.0, float(CTRL_H) / 2 - 3.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = CTRL_CX + sx * dx, CTRL_CY + sy * dy
            part += Pos(x, y, Z_LIP - lc / 2) * Cylinder(STANDOFF_D / 2, lc)
            part -= Pos(x, y, Z_LIP - float(INSERT_M25_L) / 2) * Cylinder(
                float(INSERT_M25_D) / 2, float(INSERT_M25_L) + 0.1)

    # притяжка к корпусу: проход винта и зенковка под головку
    for x, y in cover_points():
        part -= Pos(x, y, D / 2) * Cylinder(float(COVER_SCREW_D) / 2, 3 * D)
        part -= Pos(x, y, D - float(COVER_HEAD_H) / 2) * Cylinder(
            float(COVER_HEAD_D) / 2, float(COVER_HEAD_H) + 0.01)

    # кабельный ввод снизу
    y_bottom = -CY - PLATE_H / 2
    part -= Pos(CTRL_CX, y_bottom + TS / 2, D - CABLE_H / 2) * Box(
        CABLE_W, 3 * TS, CABLE_H)

    part.label = "back_cover"
    return part


part = build()


if __name__ == "__main__":
    bb = part.bounding_box()
    print(f"габарит: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}")
    print(f"объём: {part.volume / 1000:.1f} см3, тел: {len(part.solids())}")
    print(f"стоек матриц: {2 * len(M3_POINTS)}, точек притяжки: {len(cover_points())}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    export_stl(part, os.path.join(out, "back_cover.stl"))
    print("stl записан")
