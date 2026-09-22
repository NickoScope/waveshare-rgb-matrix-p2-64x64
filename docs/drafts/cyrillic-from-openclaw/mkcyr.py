#!/usr/bin/env python3
"""mkcyr.py - PicopixelCyr: a 3x5 (5-wide where needed) Cyrillic set packed in
the exact Adafruit GFX bitmap format PicopixelFB uses.

Emits two things from ONE ASCII-art source, so firmware and simulator can never
disagree:
  --header  -> the PicopixelCyrBitmaps[] / PicopixelCyrGlyphs[] block for
               src/fonts/picopixel_fb.h
  --inc     -> the kPicoCyrBitmap[]/kPicoCyrGlyphs[] block for
               tools/luasim/font_picopixel.inc (append via gen_font.py)

Design rule, same as the panel's Latin: 5 rows tall, ink at baseline rows +2..+6
(yOffset -4), xOffset 0, advance = width + 1. Case is FOLDED - lowercase codepoints
reuse the uppercase bitmap, exactly as lua_px.cpp:202 folds a..z onto A..Z. So the
bitmap holds ~34 shapes; the 96-slot table just points lowercase at uppercase.

Bit order is drawChar's: continuous MSB-first bitstream, row-major (gy outer,
gx inner), each glyph byte-aligned at its bitmapOffset. Verified against the loop
in lua_px.cpp l_text (bo++/(7-(bit&7))).

Diagonal letters (И Й Л Д У) are the known-hard ones at 3px; these are a first
cut to be eyeballed on the wall (panel truth > table) and tweaked in-place here.
"""
import sys

# Uppercase Russian A..Я plus Ё. 5 rows each. '#'=ink '.'=off.
# Width is len(row); keep every row of a glyph the same width.
ART = {
0x0410: ["...", ".#.", "#.#", "###", "#.#", "#.#"][1:],  # А
0x0411: ["###", "#..", "###", "#.#", "###"],             # Б
0x0412: ["##.", "#.#", "##.", "#.#", "##."],             # В
0x0413: ["###", "#..", "#..", "#..", "#.."],             # Г
0x0414: [".##", "#.#", "#.#", "###", "#.#"],             # Д (compromise)
0x0415: ["###", "#..", "##.", "#..", "###"],             # Е
0x0416: ["#.#.#", ".###.", "..#..", ".###.", "#.#.#"],   # Ж (5)
0x0417: ["##.", "..#", ".#.", "..#", "##."],             # З
0x0418: ["#.#", "#.#", "#.#", "#.#", "#.#"],             # И (first cut)
0x0419: [".#.", "#.#", "#.#", "#.#", "#.#"],             # Й (breve, first cut)
0x041A: ["#.#", "#.#", "##.", "#.#", "#.#"],             # К
0x041B: [".##", "#.#", "#.#", "#.#", "#.#"],             # Л
0x041C: ["#...#", "##.##", "#.#.#", "#...#", "#...#"],    # М (5)
0x041D: ["#.#", "#.#", "###", "#.#", "#.#"],             # Н
0x041E: [".#.", "#.#", "#.#", "#.#", ".#."],             # О
0x041F: ["###", "#.#", "#.#", "#.#", "#.#"],             # П
0x0420: ["###", "#.#", "###", "#..", "#.."],             # Р
0x0421: [".##", "#..", "#..", "#..", ".##"],             # С
0x0422: ["###", ".#.", ".#.", ".#.", ".#."],             # Т
0x0423: ["#.#", "#.#", ".##", "..#", "##."],             # У
0x0424: ["..#..", ".###.", "#.#.#", ".###.", "..#.."],   # Ф (5)
0x0425: ["#.#", "#.#", ".#.", "#.#", "#.#"],             # Х
0x0426: ["#.#", "#.#", "#.#", "#.#", "###"],             # Ц (no descender)
0x0427: ["#.#", "#.#", "###", "..#", "..#"],             # Ч
0x0428: ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],    # Ш (5)
0x0429: ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],    # Щ (5, no tail)
0x042A: ["##..", ".#..", ".##.", ".#.#", ".##."],        # Ъ (4)
0x042B: ["#...#", "#...#", "##..#", "#.#.#", "##..#"],    # Ы (5)
0x042C: ["#..", "#..", "##.", "#.#", "##."],             # Ь
0x042D: ["##.", "..#", ".##", "..#", "##."],             # Э
0x042E: ["#.###", "#.#.#", "#.#.#", "#.#.#", "#.###"],    # Ю (5)
0x042F: [".##", "#.#", ".##", "#.#", "#.#"],             # Я
0x0401: ["#.#", "###", "##.", "#..", "###"],             # Ё (dots+E, first cut)
}

# Lowercase 0x0430..0x044F fold onto 0x0410..0x042F; ё 0x0451 -> Ё 0x0401.
FOLD = {cp + 0x20: cp for cp in range(0x0410, 0x0430)}
FOLD[0x0451] = 0x0401

FIRST, LAST = 0x0400, 0x045F          # whole Cyrillic-basic block, room to grow


def pack(rows):
    bits = "".join("1" if ch == "#" else "0" for r in rows for ch in r)
    out = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i + 8].ljust(8, "0")
        out.append(int(chunk, 2))
    return out


def build():
    bitmap, glyphs, shape_off = [], {}, {}
    NOTDEF = (0, 0, 0, 2, 0, 1)       # zero-width space, like 0x20
    for cp in sorted(ART):
        rows = ART[cp]
        w, h = len(rows[0]), len(rows)
        assert all(len(r) == w for r in rows), hex(cp)
        shape_off[cp] = len(bitmap)
        bitmap += pack(rows)
        glyphs[cp] = (shape_off[cp], w, h, w + 1, 0, -4)
    table = []
    for cp in range(FIRST, LAST + 1):
        if cp in glyphs:
            table.append((cp, glyphs[cp]))
        elif cp in FOLD and FOLD[cp] in glyphs:
            o, w, h, a, xo, yo = glyphs[FOLD[cp]]
            table.append((cp, (o, w, h, a, xo, yo)))   # shares uppercase offset
        else:
            table.append((cp, NOTDEF))
    return bitmap, table


def emit_header(bitmap, table):
    rows = "\n".join("    " + " ".join(f"0x{b:02X}," for b in bitmap[i:i + 12])
                     for i in range(0, len(bitmap), 12))
    gl = "\n".join(
        f"    {{{o:4d},{w:2d},{h:2d},{a:2d},{xo:3d},{yo:3d}}},  // U+{cp:04X}"
        for cp, (o, w, h, a, xo, yo) in table)
    return f"""const uint8_t PicopixelCyrBitmaps[] PROGMEM = {{
{rows}}};

const GFXglyph PicopixelCyrGlyphs[] PROGMEM = {{
{gl}}};

const GFXfont PicopixelCyr PROGMEM = {{(uint8_t *)PicopixelCyrBitmaps,
                                      (GFXglyph *)PicopixelCyrGlyphs,
                                      0x{FIRST:04X}, 0x{LAST:04X}, 7}};"""


def emit_inc(bitmap, table):
    rows = "\n".join("  " + " ".join(f"0x{b:02X}," for b in bitmap[i:i + 12])
                     for i in range(0, len(bitmap), 12))
    gl = "\n".join(f"  {{{o:4d},{w:2d},{h:2d},{a:2d},{xo:3d},{yo:3d}}},  // U+{cp:04X}"
                   for cp, (o, w, h, a, xo, yo) in table)
    return (f"#define PICO_CYR_FIRST 0x{FIRST:04X}\n"
            f"#define PICO_CYR_LAST  0x{LAST:04X}\n"
            f"static const unsigned char kPicoCyrBitmap[] = {{\n{rows}\n}};\n"
            f"static const PicoGlyph kPicoCyrGlyphs[] = {{\n{gl}\n}};\n")


if __name__ == "__main__":
    bitmap, table = build()
    mode = sys.argv[1] if len(sys.argv) > 1 else "--stats"
    if mode == "--header":
        print(emit_header(bitmap, table))
    elif mode == "--inc":
        print(emit_inc(bitmap, table))
    else:
        gsz = 7  # sizeof(GFXglyph): u16 + 4*u8 + ... = 7 packed, 8 aligned
        sys.stderr.write(
            f"shapes: {len(ART)}   bitmap: {len(bitmap)} B (flash)\n"
            f"glyph table: {len(table)} entries x {gsz} B = {len(table)*gsz} B (flash)\n"
            f"total flash: ~{len(bitmap) + len(table)*gsz} B   RAM/SRAM: 0\n")
