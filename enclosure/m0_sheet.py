# -*- coding: utf-8 -*-
"""
Лист M0 корпуса C «LED MATRIX»: три варианта лицевой композиции и схема членения.
Пишет SVG; растр — rsvg-convert.

    python m0_sheet.py m0_sheet.svg
"""

import sys

FIELD_W, FIELD_H = 256.0, 128.0      # активное поле, 2 матрицы
STRIP_H = 20.0                        # свободная полоса снизу по ТЗ §4.4
BUILD = 250.0                         # предельный габарит печатной детали
DIAG = BUILD * 2 ** 0.5               # 353,5 — предел суммы L+W при печати по диагонали

# варианты: имя, рамка сверху, с боков, снизу под полосой, вынос рамки вперёд
VAR = [
    ("1 · РАМКА", "ровная рамка 12 мм по периметру,\nполоса заподлицо с лицом",
     12, 12, 12, 0),
    ("2 · КАССЕТА", "рамка 14 мм выступает вперёд на 6 —\nкозырёк против засветки, тень по контуру",
     14, 14, 14, 6),
    ("3 · ПЛИНТ", "сверху и с боков 10, снизу плинт 34 —\nасимметрия, органы и датчик в плинте",
     10, 10, 24, 0),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self):
        self.o = []

    def add(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, fill="none", stroke="#1b232b", sw=0.6, extra=""):
        self.add('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" '
                 'stroke="%s" stroke-width="%.2f" %s/>' % (x, y, w, h, fill, stroke, sw, extra))

    def line(self, x1, y1, x2, y2, stroke="#1b232b", sw=0.4, extra=""):
        self.add('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                 'stroke-width="%.2f" %s/>' % (x1, y1, x2, y2, stroke, sw, extra))

    def txt(self, x, y, s, size=4.0, fill="#1b232b", anchor="start", weight="normal"):
        for i, ln in enumerate(str(s).split("\n")):
            self.add('<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" '
                     'text-anchor="%s" font-weight="%s" '
                     'font-family="Helvetica,Arial,sans-serif">%s</text>'
                     % (x, y + i * size * 1.25, size, fill, anchor, weight, esc(ln)))

    def dim(self, x1, y1, x2, y2, label, off=6, vert=False):
        """Простая размерная линия со стрелками-засечками."""
        if vert:
            xx = x1 + off
            self.line(x1, y1, xx + 2, y1, "#7a8791", 0.25)
            self.line(x2, y2, xx + 2, y2, "#7a8791", 0.25)
            self.line(xx, y1, xx, y2, "#7a8791", 0.35)
            self.txt(xx + 2.5, (y1 + y2) / 2 + 1.4, label, 3.4, "#4a5a68")
        else:
            yy = y1 + off
            self.line(x1, y1, x1, yy + 2, "#7a8791", 0.25)
            self.line(x2, y2, x2, yy + 2, "#7a8791", 0.25)
            self.line(x1, yy, x2, yy, "#7a8791", 0.35)
            self.txt((x1 + x2) / 2, yy + 4.6, label, 3.4, "#4a5a68", "middle")


def draw_variant(s, ox, oy, name, note, ft, fs, fb, relief):
    """Фасад варианта. ox, oy — левый верхний угол наружного контура."""
    ow = FIELD_W + 2 * fs
    oh = ft + FIELD_H + STRIP_H + fb
    # тень выступающей рамки
    if relief:
        s.rect(ox + 2.2, oy + 2.2, ow, oh, fill="#dde3e8", stroke="none")
    s.rect(ox, oy, ow, oh, fill="#f2f4f6", sw=0.8)
    # активное поле
    fx, fy = ox + fs, oy + ft
    s.rect(fx, fy, FIELD_W, FIELD_H, fill="#12181e", stroke="#12181e", sw=0.4)
    # стык двух матриц — штриховая осевая
    s.line(fx + FIELD_W / 2, fy, fx + FIELD_W / 2, fy + FIELD_H,
           "#5c6b78", 0.5, 'stroke-dasharray="3 2.5"')
    s.txt(fx + FIELD_W / 2, fy - 2.5, "стык матриц", 3.2, "#5c6b78", "middle")
    # пиксельная сетка намёком
    for i in range(1, 8):
        s.line(fx + i * FIELD_W / 8, fy, fx + i * FIELD_W / 8, fy + FIELD_H,
               "#20303c", 0.25)
    for i in range(1, 4):
        s.line(fx, fy + i * FIELD_H / 4, fx + FIELD_W, fy + i * FIELD_H / 4,
               "#20303c", 0.25)
    # свободная полоса
    sy = fy + FIELD_H
    s.rect(fx, sy, FIELD_W, STRIP_H, fill="#e6eaee", sw=0.5)
    s.txt(fx + 4, sy + STRIP_H / 2 + 1.3, "сменная вставка 20 мм", 3.4, "#4a5a68")
    for k in range(4):
        cx = fx + FIELD_W - 16 - k * 15
        s.add('<circle cx="%.2f" cy="%.2f" r="4" fill="none" stroke="#8e9aa4" '
              'stroke-width="0.45"/>' % (cx, sy + STRIP_H / 2))
    s.add('<rect x="%.2f" y="%.2f" width="7" height="4" rx="1" fill="none" '
          'stroke="#8e9aa4" stroke-width="0.45"/>' % (fx + 62, sy + STRIP_H / 2 - 2))
    s.txt(fx + 62, sy + STRIP_H / 2 + 8, "датчик", 2.8, "#8e9aa4")
    # углы — места стыка планок рамки
    for cx, cy in ((ox, oy), (ox + ow, oy), (ox, oy + oh), (ox + ow, oy + oh)):
        d = 1 if cx == ox else -1
        e = 1 if cy == oy else -1
        s.line(cx + d * fs * 1.6, cy, cx, cy + e * fs * 1.6, "#c2452f", 0.7)
    # подписи и размеры
    s.txt(ox, oy - 16, name, 6.5, "#16212c", weight="bold")
    s.txt(ox, oy - 9.5, note, 3.6, "#4a5a68")
    s.dim(ox, oy + oh, ox + ow, oy + oh, "%.0f" % ow, 9)
    s.dim(ox + ow, oy, ox + ow, oy + oh, "%.0f" % oh, 5, vert=True)
    s.txt(ox, oy + oh + 21, "рамка  верх %g · борт %g · низ %g%s"
          % (ft, fs, fb, "  ·  вынос вперёд %g" % relief if relief else ""),
          3.4, "#4a5a68")
    return ow, oh


def draw_split(s, ox, oy):
    ow = FIELD_W + 28
    oh = 12 + FIELD_H + STRIP_H + 14
    s.txt(ox, oy - 16, "ЧЛЕНЕНИЕ", 6.5, "#16212c", weight="bold")
    s.txt(ox, oy - 9.5,
          "Ни один шов не пересекает лицо. Планки рамки печатаются ЦЕЛИКОМ по диагонали стола,\n"
          "швы уходят в углы и на заднюю сторону, где их не видно.", 3.6, "#4a5a68")

    parts = [
        ("верхняя планка", ox, oy, ow, 12),
        ("нижняя планка", ox, oy + oh - 14, ow, 14),
        ("борт левый", ox, oy + 12, 12, oh - 26),
        ("борт правый", ox + ow - 12, oy + 12, 12, oh - 26),
    ]
    s.rect(ox + 12, oy + 12, ow - 24, oh - 26, fill="#12181e", stroke="none")
    cols = ["#cfe0e6", "#cfe0e6", "#e9d9c6", "#e9d9c6"]
    for (nm, x, y, w, h), c in zip(parts, cols):
        s.rect(x, y, w, h, fill=c, sw=0.6)
    for cx, cy in ((ox, oy), (ox + ow - 12, oy), (ox, oy + oh - 14), (ox + ow - 12, oy + oh - 14)):
        s.rect(cx, cy, 12, 14 if cy > oy else 12, fill="#d8c6dd", sw=0.6)
    s.txt(ox + ow / 2, oy + oh / 2, "поле 256 × 128", 4.2, "#8fa3b0", "middle")
    s.txt(ox + ow / 2, oy + oh / 2 + 6, "задняя часть — две половины, шов вертикальный сзади",
          3.2, "#8fa3b0", "middle")

    # табличка проверки печати
    tx, ty = ox + ow + 26, oy - 4
    s.txt(tx, ty, "Проверка печати: деталь L × W ложится на стол по диагонали,", 3.6, "#16212c")
    s.txt(tx, ty + 5, "если L + W ≤ %.0f (диагональ поля %.0f × %.0f)." % (DIAG, BUILD, BUILD),
          3.6, "#16212c")
    rows = [("верхняя планка", ow, 12), ("нижняя планка с плинтом", ow, 34),
            ("борт", oh - 26, 12), ("угловая накладка", 26, 26),
            ("задняя половина", ow / 2 + 6, oh)]
    y = ty + 13
    s.txt(tx, y, "деталь", 3.4, "#4a5a68", weight="bold")
    s.txt(tx + 74, y, "L", 3.4, "#4a5a68", "middle", weight="bold")
    s.txt(tx + 92, y, "W", 3.4, "#4a5a68", "middle", weight="bold")
    s.txt(tx + 116, y, "L + W", 3.4, "#4a5a68", "middle", weight="bold")
    s.txt(tx + 140, y, "вердикт", 3.4, "#4a5a68", weight="bold")
    for nm, L, W in rows:
        y += 6.2
        ok = (L + W) <= DIAG
        flat = L <= BUILD and W <= BUILD
        v = "по диагонали ✓" if ok else ("плашмя ✓" if flat else "делить")
        col = "#2f6b3a" if (ok or flat) else "#a8351f"
        s.txt(tx, y, nm, 3.4)
        s.txt(tx + 74, y, "%.0f" % L, 3.4, anchor="middle")
        s.txt(tx + 92, y, "%.0f" % W, 3.4, anchor="middle")
        s.txt(tx + 116, y, "%.0f" % (L + W), 3.4, anchor="middle")
        s.txt(tx + 140, y, v, 3.4, col)
    y += 10
    s.txt(tx, y, "Почему не шов посередине: он совпал бы со стыком матриц —", 3.4, "#a8351f")
    s.txt(tx, y + 5, "тем самым местом, которое всё ТЗ требует сделать невидимым.", 3.4, "#a8351f")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "m0_sheet.svg"
    W, H = 980, 640
    s = SVG()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d">' % (W * 2, H * 2, W, H))
    s.add('<rect width="%d" height="%d" fill="#fbfcfd"/>' % (W, H))
    s.txt(26, 28, "Корпус C «LED MATRIX» — M0", 11, "#16212c", weight="bold")
    s.txt(26, 38, "Три варианта лицевой композиции и схема членения. "
                  "Поле 256 × 128 из двух матриц HUB75, свободная полоса 20 мм снизу.",
          4.2, "#4a5a68")
    s.line(26, 44, W - 26, 44, "#c8d0d8", 0.6)

    x = 26
    for name, note, ft, fs, fb, relief in VAR:
        ow, _ = draw_variant(s, x, 92, name, note, ft, fs, fb, relief)
        x += ow + 34

    s.line(26, 300, W - 26, 300, "#c8d0d8", 0.6)
    draw_split(s, 26, 348)

    s.txt(26, H - 14,
          "Размеры лицевой части — предложение; поле 256 × 128 и полоса 20 мм — из ТЗ. "
          "Толщина и стык уточняются обмером матриц (§3.4).", 3.6, "#7a8791")
    s.add("</svg>")
    open(out, "w", encoding="utf-8").write("\n".join(s.o))
    print("сохранено:", out)


if __name__ == "__main__":
    main()
