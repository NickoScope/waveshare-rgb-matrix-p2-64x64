# -*- coding: utf-8 -*-
"""
Лист M0-2 корпуса C «LED MATRIX»: компоновочная схема.
Вид сзади, разрез стека спереди назад, узел стыка матриц.

    python m0_layout.py M0_komponovka.svg
"""

import math
import sys

FIELD_W, FIELD_H = 256.0, 128.0   # активное поле из двух матриц, ТЗ §3.1
STRIP_H = 20.0                    # сменная полоса снизу, ТЗ §4.4
PANEL = 128.0                     # номинал матрицы; чертёж даёт рамку 127,8
CTRL_W, CTRL_H = 50.0, 42.0       # плата ESP32-S3-RGB-Matrix, ТЗ §3.2
M3 = [(0, 56.85), (-56.85, 44.0), (56.85, 44.0),
      (-56.85, -44.0), (56.85, -44.0), (0, -56.85)]   # заводской чертёж

INK, MUTE, PALE = "#16212c", "#4a5a68", "#8e9aa4"
ACC, WARN, PWR, MNT = "#2f6b8a", "#a8351f", "#8a6a20", "#5a4f80"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self):
        self.o = []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=0.6, dash=None, rx=0):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.1f" fill="%s" '
                 'stroke="%s" stroke-width="%.2f"%s/>' % (x, y, w, h, rx, fill, stroke, sw, d))

    def line(self, x1, y1, x2, y2, stroke=INK, sw=0.4, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                 'stroke-width="%.2f"%s/>' % (x1, y1, x2, y2, stroke, sw, d))

    def circ(self, x, y, r, fill="none", stroke=INK, sw=0.5):
        self.add('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" '
                 'stroke-width="%.2f"/>' % (x, y, r, fill, stroke, sw))

    def txt(self, x, y, s, size=3.4, fill=INK, anchor="start", weight="normal"):
        for i, ln in enumerate(str(s).split("\n")):
            self.add('<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" text-anchor="%s" '
                     'font-weight="%s" font-family="Helvetica,Arial,sans-serif">%s</text>'
                     % (x, y + i * size * 1.35, size, fill, anchor, weight, esc(ln)))

    def arrow(self, x1, y1, x2, y2, stroke=ACC, sw=0.5):
        self.line(x1, y1, x2, y2, stroke, sw)
        a = math.atan2(y2 - y1, x2 - x1)
        for s in (0.38, -0.38):
            self.line(x2, y2, x2 - 3.0 * math.cos(a + s), y2 - 3.0 * math.sin(a + s),
                      stroke, sw)

    def head(self, x, y, title, note):
        self.txt(x, y, title, 6.2, INK, weight="bold")
        self.txt(x, y + 6.5, note, 3.4, MUTE)


# --------------------------------------------------------------------- вид сзади

def rear_view(s, ox, oy):
    s.head(ox, oy - 17, "ВИД СЗАДИ · что где стоит",
           "Задняя крышка снята. Матрицы прижаты с торцов внутрь, между ними ничего нет.\n"
           "Пунктиром — местные приливы задней стенки: только там корпус глубже 20.")
    pad = 14
    bw, bh = FIELD_W + 2 * pad, FIELD_H + STRIP_H + 2 * pad + 8
    s.rect(ox, oy, bw, bh, fill="#f4f6f8", sw=0.9, rx=3)
    fx, fy = ox + pad, oy + pad + 8

    for k in (0, 1):
        px = fx + k * PANEL
        s.rect(px, fy, PANEL, FIELD_H, fill="#e7ecf0", sw=0.7)
        cx, cy = px + PANEL / 2, fy + FIELD_H / 2
        for mx, my in M3:
            s.circ(cx + mx, cy + my, 1.7, "none", "#7a8791", 0.5)
        s.txt(cx, fy + 12, "матрица %d" % (k + 1), 4.2, MUTE, "middle")
        s.txt(cx, fy + 17.5, "6 × M3 по сетке 113,7 × 88", 3.1, PALE, "middle")

    s.line(fx + PANEL, fy - 5, fx + PANEL, fy + FIELD_H + 3, WARN, 1.0)
    s.txt(fx + PANEL, fy - 7, "стык: ни ребра, ни зазора", 3.3, WARN, "middle")

    s.arrow(ox + 2, fy + FIELD_H / 2, fx - 1.5, fy + FIELD_H / 2, WARN, 0.8)
    s.arrow(ox + bw - 2, fy + FIELD_H / 2, fx + FIELD_W + 1.5, fy + FIELD_H / 2, WARN, 0.8)
    s.txt(ox + 3, fy + FIELD_H / 2 - 3.5, "прижим", 3.1, WARN)
    s.txt(ox + bw - 3, fy + FIELD_H / 2 - 3.5, "прижим", 3.1, WARN, "end")

    cbx, cby = fx + FIELD_W - CTRL_W - 16, fy + FIELD_H - CTRL_H - 14
    s.rect(cbx - 5, cby - 5, CTRL_W + 10, CTRL_H + 10, fill="#eef6fa", stroke=ACC,
           sw=0.7, dash="4 2", rx=2)
    s.rect(cbx, cby, CTRL_W, CTRL_H, fill="#dcebf2", stroke=ACC, sw=0.9)
    s.txt(cbx + CTRL_W / 2, cby + 12, "ESP32-S3", 4.2, ACC, "middle", "bold")
    s.txt(cbx + CTRL_W / 2, cby + 18, "50 × 42", 3.2, ACC, "middle")
    s.txt(cbx + CTRL_W / 2, cby + 26, "в приливе задней", 3.0, ACC, "middle")
    s.txt(cbx + CTRL_W / 2, cby + 30.5, "стенки, +12 назад", 3.0, ACC, "middle")
    s.txt(cbx + CTRL_W / 2, cby + 37, "USB-C наружу вниз", 3.0, ACC, "middle")
    s.arrow(cbx + CTRL_W / 2, cby + CTRL_H, cbx + CTRL_W / 2, oy + bh - 3)

    s.line(cbx, cby + 9, fx + PANEL + 34, cby + 9, ACC, 0.7, "3 2")
    s.circ(fx + PANEL + 34, cby + 9, 1.4, "none", ACC, 0.7)
    s.txt(fx + PANEL + 38, cby + 7, "HUB75 вход", 3.1, ACC)
    s.line(fx + PANEL + 30, cby + 22, fx + PANEL - 30, cby + 22, ACC, 0.7, "3 2")
    s.circ(fx + PANEL - 30, cby + 22, 1.4, "none", ACC, 0.7)
    s.txt(fx + PANEL - 26, cby + 20, "HUB75 перемычка на матрицу 1", 3.1, ACC)

    s.rect(fx + 10, fy + FIELD_H - 26, 26, 12, fill="#f7ecd4", stroke=PWR, sw=0.7)
    s.txt(fx + 23, fy + FIELD_H - 18.5, "5 В разв.", 3.1, PWR, "middle")
    for k in (0, 1):
        s.line(fx + 36, fy + FIELD_H - 20, fx + PANEL / 2 + k * PANEL - 20,
               fy + FIELD_H - 20, PWR, 0.7, "3 2")
        s.circ(fx + PANEL / 2 + k * PANEL - 20, fy + FIELD_H - 20, 1.4, "none", PWR, 0.7)
    s.txt(fx + 40, fy + FIELD_H - 22.5, "VH4 на каждую матрицу — током питания "
                                        "контроллер не нагружаем", 3.1, PWR)

    s.rect(fx, oy + 4, FIELD_W, 7, fill="#e6e1f2", stroke=MNT, sw=0.7)
    s.txt(fx + 5, oy + 9, "французский подвес на всю ширину — задаёт вертикаль", 3.2, MNT)
    for x in (fx + 34, fx + FIELD_W - 34):
        s.circ(x, oy + bh - 9, 2.6, "none", MNT, 0.7)
    s.txt(fx + 40, oy + bh - 7.5, "две опоры с регулировкой по горизонту", 3.2, MNT)

    s.rect(fx, fy + FIELD_H, FIELD_W, STRIP_H, fill="#eceff2", sw=0.5, dash="3 2")
    s.txt(fx + 5, fy + FIELD_H + 12, "сменная вставка 20 мм — ставится изнутри, "
                                     "до четырёх ⌀12 и окно датчика", 3.2, MUTE)
    return bw, bh


# ----------------------------------------------------------------------- разрез

# kind: "fix" — наш размер; "meas" — зависит от железа, обмер
# Толщина матрицы 15,0 — габарит литого корпуса по заводскому чертежу (боковой
# вид меряется 15,000). Дистрибьютор даёт 14,5. Это ВЕСЬ модуль целиком, вместе
# с полотном, GOB и электроникой; складывать его по слоям нельзя.
LAYERS = [
    ("лицевая рамка, перекрытие ≤ 0,5", 1.5, "#f2f4f6", INK, "fix"),
    ("матрица целиком", 15.0, "#e7ecf0", INK, "meas"),
    ("шлейф плашмя", 1.5, "#eef2f5", PALE, "fix"),
    ("задняя стенка", 2.0, "#f2f4f6", INK, "fix"),
]
LIMIT = 20.0


def section(s, ox, oy):
    s.head(ox, oy - 17, "РАЗРЕЗ · стек спереди назад",
           "Предел 20 мм по кромке. Матрица съедает 15 из них.")
    k = 5.6
    w = 78.0
    y = oy
    for nm, d, fill, stroke, kind in LAYERS:
        h = d * k
        s.rect(ox, y, w, h, fill=fill, stroke=stroke, sw=0.7,
               dash="3 2" if kind == "meas" else None)
        s.txt(ox - 3, y + h / 2 + 1.2, "%g" % d, 3.6, MUTE, "end")
        s.line(ox + w, y + h / 2, ox + w + 6, y + h / 2, "#c0c8cf", 0.35)
        s.txt(ox + w + 8, y + h / 2 + 1.2, nm + ("  · обмер" if kind == "meas" else ""),
              3.4, WARN if kind == "meas" else INK)
        y += h
    total = sum(d for _, d, _, _, _ in LAYERS)
    s.line(ox - 13, oy, ox - 13, y, "#7a8791", 0.4)
    s.txt(ox - 16, (oy + y) / 2, "%.0f" % total, 5.4, INK, "end", "bold")
    s.txt(ox - 16, (oy + y) / 2 + 6, "по кромке\nпредел %.0f" % LIMIT, 3.1, MUTE, "end")

    s.txt(ox - 16, y + 13,
          "Матрица — единый модуль 15 мм: полотно, GOB и вся электроника уже внутри\n"
          "её литого корпуса. Раскладывать её на слои и складывать их — ошибка;\n"
          "измерять надо один размер, полную толщину модуля с надетым шлейфом.\n\n"
          "За полотном остаётся 3,5 мм. Этого хватает на плоский шлейф и ни на что\n"
          "больше. Колодки HUB75 и VH4 в эти 3,5 мм, скорее всего, не уложатся:\n"
          "под каждую в задней стенке местный карман, кабель загибается у колодки.",
          3.5, MUTE)


def controller(s, ox, oy):
    s.head(ox, oy - 17, "КУДА ДЕВАТЬ КОНТРОЛЛЕР",
           "Плата 50 × 42 в 3,5 мм за полотном не помещается. Три выхода.")
    opts = [
        ("A · прилив сзади", "#2f6b3a",
         "Местный карман в задней стенке под платой: по кромке\n"
         "панель остаётся 20, в зоне прилива 32. Прилив уходит\n"
         "в зазор подвеса, с фронта и сбоку не виден.", "принято"),
        ("B · вынести на кабель", MUTE,
         "Контроллер в отдельной коробке у розетки, к панели\n"
         "идёт шлейф. Панель ровно 20 везде, но появляется\n"
         "вторая коробка и внешний шлейф.", "запасной"),
        ("C · растить корпус", WARN,
         "Ровная задняя плоскость на 32-35 мм. Просто в печати,\n"
         "но нарушает поставленный предел 20.", "отклонено"),
    ]
    y = oy
    for nm, col, body, verdict in opts:
        s.rect(ox, y, 250, 30, fill="#f7f9fa", stroke=col, sw=0.7, rx=2)
        s.txt(ox + 5, y + 7.5, nm, 4.0, col, weight="bold")
        s.txt(ox + 200, y + 7.5, verdict, 3.3, col, "end")
        s.txt(ox + 5, y + 13.5, body, 3.3, MUTE)
        y += 36
    s.txt(ox, y + 4,
          "Толщина у прецедентов: корпуса под MatrixPortal и клоны корпуса Adafruit\n"
          "кладут плату контроллера прямо за панелью и выходят на 28-35 мм по всей\n"
          "площади. Двадцать по кромке держится только приливом.", 3.4, INK)


# -------------------------------------------------------------------- узел стыка

def seam(s, ox, oy):
    s.head(ox, oy - 17, "УЗЕЛ СТЫКА",
           "Почему прижим ведём по плате, а не по литой рамке.")
    k = 1.5
    cases = [("если наружу выходит ПЛАТА 128,0", 128.0, "2,0 ✓", "#2f6b3a"),
             ("если наружу выходит РАМКА 127,8", 127.8, "1,8 ✗", WARN)]
    for i, (lbl, pw, pitch, col) in enumerate(cases):
        yy = oy + i * 54
        s.txt(ox, yy, lbl, 3.7, col, weight="bold")
        for kk in (0, 1):
            px = ox + kk * pw * k / 2
            s.rect(px, yy + 5, pw * k / 2, 15, fill="#e7ecf0", sw=0.6)
            s.rect(px + 2, yy + 20, pw * k / 2 - 4, 5, fill="#dde3e8",
                   stroke=PALE, sw=0.5)
        s.line(ox + pw * k / 2, yy + 2, ox + pw * k / 2, yy + 28, col, 1.0)
        s.txt(ox + pw * k + 4, yy + 14, "плата", 3.0, PALE)
        s.txt(ox + pw * k + 4, yy + 24, "литая рамка", 3.0, PALE)
        s.txt(ox, yy + 35, "полотно %.1f · шаг через стык %s" % (pw * 2, pitch), 3.5, col)
    s.rect(ox - 4, oy + 112, 300, 26, "none", INK, 0.45, dash="3 2")
    s.txt(ox, oy + 120,
          "Чертёж размеряет рамку 127,8 и не размеряет кромку платы. Какой из двух\n"
          "случаев верен, решает обмер. Конструкция обязана работать в обоих:\n"
          "прижим ведём ПЛАТА К ПЛАТЕ и на соприкосновение рамок не опираемся.",
          3.5, INK)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "M0_komponovka.svg"
    W, H = 980, 428
    s = SVG()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d">' % (W * 2, H * 2, W, H))
    s.add('<rect width="%d" height="%d" fill="#fbfcfd"/>' % (W, H))
    s.txt(26, 28, "Корпус C «LED MATRIX» — M0, компоновка", 11, INK, weight="bold")
    s.txt(26, 38, "Две матрицы HUB75, контроллер ESP32-S3, питание 5 В до 35 Вт. "
                  "Предел по толщине — 20 мм по кромке.", 4.2, MUTE)
    s.line(26, 44, W - 26, 44, "#c8d0d8", 0.6)

    bw, bh = rear_view(s, 26, 82)
    section(s, 26 + bw + 92, 82)
    controller(s, 640, 82)
    seam(s, 640, 258)

    s.txt(26, H - 12,
          "Поле 256 × 128, полоса 20 мм и требования к безелю — из ТЗ v1.1. "
          "Сетка M3 и контур 127,8 — из заводского чертежа Waveshare.", 3.5, "#7a8791")
    s.add("</svg>")
    open(out, "w", encoding="utf-8").write("\n".join(s.o))
    print("сохранено:", out)


if __name__ == "__main__":
    main()
