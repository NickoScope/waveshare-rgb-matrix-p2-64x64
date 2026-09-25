# -*- coding: utf-8 -*-
"""
Сквозная проверка перед выпуском. python3 audit.py

Проверяется то, что можно проверить счётом: наложения резов, перемычки,
попадание гравировки на рез, посадка шипов. Выход != 0, если есть
блокирующее.

Расстояния меряются ВДОЛЬ геометрии, точками через 0.4 мм. Мерить от углов
габаритного прямоугольника отрезка нельзя: у диагонали эти углы лежат в
стороне от неё самой, и проверка ругается на то, что на деле проходит далеко.
"""

import math
import export as E
import layout as L
import panel_facts as F

MIN_CLEAR = 0.8          # гравировка до реза
MIN_WEB = 1.0            # между двумя резами
STEP = 0.4


def sample(seg):
    if seg[0] == "line":
        n = max(1, int(math.hypot(seg[3] - seg[1], seg[4] - seg[2]) / STEP))
        return [(seg[1] + (seg[3] - seg[1]) * i / n,
                 seg[2] + (seg[4] - seg[2]) * i / n) for i in range(n + 1)]
    if seg[0] == "arc":
        _, cx, cy, r, a1, a2 = seg
        n = max(4, int(abs(math.radians(a2 - a1)) * r / STEP))
        return [(cx + r * math.cos(math.radians(a1 + (a2 - a1) * i / n)),
                 cy + r * math.sin(math.radians(a1 + (a2 - a1) * i / n)))
                for i in range(n + 1)]
    if seg[0] == "circle":
        _, cx, cy, r = seg
        n = max(8, int(2 * math.pi * r / STEP))
        return [(cx + r * math.cos(2 * math.pi * i / n),
                 cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    _, x, y, txt, h = seg
    w = len(txt) * h * 0.62          # ширина знака с запасом, замер 0.546
    return [(x - w / 2, y - h * .6), (x + w / 2, y - h * .6),
            (x - w / 2, y + h * .6), (x + w / 2, y + h * .6)]


def box(seg):
    p = sample(seg)
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    return min(xs), min(ys), max(xs), max(ys)


def near(a, b, gap):
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or
                a[3] + gap < b[1] or b[3] + gap < a[1])


def dist(sa, sb):
    pb = sample(sb)
    return min(math.hypot(x1 - x2, y1 - y2)
               for x1, y1 in sample(sa) for x2, y2 in pb)


def main():
    bad, warn = [], []
    print("=" * 72)
    print("ПРОВЕРКА КОРПУСА LED MATRIX")
    print("=" * 72)

    for name, _, _ in E.PLACES:
        part = E.part_segments(name)
        cuts = [s for g, v in part.items() if g != "гравировка" for s in v]
        engr = part.get("гравировка", [])
        x0, y0, x1, y1 = L.bbox(cuts)
        m = "  (ЗЕРКАЛЬНО)" if name in E.MIRROR else ""
        print(f"\n--- {name}{m}: {x1 - x0:.1f} x {y1 - y0:.1f}, "
              f"резов {len(cuts)}, гравировки {len(engr)}")

        # 1. гравировка не должна ложиться на рез
        worst = None
        for t in engr:
            tb = box(t)
            for c in cuts:
                if not near(box(c), tb, MIN_CLEAR):
                    continue
                d = dist(t, c)
                worst = d if worst is None else min(worst, d)
                if d < MIN_CLEAR:
                    bad.append(f"{name}: надпись «{t[3]}» в {d:.2f} мм от реза")
        if engr:
            print(f"    гравировка: до реза "
                  f"{'чисто' if worst is None else f'{worst:.2f} мм'}")

        # 2. перемычки между круглыми резами
        circ = [c for c in cuts if c[0] == "circle"]
        mn = None
        for i in range(len(circ)):
            for j in range(i + 1, len(circ)):
                a, b = circ[i], circ[j]
                d = math.hypot(a[1] - b[1], a[2] - b[2]) - a[3] - b[3]
                if d < 6.0:
                    mn = d if mn is None else min(mn, d)
        if mn is not None:
            ok = mn >= MIN_WEB
            print(f"    {'✓' if ok else '✗'} перемычка между отверстиями: {mn:.2f} мм")
            if not ok:
                bad.append(f"{name}: перемычка {mn:.2f} мм между отверстиями")

        # 3. зазор между резами РАЗНЫХ групп.
        # Раньше сравнивались только окружности между собой, и щель
        # вентиляции против стойки матрицы проверку не проходила вовсе:
        # щель — это дуги с линиями, а стойка — окружность.
        gl = [(g, sg) for g, v in part.items() if g != "гравировка" for sg in v]
        mn2, pair = None, None
        for i in range(len(gl)):
            ga, sa = gl[i]
            ba = box(sa)
            for j in range(i + 1, len(gl)):
                gb, sb = gl[j]
                if ga == gb:
                    continue
                if not near(ba, box(sb), 4.0):
                    continue
                d = dist(sa, sb)
                if mn2 is None or d < mn2:
                    mn2, pair = d, (ga, gb)
        if mn2 is not None:
            ok = mn2 >= MIN_WEB
            print(f"    {'✓' if ok else '✗'} между группами «{pair[0]}» и "
                  f"«{pair[1]}»: {mn2:.2f} мм")
            if not ok:
                bad.append(f"{name}: «{pair[0]}» и «{pair[1]}» в {mn2:.2f} мм")

        # 4. отверстия не подходят к кромке детали
        edge = None
        for c in circ:
            e = min(c[1] - c[3] - x0, x1 - c[1] - c[3],
                    c[2] - c[3] - y0, y1 - c[2] - c[3])
            edge = e if edge is None else min(edge, e)
        if edge is not None:
            ok = edge >= 2.0
            print(f"    {'✓' if ok else '!'} ближайшее отверстие к кромке: {edge:.2f} мм")
            if edge < 1.2:
                bad.append(f"{name}: отверстие в {edge:.2f} мм от кромки")
            elif not ok:
                warn.append(f"{name}: отверстие в {edge:.2f} мм от кромки")

    # ── посадка ────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("ПОСАДКА ШИПА В ПАЗ")
    print("=" * 72)
    k = F.KERF
    print(f"  рез (ОЦЕНКА до купона)     {k:.2f} мм на сторону")
    print(f"  поперёк: чертёж {L.SLOT_W:.2f} -> факт {L.SLOT_W + 2 * k:.2f}   "
          f"шип = толщина листа {F.T:.2f}")
    print(f"  вдоль:   чертёж {L.SLOT_L:.2f} -> факт {L.SLOT_L + 2 * k:.2f}   "
          f"шип факт {F.FINGER_LEN - 2 * k:.2f}, ход "
          f"{L.SLOT_L + 2 * k - F.FINGER_LEN + 2 * k:.2f}")
    if abs(L.SLOT_W + 2 * k - F.T) > 0.01:
        bad.append("посадка: паз после реза не равен толщине листа")

    # ── окно и рамка ───────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("ОКНО, РАМКА, СЕТКА")
    print("=" * 72)
    slot_in = F.WALL_INSET + F.T
    web = F.BEZEL_SIDE - slot_in
    print(f"  паз борта занимает {F.WALL_INSET:.0f}…{slot_in:.0f} от кромки")
    print(f"  {'✓' if web >= 2.5 else '✗'} перемычка паз -> окно: {web:.2f} мм")
    if web < 2.5:
        bad.append(f"перемычка между пазом борта и окном {web:.2f} мм")
    dot_web = F.DOT_PITCH - F.DOT_D
    print(f"  {'!' if dot_web < 2.0 else '✓'} перемычка сетки: {dot_web:.2f} мм "
          f"(на NickoScope32 закладывалось 2.30 — проверить на купоне)")
    if dot_web < 2.0:
        warn.append(f"перемычка сетки {dot_web:.2f} мм тоньше принятой на NickoScope32")
    vent = len(L.TEXT_CELLS) * math.pi * (F.DOT_D / 2) ** 2
    print(f"  строка надписи: {L.TEXT_COLS} колонок, {len(L.TEXT_CELLS)} отверстий, "
          f"{vent:.0f} мм² продуха")
    print(f"  ширина строки {L.TEXT_W:.1f} при поле {F.FIELD_W:.1f} — "
          f"{'совпадает' if abs(L.TEXT_W - F.FIELD_W) < 0.5 else 'НЕ совпадает'}")

    # ── необмеренное ───────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    um = F.unmeasured()
    print(f"НЕ ОБМЕРЕНО: {len(um)} — резать по этому чертежу НЕЛЬЗЯ")
    for v, n in um:
        print(f"  {str(v):>10}  {n}")

    print("\n" + "=" * 72)
    if bad:
        print(f"ОТКАЗАНО — {len(bad)}:")
        for b in bad:
            print("  ✗", b)
    else:
        print("ГЕОМЕТРИЯ ЧИСТА — блокирующих нет")
    if warn:
        print(f"\nзамечания ({len(warn)}):")
        for w in warn:
            print("  !", w)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
