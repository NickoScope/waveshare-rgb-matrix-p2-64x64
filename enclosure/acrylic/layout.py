# -*- coding: utf-8 -*-
"""
Раскладка корпуса LED MATRIX — единая геометрия для SVG и DXF.

Здесь только контуры в миллиметрах, без рисования. Деталь отдаётся словарём
групп; группа — список сегментов:

    ("line", x1, y1, x2, y2)
    ("arc",  cx, cy, r, a1, a2)      углы в градусах, против часовой
    ("circle", cx, cy, r)
    ("text", x, y, строка, высота)   гравировка

Начало координат детали — её левый нижний угол, ось Y вверх.

Конструкция повторяет корпус NickoScope32 v1b: две плиты, четыре борта между
ними на шипах, всё стягивается резьбовыми стойками через штатные отверстия
железа. Отличия продиктованы тем, что тут экран, а не плата:

  * панели УТОПЛЕНЫ в окно передней плиты и стоят заподлицо с её лицом,
    поэтому её 4 мм не добавляются к глубине;
  * ножек нет — панель настенная;
  * решётка динамика и надпись набраны ОДНОЙ точечной сеткой ⌀2 с шагом 3.2,
    по мотивам самой матрицы; надпись заодно работает продухом.
"""

import math

import panel_facts as F
import pixfont

T = F.T
KERF = F.KERF
SLOT_W = F.SLOT_W                                   # поперёк: посадка
SLOT_L = F.FINGER_LEN - 4 * KERF + F.SLOT_L_CLEAR   # вдоль: свободный ход


# ── общие примитивы ────────────────────────────────────────────────────────
def rect(w, h, x0=0.0, y0=0.0):
    return [("line", x0, y0, x0 + w, y0), ("line", x0 + w, y0, x0 + w, y0 + h),
            ("line", x0 + w, y0 + h, x0, y0 + h), ("line", x0, y0 + h, x0, y0)]


def rounded_rect(w, h, r, x0=0.0, y0=0.0):
    return [("line", x0 + r, y0, x0 + w - r, y0),
            ("arc", x0 + w - r, y0 + r, r, -90, 0),
            ("line", x0 + w, y0 + r, x0 + w, y0 + h - r),
            ("arc", x0 + w - r, y0 + h - r, r, 0, 90),
            ("line", x0 + w - r, y0 + h, x0 + r, y0 + h),
            ("arc", x0 + r, y0 + h - r, r, 90, 180),
            ("line", x0, y0 + h - r, x0, y0 + r),
            ("arc", x0 + r, y0 + r, r, 180, 270)]


def plate_outline(w, h, r):
    """Контур плиты со скруглёнными углами и двумя ножками по низу.

    Ножки выступают НИЖЕ кромки на FOOT_PROUD, поэтому габарит детали по Y
    получается h + FOOT_PROUD. Пазы бортов и всё содержимое отсчитываются
    по-прежнему от y = 0, то есть от кромки плиты, а не от низа ножки.
    """
    f, fw, fr = F.FOOT_PROUD, F.FOOT_W, F.FOOT_R
    a = F.FOOT_FROM_EDGE
    feet = [(a, a + fw), (w - a - fw, w - a)]
    path = [("line", r, 0, feet[0][0], 0)]
    for i, (x1, x2) in enumerate(feet):
        path += [("line", x1, 0, x1, -f + fr),
                 ("arc", x1 + fr, -f + fr, fr, 180, 270),
                 ("line", x1 + fr, -f, x2 - fr, -f),
                 ("arc", x2 - fr, -f + fr, fr, 270, 360),
                 ("line", x2, -f + fr, x2, 0)]
        nxt = feet[i + 1][0] if i + 1 < len(feet) else w - r
        path.append(("line", x2, 0, nxt, 0))
    path += [("arc", w - r, r, r, -90, 0),
             ("line", w, r, w, h - r),
             ("arc", w - r, h - r, r, 0, 90),
             ("line", w - r, h, r, h),
             ("arc", r, h - r, r, 90, 180),
             ("line", 0, h - r, 0, r),
             ("arc", r, r, r, 180, 270)]
    return path


def finger_positions(length):
    """Начала шипов вдоль борта.

    Два шипа на 326-мм борт — это гуляющая стенка, поэтому число зависит от
    длины: крайние в 30 мм от концов, между ними примерно через 80.
    """
    a = F.FINGER_FROM_EDGE
    b = length - F.FINGER_FROM_EDGE - F.FINGER_LEN
    if b <= a:
        return [(length - F.FINGER_LEN) / 2]
    n = max(2, round((b - a) / F.FINGER_EVERY) + 1)
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def slot_pair(length, along_x, x0, y0):
    """Пазы под шипы одного борта. along_x — борт идёт вдоль X."""
    out = []
    for f in finger_positions(length):
        c = f + F.FINGER_LEN / 2
        if along_x:
            out += rect(SLOT_L, SLOT_W, x0 + c - SLOT_L / 2, y0 + (T - SLOT_W) / 2)
        else:
            out += rect(SLOT_W, SLOT_L, x0 + (T - SLOT_W) / 2, y0 + c - SLOT_L / 2)
    return out


def plate_slots():
    """Пазы всех четырёх бортов в плите. Одинаковы у передней и задней."""
    w = F.WALL_INSET
    out = []
    for y0 in (w, F.CASE_H - w - T):                       # верх и низ
        out += slot_pair(F.BOX_W, True, w, y0)
    for x0 in (w, F.CASE_W - w - T):                       # бока
        out += slot_pair(F.RAIL_SIDE_L, False, x0, w + T)
    return out


# ── точечная сетка ─────────────────────────────────────────────────────────
def dot_disc(cx, cy, r_field):
    p, lim, out = F.DOT_PITCH, r_field - F.DOT_D / 2, []
    n = int(lim / p) + 1
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            if math.hypot(i * p, j * p) <= lim:
                out.append(("circle", cx + i * p, cy + j * p, F.DOT_D / 2))
    return out


TEXT_CELLS, TEXT_COLS = pixfont.mini_cells(["NickoScope", "Matrix"])
TEXT_W = TEXT_COLS * F.DOT_PITCH


def dot_text(x0, y_top):
    """Строка сеткой. y_top — верх строки, ось Y детали вверх."""
    return [("circle", x0 + c * F.DOT_PITCH, y_top - r * F.DOT_PITCH, F.DOT_D / 2)
            for c, r in TEXT_CELLS]


# ── опорные координаты компоновки ──────────────────────────────────────────
# Ось Y детали смотрит ВВЕРХ, поэтому всё, что в концепции считалось сверху,
# тут отсчитывается от низа: y = CASE_H - y_сверху.
WIN_X = F.BEZEL_SIDE
WIN_Y = F.BEZEL_BOTTOM + F.BAND_H + F.BAND_GAP
WIN_CX = WIN_X + F.WINDOW_W / 2
WIN_CY = WIN_Y + F.WINDOW_H / 2

COL_X = WIN_X + F.WINDOW_W + F.COL_GAP
SPK_CX = COL_X + F.COL_W / 2
SPK_CY = WIN_CY                                  # динамик по оси экрана

BAND_TOP = F.BEZEL_BOTTOM + F.BAND_H
TEXT_X = WIN_CX - TEXT_W / 2
ENC_CX = SPK_CX
ENC_CY = F.BEZEL_BOTTOM + F.BAND_H / 2           # энкодер по линии надписи

# Панели и их стойки: центр каждой матрицы в своей половине окна.
PANEL_CX = [WIN_X + F.WINDOW_GAP + F.PANEL_BOARD * (i + 0.5) for i in range(F.PANELS_N)]
PANEL_CY = WIN_CY
STANDOFFS = [(cx + mx, PANEL_CY + my) for cx in PANEL_CX for mx, my in F.MOUNT_XY]

CTRL_CX = WIN_CX
CTRL_CY = F.BEZEL_BOTTOM + F.BAND_H + F.BAND_GAP + F.CTRL_H / 2 + 4.0


def slot_round(w, h, x0, y0):
    """Щель со скруглёнными торцами."""
    r = h / 2
    return [("line", x0 + r, y0, x0 + w - r, y0),
            ("arc", x0 + w - r, y0 + r, r, -90, 90),
            ("line", x0 + w - r, y0 + h, x0 + r, y0 + h),
            ("arc", x0 + r, y0 + r, r, 90, 270)]


def vent_slots():
    """Два ряда щелей вразбежку по верху задней плиты.

    Места мало: верхние стойки матриц кончаются на 158.0, а паз верхнего
    борта начинается на 166.8 — между ними 8.8 мм. Поэтому щель, подошедшая
    к стойке ближе VENT_CLEAR_X, просто выбрасывается: ряд получается с
    разрывом там, где стоит стойка, и это честнее, чем двигать ряды вслепую.
    """
    w, g, sw = F.VENT_LONG, F.VENT_GAP, F.VENT_SLOT_W
    period = w + g
    x_lo = F.WALL_INSET + T + F.VENT_CLEAR_X
    x_hi = F.CASE_W - F.WALL_INSET - T - F.VENT_CLEAR_X
    top = F.CASE_H - F.WALL_INSET - T - F.VENT_CLEAR_TOP     # низ паза борта
    holes = [(x, y) for x, y in STANDOFFS]
    out = []
    for ri in range(F.VENT_ROWS):
        y0 = top - sw - ri * (sw + F.VENT_ROW_GAP)
        shift = 0.0 if ri % 2 == 0 else period / 2
        x = x_lo - shift
        while x < x_hi - 1.0:
            a, b = max(x, x_lo), min(x + w, x_hi)
            if b - a > 6.0:
                clash = any(abs(hy - (y0 + sw / 2)) < F.STANDOFF_D / 2 + sw / 2 + F.VENT_CLEAR_X
                            and a - F.VENT_CLEAR_X - F.STANDOFF_D / 2 < hx < b + F.VENT_CLEAR_X + F.STANDOFF_D / 2
                            for hx, hy in holes)
                if not clash:
                    out += slot_round(b - a, sw, a, y0)
            x += period
    return out


# ── детали ─────────────────────────────────────────────────────────────────
def front():
    """Лицевая плита: окно под утопленные панели, решётка, надпись, энкодер."""
    p = {"контур": plate_outline(F.CASE_W, F.CASE_H, F.PLATE_CORNER_R)}
    p["пазы"] = plate_slots()
    # Окно по габариту матриц с зазором. Панели входят В него и встают
    # заподлицо с лицом; держат их стойки, окно только обрамляет.
    p["окно"] = rect(F.WINDOW_W, F.WINDOW_H, WIN_X, WIN_Y)
    p["крепёж динамика"] = [
        ("circle", SPK_CX + sx * F.SPK_BOLT_PITCH / 2,
         SPK_CY + sy * F.SPK_BOLT_PITCH / 2, F.SPK_BOLT_D / 2)
        for sx in (-1, 1) for sy in (-1, 1)]
    p["энкодер"] = [("circle", ENC_CX, ENC_CY, F.ENC_HOLE_D / 2)]
    # Решётка и надпись — одна сетка, один слой реза.
    p["сетка"] = dot_disc(SPK_CX, SPK_CY, F.SPK_CUTOUT / 2) + \
        dot_text(TEXT_X, BAND_TOP - F.DOT_PITCH / 2)
    return p


def back():
    """Задняя плита: стойки матриц, контроллер, USB-C."""
    p = {"контур": plate_outline(F.CASE_W, F.CASE_H, F.PLATE_CORNER_R)}
    p["пазы"] = plate_slots()
    p["стойки матриц"] = [("circle", x, y, F.STANDOFF_D / 2) for x, y in STANDOFFS]
    p["крепёж контроллера"] = [
        ("circle", CTRL_CX + mx, CTRL_CY + my, F.CTRL_SCREW_D / 2)
        for mx, my in F.CTRL_MOUNT]
    # USB-C выводится наружу: перепрошивка не должна требовать разборки.
    p["USB-C"] = rect(F.USB_W, F.USB_H, CTRL_CX - F.USB_W / 2,
                      CTRL_CY - F.CTRL_H / 2 - F.USB_H / 2)
    # Окно под магнит: динамик заходит в толщину задней плиты на 3 мм.
    p["окно магнита"] = [("circle", SPK_CX, SPK_CY, F.SPK_RELIEF_D / 2)]
    p["щели"] = vent_slots()
    p["гравировка"] = [("text", F.CASE_W / 2, F.BEZEL_BOTTOM / 2 + 1.0,
                        "NickoScope Matrix  ·  4 mm acrylic", 2.4)]
    return p


def rail_outline(length):
    """Контур борта: шипы сверху и снизу, в обе плиты.

    Ножек нет — панель настенная, стоять ей не на чем.
    """
    seq = [(f, f + F.FINGER_LEN) for f in finger_positions(length)]
    path = [("line", 0, 0, seq[0][0], 0)]
    for i, (x1, x2) in enumerate(seq):
        path += [("line", x1, 0, x1, -T), ("line", x1, -T, x2, -T),
                 ("line", x2, -T, x2, 0)]
        nxt = seq[i + 1][0] if i + 1 < len(seq) else length
        path.append(("line", x2, 0, nxt, 0))
    path.append(("line", length, 0, length, F.CAVITY))
    path.append(("line", length, F.CAVITY, seq[-1][1], F.CAVITY))
    for i in range(len(seq) - 1, -1, -1):
        x1, x2 = seq[i]
        path += [("line", x2, F.CAVITY, x2, F.CAVITY + T),
                 ("line", x2, F.CAVITY + T, x1, F.CAVITY + T),
                 ("line", x1, F.CAVITY + T, x1, F.CAVITY)]
        nxt = seq[i - 1][1] if i > 0 else 0.0
        path.append(("line", x1, F.CAVITY, nxt, F.CAVITY))
    path.append(("line", 0, F.CAVITY, 0, 0))
    return path


def rail_long():
    return {"контур": rail_outline(F.BOX_W)}


def rail_short():
    return {"контур": rail_outline(F.RAIL_SIDE_L)}


def coupon():
    """Пробный купон: линейка пазов, эталонный шип и кусок сетки.

    Помимо посадки шипа проверяет перемычку 1.2 мм между отверстиями сетки —
    она тоньше, чем закладывалась на решётки NickoScope32, и её надо увидеть
    на настоящем резе прежде, чем пускать в дело всю строку надписи.
    """
    steps = [3.30, 3.40, 3.50, 3.60, 3.70, 3.80, 3.90]
    pitch, sl = 16.0, F.FINGER_LEN + 2.0
    w, h = 26.0 + len(steps) * pitch + 46.0, 34.0
    p = {"контур": rounded_rect(w, h, 3.0)}
    y0 = (h - F.FINGER_LEN) / 2
    p["эталон"] = rect(10.0, F.FINGER_LEN, 6.0, y0)
    slots, labels = [], []
    for i, wd in enumerate(steps):
        cx = 26.0 + i * pitch + pitch / 2
        slots += rect(wd, sl, cx - wd / 2, (h - sl) / 2)
        labels.append(("text", cx, 4.0, f"{wd:.2f}", 3.0))
    p["пазы"] = slots
    # кусок сетки: три ряда по шесть — увидеть перемычку 1.2 живьём
    gx = 26.0 + len(steps) * pitch + 16.0
    p["сетка"] = [("circle", gx + c * F.DOT_PITCH, h / 2 - 3.2 + r * F.DOT_PITCH,
                   F.DOT_D / 2) for c in range(6) for r in range(3)]
    p["гравировка"] = labels + [
        ("text", w / 2, h - 5.0, "LED MATRIX  ·  FINGER FIT + DOT WEB  ·  mm", 3.0)]
    return p


PARTS = {
    "лицевая": front, "задняя": back,
    "борт верхний": rail_long, "борт нижний": rail_long,
    "борт левый": rail_short, "борт правый": rail_short,
    "купон": coupon,
}


def bbox(segs):
    xs, ys = [], []
    for s in segs:
        if s[0] == "text":
            xs.append(s[1]); ys.append(s[2])
        elif s[0] == "line":
            xs += [s[1], s[3]]; ys += [s[2], s[4]]
        elif s[0] == "arc":
            _, cx, cy, r, _, _ = s
            xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
        else:
            xs += [s[1] - s[3], s[1] + s[3]]; ys += [s[2] - s[3], s[2] + s[3]]
    return min(xs), min(ys), max(xs), max(ys)


def cut_length(segs):
    """Длина РЕЗА. Гравировка сюда не входит — это другой проход."""
    t = 0.0
    for s in segs:
        if s[0] == "text":
            continue
        if s[0] == "line":
            t += math.hypot(s[3] - s[1], s[4] - s[2])
        elif s[0] == "arc":
            t += abs(math.radians(s[5] - s[4])) * s[3]
        else:
            t += 2 * math.pi * s[3]
    return t


if __name__ == "__main__":
    print(f"{'деталь':16s} {'габарит':>18s} {'сегментов':>10s} {'рез, см':>9s}")
    total = 0.0
    for n, fn in PARTS.items():
        part = fn()
        segs = [s for v in part.values() for s in v]
        x0, y0, x1, y1 = bbox(segs)
        L = cut_length(segs)
        total += L
        print(f"{n:16s} {x1 - x0:8.1f} x {y1 - y0:<7.1f} {len(segs):10d} {L / 10:9.1f}")
    print(f"{'ИТОГО':16s} {'':18s} {'':10s} {total / 10:9.1f}")
