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

from build123d import (Box, Cylinder, Plane, Pos, Rectangle, Rotation,
                       export_stl, loft)

from case_c_lib import (BEVEL_RUN, CASE_H, CASE_W, COVER_BOSS_D, COVER_GAP,
                        CLAMP_T, CLAMP_W, JOINT_ARM, JOINT_BOSS,
                        JOINT_HEAD_D, JOINT_HEAD_H, JOINT_SCREW_D,
                        SEAT_RIB_H, SEAT_RIB_W, SPLIT_BOT, SPLIT_TOP,
                        corner_joints,
                        clamp_positions, seat_bounds,
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

    # Внутренняя граница канавки НАМЕРЕННО меньше кромки окна на SEAL_BITE.
    # Если сделать её ровно по кромке, две поверхности совпадут, и булева
    # операция оставит в теле грань нулевой толщины: объёма у неё нет, но
    # она тянется на всё окно, раздувает габарит отрезанной детали и уезжает
    # в STL. Лишнее вычитание попадает в пустоту окна и ничего не портит.
    # Канавка вычитается С ЗАПАСОМ в обе стороны: внутрь — за кромку окна,
    # назад — за тыльную поверхность плиты. Если её границы совпадут с уже
    # существующими поверхностями, булева операция оставит грани нулевой
    # толщины; объёма у них нет, но они уезжают в STL и раздувают габарит
    # отрезанных деталей. Запас уходит в пустоту и ничего не меняет.
    SEAL_BITE, SEAL_OVER = 1.0, 0.5
    outer = Box(AP_W + 2 * SEAL_W, AP_H + 2 * SEAL_W, SEAL_D + SEAL_OVER)
    inner = Box(AP_W - 2 * SEAL_BITE, AP_H - 2 * SEAL_BITE, SEAL_D + SEAL_OVER)
    zc = T - SEAL_D / 2 + SEAL_OVER / 2
    part -= (Pos(0, 0, zc) * outer - Pos(0, 0, zc) * inner)

    # бобышки под втулки M3: растут от тыльной стороны плиты до полки крышки
    L = Z_LIP - T
    for x, y in cover_points():
        part += Pos(x, y, T + L / 2) * Cylinder(float(COVER_BOSS_D) / 2, L)
    for x, y in cover_points():
        part -= Pos(x, y, Z_LIP - float(INSERT_M3_L) / 2) * Cylinder(
            float(INSERT_M3_D) / 2, float(INSERT_M3_L) + 0.1)

    # Рёбра посадочного гнезда. Они не обжимают матрицу в размер — гнездо
    # сделано по большему кандидату, а к центру матрицы прижимают языки
    # крышки. Рёбра задают плоскость и не дают блоку разъехаться при сборке.
    x0, x1, y0, y1 = seat_bounds()
    rw, rh = float(SEAT_RIB_W), float(SEAT_RIB_H)
    outer = Pos((x0 + x1) / 2, (y0 + y1) / 2, T + rh / 2) * Box(
        x1 - x0 + 2 * rw, y1 - y0 + 2 * rw, rh)
    inner = Pos((x0 + x1) / 2, (y0 + y1) / 2, T + rh / 2) * Box(
        x1 - x0, y1 - y0, rh)
    ribs = outer - inner
    # Проёмы под языки крышки: язык проходит сквозь ребро, а не мимо него,
    # иначе он упёрся бы в ребро снаружи и до торца матрицы не достал.
    slot_t = float(CLAMP_T) + 0.6
    slot_w = float(CLAMP_W) + 1.2
    for cx, cy, horizontal, sign in clamp_positions():
        if horizontal:
            box = Pos(cx + sign * (slot_t / 2), cy, T + rh / 2) * Box(
                slot_t + 2 * rw, slot_w, rh + 0.1)
        else:
            box = Pos(cx, cy + sign * (slot_t / 2), T + rh / 2) * Box(
                slot_w, slot_t + 2 * rw, rh + 0.1)
        ribs -= box
    part += ribs

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

    # Угловые стяжки: приливы по обе стороны шва членения и винт вдоль шва,
    # ставящийся изнутри полости. Снаружи, включая торцы, крепежа не видно.
    b, arm = float(JOINT_BOSS), float(JOINT_ARM)
    z_lo, z_hi = T, Z_LIP                      # прилив живёт в толще борта
    for x, sy in corner_joints():
        y_seam = float(SPLIT_TOP) if sy > 0 else float(SPLIT_BOT)
        part += Pos(x, y_seam, (z_lo + z_hi) / 2) * Box(b, 2 * arm, z_hi - z_lo)
    for x, sy in corner_joints():
        y_seam = float(SPLIT_TOP) if sy > 0 else float(SPLIT_BOT)
        zc = (z_lo + z_hi) / 2
        # проход винта вдоль Y, через оба прилива
        part -= Pos(x, y_seam, zc) * Rotation(90, 0, 0) * Cylinder(
            float(JOINT_SCREW_D) / 2, 4 * arm)
        # гнездо головки — со стороны полости, то есть с внутренней планки
        y_head = y_seam - sy * (arm - float(JOINT_HEAD_H) / 2)
        part -= Pos(x, y_head, zc) * Rotation(90, 0, 0) * Cylinder(
            float(JOINT_HEAD_D) / 2, float(JOINT_HEAD_H))

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
