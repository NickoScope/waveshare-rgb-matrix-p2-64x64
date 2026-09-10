# -*- coding: utf-8 -*-
"""
Разрезы сборки корпуса C.

Секут не одну деталь, а всю сборку вместе с макетами железа: смысл разреза
именно в том, чтобы видеть, как детали садятся друг к другу и хватает ли
зазоров. Каждый разрез — пересечение сборки с полупространством.

    E  узел притяжки    — плоскость XZ через бобышку: как держится крышка
    A  полоса и энкодер — плоскость YZ через ось энкодера
    B  верхняя кромка   — плоскость YZ по центру: фаска, матрица, прилив
    C  стык матриц      — плоскость XZ по оси: между матрицами ничего нет
    D  боковой край     — плоскость XZ у борта: борт, фаска, край матрицы
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build123d import Box, Compound, Pos, export_stl

from case_c_lib import CASE_H, CASE_W, DEPTH, ENC_X, FIELD_CY

BIG = 900.0

# Крайняя бобышка притяжки в среднем ряду — на ней и режем узел.
from case_c_lib import cover_points as _cp
_JOIN_X, _JOIN_Y = max(_cp(), key=lambda p: (abs(p[0]), -abs(p[1])))


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace(".", "_"), os.path.join(HERE, name + ".step.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.part


def _half_space(axis, at, keep_positive):
    """Полупространство: всё по одну сторону от плоскости axis = at."""
    d = BIG / 2
    off = d if keep_positive else -d
    c = {"x": (at + off, -float(FIELD_CY), float(DEPTH) / 2),
         "y": (0.0, at + off, float(DEPTH) / 2),
         "z": (0.0, -float(FIELD_CY), at + off)}[axis]
    return Pos(*c) * Box(BIG, BIG, BIG)


def cut(shapes, axis, at, keep_positive=True):
    """Пересечь каждое тело сборки с полупространством."""
    hs = _half_space(axis, at, keep_positive)
    kept = []
    for sh in shapes:
        for solid in sh.solids():
            try:
                r = solid & hs
            except Exception:
                continue
            try:
                if r is None or r.wrapped is None or r.volume < 1e-6:
                    continue
            except (AssertionError, AttributeError):
                continue
            kept.append(r)
    return kept


# Разрез во всю высоту панели читается как тонкая полоска: глубина 30 против
# высоты 169. Поэтому каждый разрез ограничен ещё и окном — фрагментом вокруг
# того узла, ради которого он и делается.
#
#   имя: (ось сечения, координата, какую сторону оставить, окно (x0,x1,y0,y1))
SECTIONS = {
    "A_strip": ("x", float(ENC_X), True, (-BIG, BIG, -95.0, -55.0)),
    "B_top": ("x", 0.0, True, (-BIG, BIG, 45.0, 95.0)),
    "C_seam": ("y", 0.0, False, (-26.0, 26.0, -BIG, BIG)),
    "D_edge": ("y", 0.0, False, (110.0, 150.0, -BIG, BIG)),
    # Узел притяжки: секущая по Y через ряд бобышек, окно вокруг крайней.
    "E_join": ("y", _JOIN_Y, False, (_JOIN_X - 16.0, _JOIN_X + 16.0, -BIG, BIG)),
}


def _window(box):
    x0, x1, y0, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return Pos(cx, cy, float(DEPTH) / 2) * Box(x1 - x0, y1 - y0, BIG)


def build():
    shells = [_load("case_body"), _load("back_cover")]
    mocks = [_load("mockups")]
    out = {}
    for name, (axis, at, pos, box) in SECTIONS.items():
        win = _window(box)
        sh = [b for b in (s & win for s in cut(shells, axis, at, pos))]
        mk = [b for b in (s & win for s in cut(mocks, axis, at, pos))]
        keep = lambda lst: [x for x in lst if _alive(x)]
        out[name] = (keep(sh), keep(mk))
    return out


def _alive(shape):
    try:
        if shape is None or shape.wrapped is None:
            return False
        return shape.volume > 1e-6
    except (AssertionError, AttributeError):
        return False


if __name__ == "__main__":
    outdir = os.path.join(HERE, "out")
    os.makedirs(outdir, exist_ok=True)
    for name, (shell, mock) in build().items():
        for tag, bodies in (("shell", shell), ("mock", mock)):
            if not bodies:
                continue
            c = Compound(children=bodies)
            c.label = f"{name}_{tag}"
            export_stl(c, os.path.join(outdir, f"sect_{name}_{tag}.stl"))
        print(f"{name}: тел оболочки {len(shell)}, макетов {len(mock)}")
