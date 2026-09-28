# -*- coding: utf-8 -*-
"""Лист концепции акрилового корпуса. python3 concept.py -> KONCEPCIYA.svg"""

import panel_facts as F

from svgkit import S, INK, MUTE, PALE, ACC, WARN, OK

K = 1.55                      # мм -> px
PAD = 40
s = S(1180, 1380)

# ───────── заголовок ─────────
s.t(PAD, 34, "Корпус LED MATRIX — акрил 4 мм, лазерная резка", 21, INK, w="bold")
s.t(PAD, 54, "Концепция. Конструкция как у корпуса NickoScope32 v1b: шипы плюс резьбовые "
             "стойки через монтажные отверстия матриц.", 11.5, MUTE)

# ───────── 1. вид спереди ─────────
y0 = 92
s.t(PAD, y0, "1 · ВИД СПЕРЕДИ", 12, ACC, w="bold")
ox, oy = PAD, y0 + 18
W, H = F.CASE_W * K, F.CASE_H * K
s.r(ox, oy, W, H, "#ffffff", INK, 1.6, 6 * K)
# поле
fx = ox + F.BEZEL_SIDE * K
fy = oy + F.BEZEL_TOP * K
s.r(fx, fy, F.FIELD_W * K, F.FIELD_H * K, "#101820", INK, 1.2)
# стык двух матриц — его НЕ должно быть видно
mid = fx + F.FIELD_W * K / 2
s.l(mid, fy, mid, fy + F.FIELD_H * K, "#2f4a5c", 0.7, "3 3")
s.t(mid, fy - 5, "стык — ни ребра, ни зазора", 8.5, WARN, "middle")
# энкодер
ex = ox + W - F.ENC_FROM_RIGHT * K
ey = oy + (F.BEZEL_TOP + F.FIELD_H + F.STRIP_H / 2) * K
s.c(ex, ey, F.ENC_KNOB_D / 2 * K, "#e8edf0", INK, 1.2)
s.c(ex, ey, F.ENC_HOLE_D / 2 * K, "none", MUTE, 0.8)
s.t(ex - 14, ey + 4, "энкодер", 9, MUTE, "end")
s.dim(ox, oy + H + 20, ox + W, f"{F.CASE_W:.0f}")
s.dim(fx, oy + H + 38, fx + F.FIELD_W * K, f"поле {F.FIELD_W:.0f}")
s.l(ox + W + 12, oy, ox + W + 12, oy + H, MUTE, 0.8)
s.t(ox + W + 18, oy + H / 2, f"{F.CASE_H:.0f}", 9, MUTE)
s.t(ox, oy + H + 60, f"рамка {F.BEZEL_SIDE:.0f} по бокам и сверху, свободная полоса "
    f"{F.STRIP_H:.0f} снизу", 10, MUTE)

# ───────── 2. разрез ─────────
sx = PAD + W + 130
s.t(sx, y0, "2 · РАЗРЕЗ ПО ГЛУБИНЕ", 12, ACC, w="bold")
LAY = [(F.T, "лицевая плита, акрил", PALE),
       (F.PANEL_T, "матрица целиком", "#233544"),
       (max(F.CONN_H, F.VH4_H, F.CTRL_T), "колодки и контроллер", "#e8edf0"),
       (F.T, "задняя плита, акрил", PALE)]
zy = y0 + 22
SK = 7.0
for d, name, col in LAY:
    s.r(sx, zy, 150, d * SK, col, INK, 1.0)
    s.t(sx + 158, zy + d * SK / 2 + 3.5, f"{d:.1f}  {name}", 10, INK)
    zy += d * SK
tot = sum(l[0] for l in LAY)
s.dim(sx - 14, zy + 14, sx - 14, "")
s.l(sx - 14, y0 + 22, sx - 14, zy, MUTE, 0.8)
s.t(sx - 20, (y0 + 22 + zy) / 2, f"{tot:.0f}", 11, INK, "end", "bold")
s.t(sx, zy + 22, "Матрица — ОДИН модуль, а не стопка слоёв:", 10, WARN, w="bold")
s.t(sx, zy + 37, "пиксели, смола GOB и электроника уже внутри", 9.5, MUTE)
s.t(sx, zy + 50, "литого корпуса. Сложить их как слои — значит", 9.5, MUTE)
s.t(sx, zy + 63, "трижды посчитать одну деталь и уехать к 60 мм.", 9.5, MUTE)

# ───────── 3. вид сзади ─────────
y1 = oy + H + 105
s.t(PAD, y1, "3 · ВИД СЗАДИ — как держатся матрицы", 12, ACC, w="bold")
ox2, oy2 = PAD, y1 + 18
s.r(ox2, oy2, W, H, "#ffffff", INK, 1.6, 6 * K)
# борта, утопленные на 5
s.r(ox2 + F.WALL_INSET * K, oy2 + F.WALL_INSET * K,
    W - 2 * F.WALL_INSET * K, H - 2 * F.WALL_INSET * K, "none", MUTE, 1.0, 0, "5 4")
# две матрицы и их стойки
for i in range(F.PANELS_N):
    cx = ox2 + (F.BEZEL_SIDE + F.PANEL_BOARD * (i + 0.5)) * K
    cy = oy2 + (F.BEZEL_TOP + F.FIELD_H / 2) * K
    s.r(cx - F.PANEL_BOARD / 2 * K, cy - F.PANEL_BOARD / 2 * K,
        F.PANEL_BOARD * K, F.PANEL_BOARD * K, "none", "#9fb0bb", 1.0)
    for mx, my in F.MOUNT_XY:
        s.c(cx + mx * K, cy - my * K, 2.6, ACC, ACC, 0)
# контроллер
ctrl_x = ox2 + W / 2 - F.CTRL_W / 2 * K
ctrl_y = oy2 + H - (F.STRIP_H + 4) * K - F.CTRL_H * K
s.r(ctrl_x, ctrl_y, F.CTRL_W * K, F.CTRL_H * K, "#f3ede1", WARN, 1.2)
s.t(ctrl_x + F.CTRL_W * K / 2, ctrl_y + F.CTRL_H * K / 2 + 3, "контроллер", 8.5, WARN, "middle")
s.t(ox2, oy2 + H + 22, "12 стоек M3 через штатные отверстия матриц (по 6 на матрицу, "
    "размах 113.7)", 10, ACC, w="bold")
s.t(ox2, oy2 + H + 38, "Положение обеих матриц задаёт ЗАДНЯЯ ПЛИТА: лазер ставит "
    "отверстия с точностью", 9.5, MUTE)
s.t(ox2, oy2 + H + 51, "порядка десятой миллиметра, и стык держится ею, а не ребром "
    "между матрицами.", 9.5, MUTE)

# ───────── 4. детали ─────────
px = PAD + W + 130
s.t(px, y1, "4 · ШЕСТЬ ДЕТАЛЕЙ", 12, ACC, w="bold")
PARTS = [("лицевая плита", f"{F.CASE_W:.0f} x {F.CASE_H:.0f}", "окно, энкодер"),
         ("задняя плита", f"{F.CASE_W:.0f} x {F.CASE_H:.0f}", "12 стоек, USB-C, вентиляция"),
         ("борт верхний", f"{F.CASE_W - 2 * F.WALL_INSET:.0f} x {tot:.0f}", "шипы в обе плиты"),
         ("борт нижний", f"{F.CASE_W - 2 * F.WALL_INSET:.0f} x {tot:.0f}", "то же"),
         ("борт левый", f"{F.CASE_H - 2 * F.WALL_INSET:.0f} x {tot:.0f}", "то же"),
         ("борт правый", f"{F.CASE_H - 2 * F.WALL_INSET:.0f} x {tot:.0f}", "то же")]
yy = y1 + 24
for n, sz, note in PARTS:
    s.t(px, yy, n, 10.5, INK, w="bold")
    s.t(px + 108, yy, sz, 10, OK)
    s.t(px + 190, yy, note, 9.5, MUTE)
    yy += 19
s.t(px, yy + 14, "Лицевая плита 284 мм режется ОДНИМ куском.", 10.5, ACC, w="bold")
s.t(px, yy + 29, "Вся нынешняя FDM-конструкция построена вокруг того,", 9.5, MUTE)
s.t(px, yy + 42, "что 284 не лезет на столик 250 и деталь приходится", 9.5, MUTE)
s.t(px, yy + 55, "резать на шесть частей и класть по диагонали.", 9.5, MUTE)
s.t(px, yy + 68, "Лазеру это безразлично: шва по лицу нет вообще.", 9.5, MUTE)

# ───────── 5. варианты лица ─────────
y2 = oy2 + H + 78
s.t(PAD, y2, "5 · ЧЕМ ЗАКРЫТЬ ЛИЦО — решение за вами", 12, WARN, w="bold")
VARS = [("A. Открытое окно", "#101820",
         ["ничего перед пикселями", "картинка как есть", "светодиоды открыты, но они",
          "и так залиты смолой GOB"]),
        ("B. Прозрачный акрил", "#dfe9ee",
         ["как на NickoScope32", "защита от пыли и тычков", "НО: бликует и моет чёрный —",
          "контраст заметно падает"]),
        ("C. Дымчатый акрил", "#7d8f99",
         ["стандарт для светодиодных", "экранов: свет диода проходит", "фильтр один раз, а внешний —",
          "дважды, поэтому чёрное глубже"])]
vx = PAD
for name, col, lines in VARS:
    s.r(vx, y2 + 16, 150, 74, "#ffffff", INK, 1.2, 4)
    s.r(vx + 10, y2 + 26, 130, 40, col, MUTE, 0.8)
    s.t(vx + 75, y2 + 80, name, 10, INK, "middle", "bold")
    ly = y2 + 104
    for ln in lines:
        s.t(vx, ly, ln, 9.2, MUTE)
        ly += 12.5
    vx += 176
s.t(PAD + 530, y2 + 30, "Рекомендую C.", 11.5, WARN, w="bold")
s.t(PAD + 530, y2 + 48, "Вы просили «как NickoScope32», а там весь корпус прозрачный —", 10, MUTE)
s.t(PAD + 530, y2 + 62, "это вариант B. Но у осциллографа за акрилом плата, а тут экран,", 10, MUTE)
s.t(PAD + 530, y2 + 76, "и прозрачное стекло перед матрицей размывает именно чёрный:", 10, MUTE)
s.t(PAD + 530, y2 + 90, "отражение комнаты ложится поверх картинки.", 10, MUTE)
s.t(PAD + 530, y2 + 110, "Борта и заднюю плиту при этом можно оставить прозрачными —", 10, MUTE)
s.t(PAD + 530, y2 + 124, "родство с NickoScope32 сохранится, а лицо будет работать.", 10, MUTE)
s.t(PAD + 530, y2 + 144, "Точный процент пропускания — из паспорта листа у поставщика,", 9.5, WARN)
s.t(PAD + 530, y2 + 158, "своего замера у меня нет.", 9.5, WARN)

# ───────── 6. что мешает резать ─────────
y3 = y2 + 190
s.r(PAD, y3, 1100, 118, "#fdf6f2", WARN, 1.2, 5)
s.t(PAD + 16, y3 + 22, "6 · ЧТО НУЖНО ЗАМЕРИТЬ, ПРЕЖДЕ ЧЕМ РЕЗАТЬ", 12, WARN, w="bold")
s.t(PAD + 16, y3 + 42, "Шесть чисел до сих пор догадки. Железо у вас на руках, так что "
    "это полчаса со штангенциркулем:", 10, INK)
yy = y3 + 62
for v, n in F.unmeasured():
    s.t(PAD + 26, yy, f"·  {v}", 10, WARN, w="bold")
    s.t(PAD + 96, yy, n, 9.8, MUTE)
    yy += 14
s.t(PAD + 600, y3 + 62, "Самое важное — КРОМКА ПЛАТЫ.", 10, WARN, w="bold")
s.t(PAD + 600, y3 + 76, "Чертёж размеряет литую рамку 127.8 и не размеряет плату.", 9.8, MUTE)
s.t(PAD + 600, y3 + 90, "Если наружу выступает рамка, две матрицы вплотную дают 255.6,", 9.8, MUTE)
s.t(PAD + 600, y3 + 104, "и шаг через стык выходит 1.8 вместо 2.0 — это видно глазом.", 9.8, MUTE)

s.save("KONCEPCIYA.svg")
print("KONCEPCIYA.svg")
