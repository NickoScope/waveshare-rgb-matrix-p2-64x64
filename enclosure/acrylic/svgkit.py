# -*- coding: utf-8 -*-
"""Мелкий рисовальщик SVG. Только классы, без тела скрипта:
импорт не должен ничего перерисовывать.
"""

INK, MUTE, PALE, ACC, WARN, OK = "#12202b", "#6b7d88", "#d7dee3", "#1f7a5a", "#a8451f", "#1f6f9a"


class S:
    def __init__(s, w, h):
        s.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
               f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="#fbfaf7"/>']

    def r(s, x, y, w, h, fill="none", st=INK, sw=1.2, rx=0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        s.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                   f'fill="{fill}" stroke="{st}" stroke-width="{sw}"{d}/>')

    def c(s, x, y, r, fill="none", st=INK, sw=1.2):
        s.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" '
                   f'stroke="{st}" stroke-width="{sw}"/>')

    def l(s, x1, y1, x2, y2, st=INK, sw=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        s.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{st}" stroke-width="{sw}"{d}/>')

    def t(s, x, y, txt, size=11, fill=INK, anchor="start", w="normal"):
        s.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica,Arial" '
                   f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                   f'font-weight="{w}">{txt}</text>')

    def dim(s, x1, y, x2, txt, off=0):
        s.l(x1, y, x2, y, MUTE, 0.8)
        for x in (x1, x2):
            s.l(x, y - 3, x, y + 3, MUTE, 0.8)
        s.t((x1 + x2) / 2, y - 4 + off, txt, 9, MUTE, "middle")

    def save(s, p):
        s.o.append("</svg>")
        open(p, "w").write("\n".join(s.o))


