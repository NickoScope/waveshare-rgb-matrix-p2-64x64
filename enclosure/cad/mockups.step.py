# -*- coding: utf-8 -*-
"""
Макеты покупного железа: матрицы, плата контроллера, энкодер, колодки.

Это НЕ печатные детали. Они существуют только чтобы проверять зазоры и
смотреть на сборку. Все их размеры со статусом ОБМЕР в case_c_lib —
макет ровно настолько правдив, насколько правдив обмер.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import Box, Compound, Cylinder, Pos, export_stl

from case_c_lib import (CONN_H, CTRL_H, CTRL_T, CTRL_W, ENC_BODY_H, ENC_BODY_T,
                        PANEL_BOARD,
                        ENC_BODY_W, ENC_BUSH_D, ENC_X, ENC_Y, PANEL_FRAME,
                        PANEL_T, WALL_FRONT)

TF, PT = float(WALL_FRONT), float(PANEL_T)
PF = float(PANEL_FRAME)
PB = float(PANEL_BOARD)
CTRL_CX, CTRL_CY = 60.0, -50.0          # согласовано с back_shell
Z_PANEL_BACK = TF + PT


def build():
    items = []
    # Панель БЕЗ монтажной рамки: наружный размер берём по кромке платы,
    # рамка — принадлежность, и мы её не ставим.
    for sx in (-1, 1):
        m = Pos(sx * PB / 2, 0, TF + PT / 2) * Box(PB, PB, PT)
        m.label = f"panel_{'L' if sx < 0 else 'R'}"
        items.append(m)

    # Колодки HUB75. Чертёж не размеряет ни их посадочные места, ни высоту,
    # поэтому положение здесь ВЫДУМАНО: по центру каждой матрицы, на осевой.
    # Оно влияет только на картинку; глубину корпуса задаёт CONN_STACK, а
    # ширину прилива — то, что положение неизвестно (полоса во всю ширину).
    for x in (-PB / 2, PB / 2):
        c = Pos(x, 0, Z_PANEL_BACK + float(CONN_H) / 2) * Box(42.0, 12.0, float(CONN_H))
        c.label = "hub75"
        items.append(c)

    b = Pos(CTRL_CX, CTRL_CY, Z_PANEL_BACK + 1.0 + float(CTRL_T) / 2) * Box(
        float(CTRL_W), float(CTRL_H), float(CTRL_T))
    b.label = "controller"
    items.append(b)

    e = Pos(float(ENC_X), float(ENC_Y), TF + float(ENC_BODY_T) / 2) * Box(
        float(ENC_BODY_W), float(ENC_BODY_H), float(ENC_BODY_T))
    e.label = "encoder_body"
    items.append(e)
    sh = Pos(float(ENC_X), float(ENC_Y), -4.0) * Cylinder(float(ENC_BUSH_D) / 2, 14.0)
    sh.label = "encoder_shaft"
    items.append(sh)

    part = Compound(children=items)
    part.label = "mockups"
    return part


part = build()


if __name__ == "__main__":
    bb = part.bounding_box()
    print(f"габарит макетов: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}")
    print(f"тел: {len(part.solids())}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    export_stl(part, os.path.join(out, "mockups.stl"))
    print("stl записан")
