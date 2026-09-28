# -*- coding: utf-8 -*-
"""Лист концепции, редакция 2. python3 concept2.py -> KONCEPCIYA_v2.svg"""

import math
import panel_facts as F
import pixfont
from svgkit import S, INK, MUTE, PALE, ACC, WARN, OK


def dot_disc(cx, cy, r_field):
    """Точки сетки внутри круга — решётка динамика по мотивам матрицы."""
    p, out = F.DOT_PITCH, []
    lim = r_field - F.DOT_D / 2
    n = int(lim / p) + 1
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i * p, j * p
            if math.hypot(x, y) <= lim:
                out.append((cx + x, cy + y))
    return out


def dot_text(x0, y0):
    """Строка той же сеткой. x0,y0 — левый верхний угол в мм."""
    return [(x0 + c * F.DOT_PITCH, y0 + r * F.DOT_PITCH) for c, r in TEXT_CELLS]


# ── геометрия компоновки ───────────────────────────────────────────────────
WIN_X, WIN_Y = F.BEZEL_SIDE, F.BEZEL_TOP
COL_X = WIN_X + F.WINDOW_W + F.COL_GAP
SPK_CX = COL_X + F.COL_W / 2
WIN_CY = WIN_Y + F.WINDOW_H / 2

# Динамик — ПО ОСИ ПАНЕЛИ: его центр на горизонтальной оси экрана.
# Выравнивание по верхнему краю пробовали, смотрится хуже.
SPK_CY = WIN_CY
BAND_Y = WIN_Y + F.WINDOW_H + F.BAND_GAP
# Энкодер — на одной линии с надписью, по её середине.
ENC_CY = BAND_Y + F.BAND_H / 2
WORDS = ["NickoScope", "Matrix"]
TEXT_CELLS, TEXT_COLS = pixfont.mini_cells(WORDS)
TEXT_W = TEXT_COLS * F.DOT_PITCH
WIN_CX = WIN_X + F.WINDOW_W / 2
TEXT_X = WIN_CX - TEXT_W / 2

K, PAD = 2.25, 42
s = S(int(F.CASE_W * K + 2 * PAD) + 430, int(F.CASE_H * K + 2 * PAD) + 210)

s.t(PAD, 34, "Корпус LED MATRIX — акрил, редакция 2", 21, INK, w="bold")
s.t(PAD, 54, "Панели утоплены заподлицо · динамик и энкодер справа · "
             "строка надписи она же продух, одной сеткой с решёткой", 11.5, MUTE)

ox, oy = PAD, 76
W, H = F.CASE_W * K, F.CASE_H * K
s.r(ox, oy, W, H, "#ffffff", INK, 1.6, 6 * K)

# окно: панели заподлицо
wx, wy = ox + WIN_X * K, oy + WIN_Y * K
s.r(wx, wy, F.WINDOW_W * K, F.WINDOW_H * K, "#101820", INK, 1.4)
mid = wx + F.WINDOW_W * K / 2
s.l(mid, wy, mid, wy + F.WINDOW_H * K, "#2f4a5c", 0.7, "3 3")
s.t(mid, wy - 6, "стык — ни ребра, ни зазора", 9, WARN, "middle")

# решётка динамика
for x, y in dot_disc(SPK_CX, SPK_CY, F.SPK_CUTOUT / 2):
    s.c(ox + x * K, oy + y * K, F.DOT_D / 2 * K, "#ffffff", MUTE, 0.5)
s.c(ox + SPK_CX * K, oy + SPK_CY * K, F.SPK_CUTOUT / 2 * K, "none", MUTE, 0.6, )
for sx in (-1, 1):
    for sy in (-1, 1):
        s.c(ox + (SPK_CX + sx * F.SPK_BOLT_PITCH / 2) * K,
            oy + (SPK_CY + sy * F.SPK_BOLT_PITCH / 2) * K,
            F.SPK_BOLT_D / 2 * K, "none", INK, 0.8)
s.t(ox + SPK_CX * K, oy + (SPK_CY - F.SPK_FLANGE / 2 - 5) * K,
    "Visaton FRWS 5 SC", 9, MUTE, "middle")

# энкодер
s.c(ox + SPK_CX * K, oy + ENC_CY * K, F.ENC_KNOB_D / 2 * K, "#e8edf0", INK, 1.2)
s.c(ox + SPK_CX * K, oy + ENC_CY * K, F.ENC_HOLE_D / 2 * K, "none", MUTE, 0.7)
s.t(ox + SPK_CX * K, oy + (ENC_CY + F.ENC_KNOB_D / 2 + 9) * K,
    "энкодер", 9, MUTE, "middle")

# строка надписи — она же продух
for x, y in dot_text(TEXT_X, BAND_Y):
    s.c(ox + x * K, oy + y * K, F.DOT_D / 2 * K, "#ffffff", MUTE, 0.5)

s.dim(ox, oy + H + 22, ox + W, f"{F.CASE_W:.1f}")
s.l(ox + W + 14, oy, ox + W + 14, oy + H, MUTE, 0.8)
s.t(ox + W + 20, oy + H / 2, f"{F.CASE_H:.1f}", 10, MUTE)

# ── правая колонка пояснений ───────────────────────────────────────────────
px = ox + W + 76
def blk(y, title, lines, col=ACC):
    s.t(px, y, title, 12, col, w="bold")
    yy = y + 19
    for ln in lines:
        s.t(px, yy, ln, 9.8, MUTE)
        yy += 13.5
    return yy + 10

y = 92
y = blk(y, "ПАНЕЛИ УТОПЛЕНЫ — ГЛУБИНА 28", [
    "Окно вырезано по габариту матрицы, панель",
    "входит в него и стоит заподлицо с лицом.",
    f"Передняя плита {F.T:.0f} мм больше НЕ добавляется",
    "к глубине — её занимают первые 4 мм самой",
    "матрицы.",
    f"    было  {F.T + F.PANEL_T + 9 + F.T:.0f} мм   ·   стало  "
    f"{F.PANEL_T + 9 + F.T:.0f} мм",
    "",
    "Держат панель 12 стоек M3 через штатные",
    "отверстия. Окно её не держит — только",
    "обрамляет, с зазором 0.3 на сторону.",
])

vent = len(TEXT_CELLS) * math.pi * (F.DOT_D / 2) ** 2
y = blk(y, "СТРОКА — ОНА ЖЕ ПРОДУХ", [
    f"«NickoScope Matrix» шрифтом {pixfont.MW}x{pixfont.MH}:",
    f"{TEXT_COLS} колонок, {len(TEXT_CELLS)} отверстий ⌀{F.DOT_D}.",
    "",
    f"Влезает в 128 колонок — столько же, сколько",
    "пикселей поперёк нашего табло, то есть эту",
    "строку можно вывести и на сам экран.",
    "",
    f"При шаге {F.DOT_PITCH} её ширина {TEXT_W:.1f} мм —",
    f"ровно ширина экрана ({F.WINDOW_W - 2 * F.WINDOW_GAP:.0f}).",
    "",
    f"Свободное сечение {vent:.0f} мм² — это и есть",
    "вентиляция, отдельных щелей не нужно.",
], WARN)

y = blk(y, "ПОЛОЖЕНИЕ ПАРЫ", [
    f"Ось окна по высоте: {WIN_CY:.1f}",
    f"Динамик:  {SPK_CY:.1f}  — ниже оси на 12",
    f"Энкодер:  {ENC_CY:.1f}  — под динамиком,",
    f"          поднят от полосы надписей на "
    f"{BAND_Y - ENC_CY - F.ENC_KNOB_D / 2:.0f} мм",
    "",
    "Скажете «ниже/выше на столько-то» — сдвину.",
])

y = blk(y, "СЕТКА", [
    f"отверстие  ⌀{F.DOT_D}      шаг  {F.DOT_PITCH}",
    f"перемычка  {F.DOT_PITCH - F.DOT_D:.1f} мм",
    f"решётка динамика  {len(dot_disc(0, 0, F.SPK_CUTOUT / 2))} отверстий",
    f"строка надписи  {len(TEXT_CELLS)} отверстий",
    f"открытая площадь решётки  "
    f"{100 * math.pi * (F.DOT_D / 2) ** 2 / F.DOT_PITCH ** 2:.0f} %",
], OK)

s.save("KONCEPCIYA_v2.svg")
print(f"KONCEPCIYA_v2.svg   корпус {F.CASE_W:.1f} x {F.CASE_H:.1f} x "
      f"{F.PANEL_T + 9 + F.T:.0f}")
print(f"  динамик ({SPK_CX:.1f}, {SPK_CY:.1f})  энкодер ({SPK_CX:.1f}, {ENC_CY:.1f})")
print(f"  строка: {TEXT_COLS} колонок, {TEXT_W:.1f} мм при окне {F.WINDOW_W:.1f}")
