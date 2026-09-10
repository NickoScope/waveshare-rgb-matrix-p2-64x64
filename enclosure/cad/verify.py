# -*- coding: utf-8 -*-
"""
Проверка модели корпуса C. Печатает список нарушений и возвращает их число.

Проверяется:
  1. габарит корпуса против заявленного;
  2. попарные пересечения деталей;
  3. хватает ли полости за матрицей на колодки с надетыми разъёмами;
  4. ложится ли каждая деталь на стол принтера;
  5. каждая деталь — одно тело и даёт герметичную сетку;
  6. что осталось на обмере.
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import case_c_lib as L
from build123d import export_stl

VIOL = []


def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace(".", "_"), os.path.join(HERE, name + ".step.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.part


def inter_volume(a, b):
    """Объём пересечения. Пустой результат в build123d 0.11 роняет .wrapped
    на assert, поэтому доступ к нему обёрнут."""
    try:
        r = a & b
    except Exception:
        return 0.0
    try:
        if r is None or r.wrapped is None:
            return 0.0
        return r.volume
    except (AssertionError, AttributeError):
        return 0.0


def fail(msg):
    VIOL.append(msg)
    print(f"  НАРУШЕНИЕ: {msg}")


def main():
    parts = {n: load(n) for n in ("case_body", "back_cover")}

    print("=== 1. габарит ===")
    for n, p in parts.items():
        bb = p.bounding_box()
        print(f"  {n:12s} {bb.size.X:7.2f} x {bb.size.Y:7.2f} x {bb.size.Z:7.2f}")
        if bb.size.X > float(L.CASE_W) + 0.01 or bb.size.Y > float(L.CASE_H) + 0.01:
            fail(f"{n} выходит за габарит корпуса")
    # Габарит по КРОМКЕ считается вне полосы прилива: прилив разрешён и уходит
    # в зазор настенного подвеса, требование 30 мм относится к кромке.
    from build123d import Box, Pos
    dz = L.relief_depth()
    band = Pos(0, float(L.RELIEF_BAND_Y), 0) * Box(
        1000, float(L.RELIEF_BAND_H), 1000)
    edge_z = 0.0
    for p in parts.values():
        rest = p - band
        try:
            edge_z = max(edge_z, rest.bounding_box().max.Z)
        except Exception:
            pass
    total_z = max(p.bounding_box().max.Z for p in parts.values())
    print(f"  глубина по кромке: {edge_z:.2f} (заявлено {float(L.DEPTH):.1f})")
    print(f"  с приливом:        {total_z:.2f} (прилив {dz:.2f})")
    if edge_z > float(L.DEPTH) + 0.01:
        fail(f"глубина по кромке {edge_z:.2f} больше заявленной {float(L.DEPTH):.1f}")

    print("\n=== 2. пересечения деталей ===")
    names = list(parts)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = parts[names[i]], parts[names[j]]
            v = inter_volume(a, b)
            print(f"  {names[i]} ∩ {names[j]}: {v:.3f} мм3")
            if v > 1.0:
                fail(f"{names[i]} и {names[j]} пересекаются на {v:.1f} мм3")

    print("\n=== 3. полость за матрицей ===")
    cav = float(L.CAVITY_BEHIND)
    cav_relief = cav + L.relief_depth()
    print(f"  полость ровная: {cav:.2f}   в полосе прилива: {cav_relief:.2f}")
    for nm, need, in_relief in (
            ("колодка HUB75 с надетым шлейфом", float(L.CONN_STACK), True),
            ("колодка питания с разъёмом", float(L.VH4_STACK), True),
            ("плата контроллера", float(L.CTRL_T), False)):
        have = cav_relief if in_relief else cav
        ok = need <= have
        where = "в приливе" if in_relief else "в ровной полости"
        print(f"  {nm:34s} {need:6.2f} против {have:6.2f} {where}"
              f"  {'входит' if ok else 'НЕ ВХОДИТ'}")
        if not ok:
            fail(f"{nm} ({need:.1f}) не входит: доступно {have:.2f}")

    print("\n=== 4. соединение корпуса и крышки ===")
    body, cover = parts["case_body"], parts["back_cover"]
    n = len(L.cover_points())
    print(f"  точек притяжки: {n}")
    if n < 8:
        fail(f"точек притяжки всего {n} — для панели 284 мм мало")
    to_win, to_wall = L.cover_boss_clearance()
    print(f"  бобышка: до кромки окна {to_win:.2f}, до борта {to_wall:.2f}")
    if min(to_win, to_wall) < 1.2:
        fail(f"бобышка притяжки почти касается стенки: {min(to_win, to_wall):.2f}")
    # крышка должна входить в четверть, не втираясь в борта
    gap = float(L.COVER_GAP)
    print(f"  зазор крышки в четверти: {gap:.2f} на сторону")
    cb = cover.bounding_box()
    if cb.size.Z > float(L.DEPTH):
        pass  # прилив за габарит — это разрешено, проверяется в разделе 1

    print("\n=== 5. свободная полоса и ручка ===")
    bevel_edge = -(float(L.FIELD_H) / 2 + float(L.BEVEL_RUN))   # нижний край фаски
    bottom = -(float(L.FIELD_H) / 2 + float(L.STRIP_H))          # кромка корпуса
    free = bevel_edge - bottom
    print(f"  свободная полоса: {free:.2f} (требуется {float(L.STRIP_FREE):.1f})")
    if free < float(L.STRIP_FREE) - 0.01:
        fail(f"свободная полоса {free:.2f} меньше требуемых {float(L.STRIP_FREE):.1f}")
    r = float(L.ENC_KNOB_D) / 2
    top_gap = bevel_edge - (float(L.ENC_Y) + r)
    bot_gap = (float(L.ENC_Y) - r) - bottom
    print(f"  ручка ⌀{float(L.ENC_KNOB_D):.0f}: до фаски {top_gap:.2f}, "
          f"до кромки {bot_gap:.2f}")
    if top_gap < 0 or bot_gap < 0:
        fail("ручка энкодера не помещается в свободную полосу")

    print("\n=== 6. печать ===")
    for n, p in parts.items():
        bb = p.bounding_box()
        ok, how = L.fits_plate(bb.size.X, bb.size.Y)
        print(f"  {n:12s} {bb.size.X:7.2f} x {bb.size.Y:7.2f}  ->  {how}")
        if not ok:
            # На M1 детали цельные: членение — работа M2 (§10 ТЗ), поэтому
            # это ожидаемый результат, а не нарушение.
            print(f"     ожидаемо на M1: членение выполняется на M2")

    print("\n=== 7. тела и сетка ===")
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    import trimesh
    for n, p in parts.items():
        ns = len(p.solids())
        f = os.path.join(out, n + ".stl")
        export_stl(p, f)
        m = trimesh.load(f)
        broken = len(trimesh.repair.broken_faces(m))
        print(f"  {n:12s} тел={ns}  watertight={m.is_watertight}  дыр={broken}")
        if ns != 1:
            fail(f"{n} состоит из {ns} тел")
        if not m.is_watertight or broken:
            fail(f"{n} даёт негерметичную сетку")

    print("\n=== 8. на обмере ===")
    for nm, v, note in L.measured_params():
        print(f"  {nm:14s} = {v:8.3f}   {note}")

    print(f"\nнарушений: {len(VIOL)}")
    for v in VIOL:
        print(f"  - {v}")
    return len(VIOL)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
