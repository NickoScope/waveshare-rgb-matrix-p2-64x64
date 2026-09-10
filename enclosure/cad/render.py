# -*- coding: utf-8 -*-
"""
Рендер модели корпуса C в PNG, без графического стека.

Собственный z-буфер по треугольникам STL: pyglet и OpenGL в этом окружении
недоступны, а посмотреть на деталь нужно. Освещение — ламбертово от одного
источника, плюс лёгкий контурный тон по глубине.

    python render.py
"""

import os

import numpy as np
import trimesh
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

BG = np.array([251, 252, 253], dtype=np.float64)
LIGHT = np.array([-0.35, 0.45, -0.82])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def _rot(elev, azim):
    e, a = np.radians(elev), np.radians(azim)
    ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return rx @ ry


def render(meshes, elev, azim, size=(1500, 1000), pad=0.06, mirror=False):
    """meshes: список (trimesh, базовый цвет RGB).

    mirror — для видов с лица. Система координат левая (см. case_c_lib),
    поэтому без отражения по X право и лево меняются местами, и энкодер,
    стоящий справа, уезжает налево.
    """
    R = _rot(elev, azim)
    if mirror:
        R = np.diag([-1.0, 1.0, 1.0]) @ R
    tris, cols = [], []
    for m, c in meshes:
        v = m.vertices @ R.T
        f = v[m.faces]
        n = np.cross(f[:, 1] - f[:, 0], f[:, 2] - f[:, 0])
        ln = np.linalg.norm(n, axis=1)
        keep = ln > 1e-12
        f, n, ln = f[keep], n[keep], ln[keep]
        n = n / ln[:, None]
        tris.append(f)
        shade = np.clip(np.abs(n @ LIGHT), 0.0, 1.0) * 0.75 + 0.25
        cols.append(np.array(c, dtype=np.float64)[None, :] * shade[:, None])
    tris = np.concatenate(tris)
    cols = np.concatenate(cols)

    W, H = size
    x0, y0 = tris[:, :, 0].min(), tris[:, :, 1].min()
    x1, y1 = tris[:, :, 0].max(), tris[:, :, 1].max()
    sc = min(W * (1 - 2 * pad) / (x1 - x0), H * (1 - 2 * pad) / (y1 - y0))
    ox = (W - (x1 - x0) * sc) / 2 - x0 * sc
    oy = (H - (y1 - y0) * sc) / 2 - y0 * sc

    px = tris[:, :, 0] * sc + ox
    py = H - (tris[:, :, 1] * sc + oy)
    pz = tris[:, :, 2]

    img = np.repeat(np.repeat(BG[None, None, :], H, 0), W, 1)
    zbuf = np.full((H, W), -1e30)

    order = np.argsort(pz.mean(axis=1))
    for i in order:
        ax, ay, az = px[i], py[i], pz[i]
        xmin, xmax = int(max(0, np.floor(ax.min()))), int(min(W - 1, np.ceil(ax.max())))
        ymin, ymax = int(max(0, np.floor(ay.min()))), int(min(H - 1, np.ceil(ay.max())))
        if xmax < xmin or ymax < ymin:
            continue
        xs = np.arange(xmin, xmax + 1)
        ys = np.arange(ymin, ymax + 1)
        gx, gy = np.meshgrid(xs, ys)
        d = ((ay[1] - ay[2]) * (ax[0] - ax[2]) + (ax[2] - ax[1]) * (ay[0] - ay[2]))
        if abs(d) < 1e-9:
            continue
        w0 = ((ay[1] - ay[2]) * (gx - ax[2]) + (ax[2] - ax[1]) * (gy - ay[2])) / d
        w1 = ((ay[2] - ay[0]) * (gx - ax[2]) + (ax[0] - ax[2]) * (gy - ay[2])) / d
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        zz = w0 * az[0] + w1 * az[1] + w2 * az[2]
        sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        better = inside & (zz > sub)
        if not better.any():
            continue
        sub[better] = zz[better]
        tile = img[ymin:ymax + 1, xmin:xmax + 1]
        tile[better] = cols[i]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def main():
    # Z смотрит от лица назад, поэтому камера по +Z видит ЗАДНЮЮ сторону,
    # а лицо показывает поворот на 180°.
    front = trimesh.load(os.path.join(OUT, "front_frame.stl"))
    back = trimesh.load(os.path.join(OUT, "back_shell.stl"))
    shell = [(front, (236, 239, 242)), (back, (176, 196, 210))]

    mock_f = os.path.join(OUT, "mockups.stl")
    with_mock = list(shell)
    if os.path.exists(mock_f):
        with_mock.append((trimesh.load(mock_f), (86, 104, 120)))

    views = {
        "front": (0.0, 180.0, shell, True),
        "back": (0.0, 0.0, shell, False),
        "iso_front": (20.0, 208.0, shell, True),
        "iso_back": (20.0, 26.0, shell, False),
        "assembly": (20.0, 208.0, with_mock, True),
    }
    for name, (elev, azim, sc, mir) in views.items():
        img = render(sc, elev, azim, mirror=mir)
        f = os.path.join(OUT, f"view_{name}.png")
        img.save(f)
        print("записан", os.path.basename(f))


if __name__ == "__main__":
    main()
