# -*- coding: utf-8 -*-
"""
Задняя часть корпуса C, цельная (до членения на печатные детали).

Она несёт всё: матрицы прикручены к её бобышкам, на ней стоит контроллер,
в ней проходят кабели, к ней крепится настенный подвес. Лицевая рамка
только закрывает и держит светоизоляцию.

  - задняя плита и борта по периметру;
  - 12 бобышек под M3 матриц (6 на матрицу, сетка из заводского чертежа);
  - площадка контроллера на четырёх стойках под втулки M2.5;
  - карманы под колодки HUB75 и VH4, чтобы кабель загибался сразу у колодки;
  - вырез кабельного ввода снизу и окно USB-C;
  - площадка энкодера в полосе.

Z от лица назад: матрица занимает WALL_FRONT..WALL_FRONT+PANEL_T,
задняя плита — DEPTH-WALL_BACK..DEPTH.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import Box, Cylinder, Pos, export_stl

from case_c_lib import (FIELD_CY as _FCY,
                        CASE_H, CASE_W, CONN_H, CTRL_H, CTRL_T, CTRL_W, DEPTH,
                        ENC_BODY_T, ENC_BODY_W, ENC_X, ENC_Y, FIELD_H, FIELD_W,
                        INSERT_M25_D, INSERT_M25_L, M3_POINTS, PANEL_FRAME,
                        PANEL_T, RELIEF_BAND_H, RELIEF_BAND_Y, STRIP_H,
                        WALL_BACK, WALL_FRONT, WALL_SIDE, relief_depth)

W, H, D = float(CASE_W), float(CASE_H), float(DEPTH)
TB, TS, TF = float(WALL_BACK), float(WALL_SIDE), float(WALL_FRONT)
PT = float(PANEL_T)

Z_PANEL_BACK = TF + PT                 # задняя плоскость матрицы
Z_PLATE = D - TB                       # передняя поверхность задней плиты

BOSS_D = 7.0                           # бобышка под винт M3
BOSS_HOLE = 3.4
PANEL_CX = [-float(PANEL_FRAME) / 2, float(PANEL_FRAME) / 2]

# Площадка контроллера. Ниже полосы прилива, чтобы её стойки не оказались
# срезанными вырезом прилива, и левее энкодера, чтобы стойки не сошлись.
CTRL_CX, CTRL_CY = 60.0, -50.0
STANDOFF_D = 6.0
CABLE_W, CABLE_H = 22.0, 8.0           # кабельный ввод снизу


def _shell():
    outer = Pos(0, -float(_FCY), (TF + D) / 2) * Box(W, H, D - TF)
    inner = Pos(0, -float(_FCY), (TF + Z_PLATE) / 2) * Box(
        W - 2 * TS, H - 2 * TS, Z_PLATE - TF)
    return outer - inner


def _panel_bosses():
    """Бобышки упираются в заднюю плоскость матрицы, винт идёт сзади."""
    out = []
    L = Z_PLATE - Z_PANEL_BACK
    for cx in PANEL_CX:
        for mx, my in M3_POINTS:
            p = Pos(cx + mx, my, Z_PANEL_BACK + L / 2)
            out.append(p * Cylinder(BOSS_D / 2, L))
    return out


def _panel_boss_holes():
    out = []
    for cx in PANEL_CX:
        for mx, my in M3_POINTS:
            out.append(Pos(cx + mx, my, D / 2) * Cylinder(BOSS_HOLE / 2, 2 * D))
    return out


def _controller():
    """Четыре стойки под втулки M2.5 и место под плату."""
    posts, holes = [], []
    L = Z_PLATE - (Z_PANEL_BACK + 1.0)     # стойка не касается матрицы
    dx, dy = float(CTRL_W) / 2 - 3.0, float(CTRL_H) / 2 - 3.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = CTRL_CX + sx * dx, CTRL_CY + sy * dy
            posts.append(Pos(x, y, Z_PLATE - L / 2) * Cylinder(STANDOFF_D / 2, L))
            holes.append(Pos(x, y, Z_PLATE - float(INSERT_M25_L) / 2)
                         * Cylinder(float(INSERT_M25_D) / 2, float(INSERT_M25_L) + 0.1))
    return posts, holes


def _encoder_pad():
    """Стойки под плату энкодера.

    Плата стоит параллельно лицевой стенке, за телом энкодера, поэтому стойки
    растут от задней плиты вперёд и кончаются там, где ложится плата.
    Высота тела энкодера — параметр на обмере: длина стоек от неё и зависит.
    """
    posts, holes = [], []
    z_board = TF + float(ENC_BODY_T)          # передняя поверхность платы
    L = Z_PLATE - z_board
    for sx in (-1, 1):
        x = float(ENC_X) + sx * (float(ENC_BODY_W) / 2 + 4.0)
        posts.append(Pos(x, float(ENC_Y), z_board + L / 2) * Cylinder(STANDOFF_D / 2, L))
        holes.append(Pos(x, float(ENC_Y), z_board + float(INSERT_M25_L) / 2)
                     * Cylinder(float(INSERT_M25_D) / 2, float(INSERT_M25_L) + 0.1))
    return posts, holes


def _relief():
    """Прилив под колодки: полоса по всей ширине, выдавленная назад.

    Глубина считается из размера колодки С НАДЕТЫМ разъёмом, а не из высоты
    самой колодки: розетка охватывает вилку сверху, и габарит определяет она.
    """
    dz = relief_depth()
    if dz <= 0:
        return None, None
    y0, hh = float(RELIEF_BAND_Y), float(RELIEF_BAND_H)
    # наружная коробка прилива: от старой задней плоскости назад на dz
    outer = Pos(0, y0, D + dz / 2) * Box(W - 2 * TS, hh, dz)
    # Полость под приливом: вскрывает старую заднюю плиту и уходит в прилив,
    # но останавливается на толщину задней стенки — иначе прилив вышел бы
    # сквозным окном, а не карманом.
    z_end = D + dz - TB
    inner = Pos(0, y0, (Z_PLATE + z_end) / 2) * Box(
        W - 4 * TS, hh - 2 * TS, z_end - Z_PLATE)
    return outer, inner


def build():
    part = _shell()

    relief_out, relief_in = _relief()
    if relief_out is not None:
        part += relief_out
        part -= relief_in

    for b in _panel_bosses():
        part += b
    posts, holes = _controller()
    for p in posts:
        part += p
    ep, eh = _encoder_pad()
    for p in ep:
        part += p

    for h in _panel_boss_holes() + holes + eh:
        part -= h

    # кабельный ввод снизу, в зоне полосы
    y_bottom = -float(_FCY) - H / 2
    part -= Pos(CTRL_CX, y_bottom + TS / 2, D - TB - CABLE_H / 2) * Box(
        CABLE_W, 3 * TS, CABLE_H)

    part.label = "back_shell"
    return part


part = build()


if __name__ == "__main__":
    bb = part.bounding_box()
    print(f"габарит: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}")
    print(f"объём: {part.volume / 1000:.1f} см3, тел: {len(part.solids())}")
    print(f"полость за матрицей: {Z_PLATE - Z_PANEL_BACK:.2f} "
          f"(колодка {float(CONN_H):.1f}, плата {float(CTRL_T):.1f})")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    export_stl(part, os.path.join(out, "back_shell.stl"))
    print("stl записан")
