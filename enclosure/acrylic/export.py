# -*- coding: utf-8 -*-
"""
Выгрузка деталей: DXF для лазера и SVG для глаз.

    python3 export.py

DXF — два слоя: CUT (сквозной рез) и ENGRAVE (гравировка отдельным проходом).
Компенсация реза заложена ТОЛЬКО в посадочные пазы: они нарисованы уже шипа
на 2·kerf, потому что рез их расширит. Величина берётся из panel_facts.SLOT_W
и снимается пробным купоном, который выведен на лист отдельной деталью.
"""

import math
import layout as L
import panel_facts as F

OUT_DXF, OUT_SVG = "LEDMX_case.dxf", "LEDMX_sheets.svg"

NAMES_EN = {
    "лицевая": "FRONT", "задняя": "REAR (MIRRORED)",
    "борт верхний": "RAIL TOP", "борт нижний": "RAIL BOTTOM",
    "борт левый": "RAIL LEFT", "борт правый": "RAIL RIGHT",
    "купон": "FIT COUPON",
}

# Задняя плита режется ЗЕРКАЛЬНО. Раскладка рисует деталь со стороны роста X;
# для передней это взгляд снаружи, а для задней — изнутри: стоя за панелью,
# вы видите ось X в обратную сторону. Без зеркала гравировка легла бы на
# внутреннюю грань и читалась наоборот.
MIRROR = {"задняя"}

PLACES = [("лицевая", 0, 0), ("задняя", 0, 190),
          ("борт верхний", 0, 385), ("борт нижний", 0, 420),
          ("борт левый", 0, 455), ("борт правый", 170, 455),
          ("купон", 0, 495)]


def mirror_segs(segs, x0, x1):
    X = x0 + x1
    out = []
    for s in segs:
        if s[0] == "line":
            out.append(("line", X - s[1], s[2], X - s[3], s[4]))
        elif s[0] == "arc":
            _, cx, cy, r, a1, a2 = s
            out.append(("arc", X - cx, cy, r, 180 - a2, 180 - a1))
        elif s[0] == "text":
            # положение зеркалим, строку — НЕТ: чертёж стал видом снаружи
            out.append(("text", X - s[1], s[2], s[3], s[4]))
        else:
            out.append(("circle", X - s[1], s[2], s[3]))
    return out


def part_segments(name):
    part = L.PARTS[name]()
    if name not in MIRROR:
        return part
    x0, _, x1, _ = L.bbox([s for v in part.values() for s in v])
    return {k: mirror_segs(v, x0, x1) for k, v in part.items()}


def dxf():
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    for lay in ("CUT", "ENGRAVE"):
        if lay not in doc.layers:
            doc.layers.add(lay)
    total = 0.0
    for name, ox, oy in PLACES:
        for grp, segs in part_segments(name).items():
            lay = "ENGRAVE" if grp == "гравировка" else "CUT"
            for s in segs:
                if s[0] == "text":
                    t = msp.add_text(s[3], height=s[4],
                                     dxfattribs={"layer": "ENGRAVE"})
                    t.set_placement((s[1] + ox, s[2] + oy),
                                    align=TextEntityAlignment.MIDDLE_CENTER)
                elif s[0] == "line":
                    msp.add_line((s[1] + ox, s[2] + oy), (s[3] + ox, s[4] + oy),
                                 dxfattribs={"layer": lay})
                elif s[0] == "arc":
                    msp.add_arc((s[1] + ox, s[2] + oy), s[3], s[4], s[5],
                                dxfattribs={"layer": lay})
                else:
                    msp.add_circle((s[1] + ox, s[2] + oy), s[3],
                                   dxfattribs={"layer": lay})
            if grp != "гравировка":
                total += L.cut_length(segs)
    doc.saveas(OUT_DXF)
    return total


def svg():
    from svgkit import S, INK, MUTE, ACC, WARN, OK
    K, PAD = 1.5, 30
    W = max(ox + L.bbox([s for v in part_segments(n).values() for s in v])[2]
            for n, ox, _ in PLACES) * K + 2 * PAD
    H = max(oy + L.bbox([s for v in part_segments(n).values() for s in v])[3]
            for n, _, oy in PLACES) * K + 2 * PAD + 30
    s = S(int(W), int(H))
    for name, ox, oy in PLACES:
        part = part_segments(name)
        x0, y0, x1, y1 = L.bbox([g for v in part.values() for g in v])

        def T(x, y):
            return PAD + (x + ox) * K, H - PAD - (y + oy) * K

        for grp, segs in part.items():
            col = INK if grp == "контур" else (
                MUTE if grp == "гравировка" else (
                    OK if grp == "сетка" else (WARN if "окно" in grp else ACC)))
            sw = 0.9 if grp == "контур" else 0.55
            for g in segs:
                if g[0] == "line":
                    a, b = T(g[1], g[2]); c, d = T(g[3], g[4])
                    s.l(a, b, c, d, col, sw)
                elif g[0] == "arc":
                    _, cx, cy, r, a1, a2 = g
                    n = max(6, int(abs(a2 - a1) / 8))
                    pts = [T(cx + r * math.cos(math.radians(a1 + (a2 - a1) * i / n)),
                             cy + r * math.sin(math.radians(a1 + (a2 - a1) * i / n)))
                           for i in range(n + 1)]
                    for i in range(n):
                        s.l(*pts[i], *pts[i + 1], col, sw)
                elif g[0] == "circle":
                    a, b = T(g[1], g[2])
                    s.c(a, b, g[3] * K, "none", col, sw)
                else:
                    a, b = T(g[1], g[2])
                    s.t(a, b + g[4] * K * 0.35, g[3], g[4] * K, col, "middle")
        a, b = T(x0, y0)
        s.t(a, b + 13, f"{NAMES_EN[name]} · {x1 - x0:.0f} × {y1 - y0:.0f} mm",
            4.2 * K, INK, "start", "bold")
    s.save(OUT_SVG)


if __name__ == "__main__":
    total = dxf()
    svg()
    print(f"DXF: {OUT_DXF}")
    print(f"SVG: {OUT_SVG}")
    print(f"общий рез: {total / 10:.0f} см")
