# -*- coding: utf-8 -*-
"""
3D-сборка корпуса LED MATRIX. python3 assembly3d.py

Оси сборки: X вправо, Y вглубь (0 — лицо), Z вверх. Ноль по Z — кромка плит,
ножки уходят ниже нуля.

Вся геометрия берётся из layout.py и panel_facts.py, здесь НИЧЕГО не
пересчитывается: на прошлом корпусе дублирование координат один раз увело
вентилятор от его же решётки.

Точность СЕТКИ, а не геометрии: build123d по умолчанию дробит с допуском
0.001 мм — микрон на детали в 335 мм, из-за чего модель раздувается до
десятков мегабайт и еле открывается. 0.06 тоньше пикселя на экране.
"""

import os

from build123d import (Axis, Box, Compound, Cylinder, Location, Pos, Rot,
                       export_step, export_stl, fillet)

import layout as L
import panel_facts as F

T, D = F.T, F.DEPTH
OUT = "out"
STL_TOL, STL_ANG = 0.06, 0.5


def _dots_solid(dots, y0, depth):
    """Все отверстия сетки одним телом: 300 последовательных вычитаний
    в OpenCascade — это минуты, одно вычитание компаунда — секунды."""
    return Compound(children=[Pos(x, y0 + depth / 2, z) *
                              Rot(90, 0, 0) * Cylinder(r, depth)
                              for _, x, z, r in dots])


def plate(part, y0):
    """Плита из раскладки: тело, ножки, пазы и все отверстия."""
    p = Pos(F.CASE_W / 2, y0 + T / 2, F.CASE_H / 2) * Box(F.CASE_W, T, F.CASE_H)
    p = fillet(p.edges().filter_by(Axis.Y), F.PLATE_CORNER_R)
    # ножки
    for i in (0, 1):
        x0 = F.FOOT_FROM_EDGE if i == 0 else F.CASE_W - F.FOOT_FROM_EDGE - F.FOOT_W
        f = Pos(x0 + F.FOOT_W / 2, y0 + T / 2, -F.FOOT_PROUD / 2) * \
            Box(F.FOOT_W, T, F.FOOT_PROUD)
        # Скругляем ТОЛЬКО два нижних угла, как и в 2D-контуре. На все
        # четыре R1.5 не сядет: ножка высотой ровно 3, и 1.5 + 1.5 — это
        # вырожденный случай, OpenCascade его отвергает.
        f = fillet(f.edges().filter_by(Axis.Y).group_by(Axis.Z)[0], F.FOOT_R)
        p += f
    # пазы бортов: в раскладке каждый паз — четыре отрезка подряд
    for grp in ("пазы",):
        xs = [g for g in part.get(grp, []) if g[0] == "line"]
        for i in range(0, len(xs), 4):
            quad = xs[i:i + 4]
            bx = [c for g in quad for c in (g[1], g[3])]
            bz = [c for g in quad for c in (g[2], g[4])]
            w, h = max(bx) - min(bx), max(bz) - min(bz)
            p -= Pos((min(bx) + max(bx)) / 2, y0 + T / 2,
                     (min(bz) + max(bz)) / 2) * Box(w, T * 3, h)
    # прямоугольные вырезы (окно, USB)
    for grp in ("окно", "USB-C"):
        segs = [g for g in part.get(grp, []) if g[0] == "line"]
        if not segs:
            continue
        bx = [c for g in segs for c in (g[1], g[3])]
        bz = [c for g in segs for c in (g[2], g[4])]
        p -= Pos((min(bx) + max(bx)) / 2, y0 + T / 2, (min(bz) + max(bz)) / 2) * \
            Box(max(bx) - min(bx), T * 3, max(bz) - min(bz))
    # щели вентиляции: в раскладке каждая — линия, дуга, линия, дуга;
    # дуги дают центры торцов и радиус, между ними коробка.
    sl = part.get("щели", [])
    for i in range(0, len(sl), 4):
        arcs = [g for g in sl[i:i + 4] if g[0] == "arc"]
        if len(arcs) != 2:
            continue
        (_, x1, z1, r, _, _), (_, x2, z2, _, _, _) = arcs
        p -= Pos((x1 + x2) / 2, y0 + T / 2, (z1 + z2) / 2) * \
            Box(abs(x2 - x1), T * 3, 2 * r)
        for cx, cz in ((x1, z1), (x2, z2)):
            p -= Pos(cx, y0 + T / 2, cz) * (Rot(90, 0, 0) * Cylinder(r, T * 3))

    # круглые
    circles = [g for grp, v in part.items() if grp not in ("контур", "гравировка")
               for g in v if g[0] == "circle"]
    if circles:
        p -= _dots_solid(circles, y0 - T, T * 3)
    return p


def rail(length):
    """Борт лёжа: X — длина, Z — высота, Y — толщина."""
    r = Pos(length / 2, T / 2, F.CAVITY / 2) * Box(length, T, F.CAVITY)
    for f in L.finger_positions(length):
        cx = f + F.FINGER_LEN / 2
        r += Pos(cx, T / 2, -T / 2) * Box(F.FINGER_LEN, T, T)
        r += Pos(cx, T / 2, F.CAVITY + T / 2) * Box(F.FINGER_LEN, T, T)
    return r


def hardware():
    """Купленное железо — только для проверки зазоров, не печатается."""
    out = {}
    # две матрицы, лицо заподлицо с лицом передней плиты
    m = None
    for cx in L.PANEL_CX:
        b = Pos(cx, F.PANEL_T / 2, L.PANEL_CY) * \
            Box(F.PANEL_BOARD, F.PANEL_T, F.PANEL_BOARD)
        m = b if m is None else m + b
    out["panels"] = m
    # Динамик: фланец к внутренней плоскости лицевой плиты. Корзина сужается
    # к магниту, поэтому рисуем её конусом — иначе не видно, что сквозь
    # заднюю плиту проходит именно магнит.
    from build123d import Cone
    sp = Pos(L.SPK_CX, T + F.SPK_FLANGE_T / 2, L.SPK_CY) * \
        Box(F.SPK_FLANGE, F.SPK_FLANGE_T, F.SPK_FLANGE)
    sp += Pos(L.SPK_CX, T + F.SPK_FLANGE_T + F.SPK_DEPTH_IN / 2, L.SPK_CY) * \
        (Rot(-90, 0, 0) * Cone(F.SPK_CUTOUT / 2 - 1, F.SPK_MAGNET_D / 2,
                               F.SPK_DEPTH_IN))
    out["speaker"] = sp
    # энкодер: втулка сквозь плиту и ручка снаружи
    e = Pos(L.ENC_CX, T / 2, L.ENC_CY) * (Rot(90, 0, 0) * Cylinder(3.5, T + 4))
    e += Pos(L.ENC_CX, -8, L.ENC_CY) * (Rot(90, 0, 0) * Cylinder(F.ENC_KNOB_D / 2, 16))
    out["encoder"] = e
    # контроллер на задней плите
    out["controller"] = Pos(L.CTRL_CX, D - T - F.CTRL_T / 2, L.CTRL_CY) * \
        Box(F.CTRL_W, F.CTRL_T, F.CTRL_H)
    # стойки от задней плиты к матрицам
    st = None
    for x, z in L.STANDOFFS:
        c = Pos(x, (F.PANEL_T + D - T) / 2, z) * \
            (Rot(90, 0, 0) * Cylinder(3.0, D - T - F.PANEL_T))
        st = c if st is None else st + c
    out["standoffs"] = st
    return out


def build():
    parts = {}
    parts["front"] = plate(L.front(), 0.0)
    parts["rear"] = plate(L.back(), D - T)
    # Борт строится лёжа: X — длина, Y — толщина T, Z — высота CAVITY,
    # шипы торчат по Z за оба конца. Rot(-90,0,0) переводит Z -> Y, то есть
    # высота борта ложится вглубь корпуса, а шипы уходят сквозь плиты.
    # После поворота тело стоит в Y = 0…CAVITY, а нужно 4…24 — отсюда +T.
    for name, z in (("rail_top", F.CASE_H - F.WALL_INSET),
                    ("rail_bottom", F.WALL_INSET + T)):
        parts[name] = Pos(F.WALL_INSET, T, z) * (Rot(-90, 0, 0) * rail(F.BOX_W))
    # Боковым нужна длина по Z. Rot(0,-90,0) переводит X -> Z: поворот вокруг
    # Z (как было) уводил длину в Y, то есть борт ложился поперёк корпуса.
    for name, x in (("rail_left", F.WALL_INSET),
                    ("rail_right", F.CASE_W - F.WALL_INSET - T)):
        parts[name] = Pos(x, T, F.WALL_INSET + T) * \
            (Rot(0, -90, 0) * (Rot(-90, 0, 0) * rail(F.RAIL_SIDE_L)))
    parts.update(hardware())
    return parts


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    parts = build()
    for k, v in parts.items():
        b = v.bounding_box()
        print(f"{k:12s} X {b.min.X:7.1f}..{b.max.X:7.1f}  "
              f"Y {b.min.Y:6.1f}..{b.max.Y:6.1f}  Z {b.min.Z:7.1f}..{b.max.Z:7.1f}")
        export_stl(v, os.path.join(OUT, f"3d_{k}.stl"),
                   tolerance=STL_TOL, angular_tolerance=STL_ANG)
    export_step(Compound(children=list(parts.values())),
                os.path.join(OUT, "LEDMX_assembly.step"))
    print("STEP: out/LEDMX_assembly.step")
