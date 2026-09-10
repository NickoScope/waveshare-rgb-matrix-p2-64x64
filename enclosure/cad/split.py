# -*- coding: utf-8 -*-
"""
Членение корпуса под стол принтера (этап M2).

Корпус 284 x 168.9 не ложится на стол 250 ни плашмя, ни по диагонали, поэтому
он режется. Схема:

    корпус  -> четыре планки: верхняя, нижняя и два борта.
               Швы лежат на границах изображения — по верхней кромке поля и
               по границе поля с нижней полосой, — то есть на линиях, которые
               на лице и так читаются.
    крышка  -> две части, шов смещён от центра: по центру идёт ребро прижима
               вдоль стыка матриц, рвать его нельзя.

    python split.py
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import case_c_lib as L
from build123d import Box, Compound, Pos, export_stl

BIG = 900.0


def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace(".", "_"), os.path.join(HERE, name + ".step.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.part


def slab(axis, lo, hi):
    """Плита-полупространство между двумя плоскостями по одной оси."""
    lo = -BIG if lo is None else lo
    hi = BIG if hi is None else hi
    c = (lo + hi) / 2
    d = hi - lo
    if axis == "y":
        return Pos(0, c, 0) * Box(BIG, d, BIG)
    return Pos(c, 0, 0) * Box(d, BIG, BIG)


def cut(shape, axis, lo, hi):
    """Куски детали внутри полосы. Возвращает список тел."""
    keep = []
    region = slab(axis, lo, hi)
    for s in shape.solids():
        try:
            r = s & region
        except Exception:
            continue
        try:
            if r is None or r.wrapped is None:
                continue
        except (AssertionError, AttributeError):
            continue
        for solid in r.solids():
            if solid.volume > 1.0:
                keep.append(solid)
    return keep


def split_body(body):
    g = float(L.SPLIT_GAP)
    top, bot = float(L.SPLIT_TOP), float(L.SPLIT_BOT)
    out = {}
    out["body_top"] = cut(body, "y", top + g, None)
    out["body_bottom"] = cut(body, "y", None, bot - g)
    # Средняя полоса — это два борта, между которыми окно, то есть пустота.
    # Булева операция всё равно отдаёт их одним телом, поэтому режем полосу
    # ещё и по оси: рез идёт по пустому месту и ничего не задевает.
    band_lo, band_hi = bot + g, top - g
    left = cut(body, "y", band_lo, band_hi)
    left = [b for b in cut_x(left, None, 0.0)]
    right = cut(body, "y", band_lo, band_hi)
    right = [b for b in cut_x(right, 0.0, None)]
    out["body_side_L"] = left
    out["body_side_R"] = right
    return out


def cut_x(bodies, lo, hi):
    region = slab("x", lo, hi)
    keep = []
    for s in bodies:
        try:
            r = s & region
        except Exception:
            continue
        try:
            if r is None or r.wrapped is None:
                continue
        except (AssertionError, AttributeError):
            continue
        for solid in r.solids():
            if solid.volume > 1.0:
                keep.append(solid)
    return keep


def split_cover(cover):
    g = float(L.SPLIT_GAP)
    x = float(L.COVER_SPLIT_X)
    return {"cover_L": cut(cover, "x", None, x - g),
            "cover_R": cut(cover, "x", x + g, None)}


def main():
    body, cover = load("case_body"), load("back_cover")

    # Резать или нет — решает поле принтера, а не привычка. При 350 обе
    # детали ложатся целиком, и тогда лучший вариант членения — никакого.
    if not L.split_needed():
        print(f"поле печати {float(L.PLATE):.0f} × {float(L.PLATE):.0f} — "
              f"членение не требуется:")
        for name, part in (("case_body", body), ("back_cover", cover)):
            bb = part.bounding_box()
            ok, how = L.fits_plate(bb.size.X, bb.size.Y)
            print(f"  {name:12s} {bb.size.X:7.1f} × {bb.size.Y:7.1f} × "
                  f"{bb.size.Z:6.1f}  {how}")
        print("\nДве детали, обе печатаются целиком.")
        return 0

    parts = {}
    parts.update(split_body(body))
    parts.update(split_cover(cover))

    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    import trimesh
    print(f"{'деталь':14s} {'тел':>4s} {'X':>8s} {'Y':>8s} {'Z':>7s}  "
          f"{'L+W':>7s}  {'герм':>5s}  вердикт")
    bad = 0
    volumes = {}
    for name, bodies in parts.items():
        if not bodies:
            print(f"{name:14s}  пусто")
            bad += 1
            continue
        c = Compound(children=bodies)
        c.label = name
        f = os.path.join(out, f"split_{name}.stl")
        export_stl(c, f)
        # Булев рез по границе окна оставляет в сетке лоскуты нулевой
        # толщины: объёма у них нет, но габарит детали они раздувают, и
        # слайсер такое честно попытается напечатать. Чистим и меряем уже
        # по тому файлу, который поедет в печать.
        m = trimesh.load(f)
        m.update_faces(m.nondegenerate_faces())
        m.remove_unreferenced_vertices()
        pieces = [q for q in m.split(only_watertight=False) if q.volume > 1.0]
        if pieces:
            m = trimesh.util.concatenate(pieces) if len(pieces) > 1 else pieces[0]
        m.export(f)
        tight = m.is_watertight and not len(trimesh.repair.broken_faces(m))
        sx, sy, sz = (m.bounds[1] - m.bounds[0])
        ok, how = L.fits_plate(sx, sy)
        flag = "" if ok else "  <-- НЕ ВЛЕЗАЕТ"
        print(f"{name:14s} {len(bodies):4d} {sx:8.1f} {sy:8.1f} "
              f"{sz:7.1f}  {sx + sy:7.1f}  "
              f"{'да' if tight else 'НЕТ':>5s}  {how}{flag}")
        if not ok:
            bad += 1
        if len(bodies) != 1:
            print(f"{'':14s}      деталь распалась на {len(bodies)} тел")
            bad += 1
        if not tight:
            print(f"{'':14s}      негерметичная сетка")
            bad += 1
        volumes[name] = m.volume
    # Сумма кусков должна сойтись с целым за вычетом того, что съели швы.
    # Если разошлось сильнее — рез что-то потерял, и это надо увидеть здесь,
    # а не на столе принтера.
    whole = body.volume + cover.volume
    total = sum(v for v in volumes.values())
    seam_len = 4 * float(L.SPLIT_GAP) * 2 + 2 * float(L.SPLIT_GAP)
    lost = whole - total
    print(f"\nобъём: целое {whole / 1000:.1f} см3, куски {total / 1000:.1f} см3, "
          f"швы съели {lost / 1000:.2f} см3 ({100 * lost / whole:.1f} %)")
    if lost < 0 or lost / whole > 0.05:
        print("  потеря на швах не похожа на зазор — проверить рез")
        bad += 1

    print(f"\nдеталей: {len(parts)}, проблемных: {bad}")
    return bad


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
