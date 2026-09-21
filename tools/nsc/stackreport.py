#!/usr/bin/env python3
"""What every function costs on the stack, from GCC's own .su reports.

Build with -fstack-usage (platformio.ini does) and this reads what it left
beside each object file. The build already refuses a frame over -Wstack-usage;
this is for seeing the shape and driving the top of the list down.

**What it cannot tell you**: which task a function runs on. A 2 KB frame is
nothing on the Lua effect task's 32 KB and a great deal on the loop task's
8,192 B - which is where, on 2026-09-21, three 2,048-byte token buffers ended
up without anything saying so. Read this list with the task in mind.

    python3 stackreport.py [build-dir] [--top N] [--over BYTES]
"""
import argparse
import pathlib
import sys

DEFAULT = pathlib.Path.home() / "AnimatedPixelClock-netbroker/.pio/build/matrix-waveshare-rgb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build", nargs="?", default=str(DEFAULT))
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--over", type=int, default=0, help="exit 1 if any frame is at or above this")
    args = ap.parse_args()

    root = pathlib.Path(args.build)
    files = list(root.rglob("*.su"))
    if not files:
        print(f"нет .su в {root} - собрано без -fstack-usage?", file=sys.stderr)
        return 4

    rows = []
    for f in files:
        for line in f.read_text(errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            where, size, kind = parts[0], parts[1], parts[2]
            try:
                n = int(size)
            except ValueError:
                continue
            name = where.split(":", 3)[-1]
            rows.append((n, name.strip(), kind.strip(), f.name))

    rows.sort(reverse=True)
    sizes = sorted(r[0] for r in rows)
    n = len(sizes)
    print(f"функций: {n}   медиана {sizes[n//2]}   90% {sizes[int(n*0.9)]}   "
          f"99% {sizes[int(n*0.99)]}   максимум {sizes[-1]}")
    print(f"\nсамые тяжёлые {args.top}:")
    for size, name, kind, obj in rows[:args.top]:
        flag = "  <-- динамический!" if "dynamic" in kind else ""
        print(f"  {size:6d} Б  {name[:70]}{flag}")

    if args.over:
        bad = [r for r in rows if r[0] >= args.over]
        if bad:
            print(f"\n{len(bad)} кадров от {args.over} Б и выше:")
            for size, name, _, _ in bad:
                print(f"  {size:6d} Б  {name[:70]}")
            return 1
        print(f"\nничего от {args.over} Б и выше")
    return 0


if __name__ == "__main__":
    sys.exit(main())
