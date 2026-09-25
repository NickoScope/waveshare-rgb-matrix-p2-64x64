# -*- coding: utf-8 -*-
"""
Сборка GLTF для просмотрщика. python3 build_gltf.py

Главное — НОРМАЛИ. trimesh кладёт в GLTF только POSITION, если вершинные
нормали не посчитаны до экспорта, а three.js без них рисует любой освещённый
материал чёрным. На прошлом корпусе это стоило получаса поисков: плата и
стойки выглядели чернильными пятнами при правильно назначенных цветах.
"""

import glob
import os

import trimesh

OUT = "out/LEDMX_assembly.json"


def main():
    scene = trimesh.Scene()
    for f in sorted(glob.glob("out/3d_*.stl")):
        name = os.path.basename(f)[3:-4]
        m = trimesh.load(f, force="mesh")
        m.vertex_normals          # посчитать и закэшировать — иначе NORMAL не уйдёт
        scene.add_geometry(m, node_name=name, geom_name=name)
    data = trimesh.exchange.gltf.export_gltf(scene, embed_buffers=True)
    blob = data.get("model.gltf") or list(data.values())[0]
    with open(OUT, "wb") as fh:
        fh.write(blob if isinstance(blob, bytes) else blob.encode())
    import json
    d = json.load(open(OUT))
    no_n = [m["name"] for m in d["meshes"]
            if "NORMAL" not in m["primitives"][0]["attributes"]]
    tri = sum(len(trimesh.load(f, force="mesh").faces)
              for f in glob.glob("out/3d_*.stl"))
    print(f"GLTF: {os.path.getsize(OUT) // 1024} КБ, узлов {len(scene.geometry)}, "
          f"треугольников {tri}")
    print("без нормалей:", no_n or "ни одного")


if __name__ == "__main__":
    main()
