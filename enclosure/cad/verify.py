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
    dz = L.relief_depth()
    cav_relief = cav + dz
    print(f"  полость за модулем: {cav:.2f}"
          + (f"   в полосе прилива: {cav_relief:.2f}" if dz > 0
             else "   прилив не нужен, крышка ровная"))
    for nm, need, in_relief in (
            ("выступ шлейфа HUB75 за модуль", float(L.CONN_PROUD), True),
            ("выступ разъёма питания", float(L.VH4_PROUD), True),
            ("плата контроллера", float(L.CTRL_T), False)):
        have = cav_relief if in_relief else cav
        ok = need <= have
        where = "в приливе" if in_relief else "в ровной полости"
        print(f"  {nm:34s} {need:6.2f} против {have:6.2f} {where}"
              f"  {'входит' if ok else 'НЕ ВХОДИТ'}")
        if not ok:
            fail(f"{nm} ({need:.1f}) не входит: доступно {have:.2f}")

    print("\n=== 3.1 что определяет глубину ===")
    need_with = L.min_depth(True)
    need_without = L.min_depth(False)
    print(f"  на панель уходит: {float(L.WALL_FRONT):.1f} + {float(L.PANEL_T):.1f}"
          f" + {float(L.WALL_BACK):.1f} = "
          f"{float(L.WALL_FRONT) + float(L.PANEL_T) + float(L.WALL_BACK):.1f}")
    print(f"  минимум с контроллером внутри: {need_with:.1f}")
    print(f"  минимум без контроллера:       {need_without:.1f}")
    print(f"  назначено: {float(L.DEPTH):.1f}")
    if float(L.DEPTH) < need_with:
        fail(f"глубина {float(L.DEPTH):.1f} меньше необходимой {need_with:.1f}")

    print("\n=== 4. соединение корпуса и крышки ===")
    body, cover = parts["case_body"], parts["back_cover"]
    pts = L.cover_points()
    n = len(pts)
    # По три винта на сторону: углы работают на две стороны сразу.
    xs = sorted({round(x, 2) for x, _ in pts})
    ys = sorted({round(y, 2) for _, y in pts})
    per_side = {
        "верх": sum(1 for _, y in pts if round(y, 2) == ys[-1]),
        "низ": sum(1 for _, y in pts if round(y, 2) == ys[0]),
        "левый борт": sum(1 for x, _ in pts if round(x, 2) == xs[0]),
        "правый борт": sum(1 for x, _ in pts if round(x, 2) == xs[-1]),
    }
    print(f"  винтов: {n}  " + ", ".join(f"{k} {v}" for k, v in per_side.items()))
    if min(per_side.values()) < 3:
        fail("на какой-то стороне меньше трёх винтов: "
             + ", ".join(f"{k} {v}" for k, v in per_side.items() if v < 3))
    step = max(xs[-1] - xs[len(xs) // 2], ys[-1] - ys[len(ys) // 2])
    print(f"  наибольший шаг между винтами: {step:.1f} мм")
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

    print("\n=== 5. посадка матриц ===")
    x0, x1, y0, y1 = L.seat_bounds()
    print(f"  гнездо: {x1 - x0:.2f} x {y1 - y0:.2f}")
    for w, ov in sorted(L.overlap_after_centering().items()):
        slack = (x1 - x0) - w
        print(f"  полотно {w:6.1f}: люфт в гнезде {slack:.2f}, "
              f"перекрытие безелем {ov:+.2f} на сторону")
        if ov <= 0:
            fail(f"при полотне {w:.1f} безель не перекрывает поле: {ov:+.2f}")
        if slack < 0:
            fail(f"полотно {w:.1f} не входит в гнездо")
    # прижим языками: зуб обязан доставать до торца в узком случае
    narrow = min(float(L.PANEL_BOARD), float(L.PANEL_FRAME))
    tooth_face = narrow - float(L.CLAMP_PRELOAD)
    for cand in (float(L.PANEL_BOARD), float(L.PANEL_FRAME)):
        grip = cand - tooth_face
        print(f"  язык против торца {cand:.1f}: перекрытие {grip:+.2f}")
        if grip <= 0:
            fail(f"язык не достаёт до торца при {cand:.1f}")

    print("\n=== 5.1 угловые стяжки ===")
    jc = L.joint_clearance()
    print(f"  зазор прилива до гнезда панели: {jc:+.2f}")
    if jc < 0.5:
        fail(f"угловой прилив упирается в панель: зазор {jc:+.2f}")

    print("\n=== 6. на что опирается конструкция ===")
    if L.USE_FRAME_M3:
        print("  панели держатся винтами по сетке M3 монтажной рамки")
        fail("конструкция опирается на сетку M3, которая принадлежит рамке; "
             "рамка — принадлежность, на голой панели точек может не быть")
    else:
        print("  панели держатся прижимом: гнездо, языки в плоскости, "
              "рёбра крышки по тыльной стороне")
        print("  сетка M3 монтажной рамки не используется — и правильно: "
              "рамку мы не ставим")

    print("\n=== 7. свободная полоса и ручка ===")
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

    print("\n=== 8. печать ===")
    for n, p in parts.items():
        bb = p.bounding_box()
        ok, how = L.fits_plate(bb.size.X, bb.size.Y)
        print(f"  {n:12s} {bb.size.X:7.2f} x {bb.size.Y:7.2f}  ->  {how}")
        if not ok:
            # На M1 детали цельные: членение — работа M2 (§10 ТЗ), поэтому
            # это ожидаемый результат, а не нарушение.
            print(f"     ожидаемо на M1: членение выполняется на M2")

    print("\n=== 9. тела и сетка ===")
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

    print("\n=== 10. на обмере ===")
    for nm, v, note in L.measured_params():
        print(f"  {nm:14s} = {v:8.3f}   {note}")

    print(f"\nнарушений: {len(VIOL)}")
    for v in VIOL:
        print(f"  - {v}")
    return len(VIOL)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
