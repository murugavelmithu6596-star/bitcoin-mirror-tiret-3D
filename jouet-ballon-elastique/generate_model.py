#!/usr/bin/env python3
"""
Petit ballon à la taille d'une main + élastique fin + base.
Pas de ruban. Dimensions en millimètres.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from stl import mesh as stl_mesh

OUT = Path(__file__).resolve().parent / "models"
OUT.mkdir(parents=True, exist_ok=True)

# Ballon ≈ taille d'une main (légèrement plus petit que la paume adulte)
# Ø 28 mm → r = 14 mm  (visible « dans la main » du personnage)
BALL_R = 14.0
BALL_VOLUME_CM3 = (4.0 / 3.0) * math.pi * (BALL_R / 10.0) ** 3

BASE_R = 10.0
BASE_H = 6.0
# Élastique fin, proportionné au ballon
ELASTIC_R = 0.9  # mm
ELASTIC_LEN = 55.0  # mm au repos
ANCHOR = (0.0, 0.0, BASE_H)
BALL_CENTER = (0.0, 0.0, BASE_H + ELASTIC_LEN + BALL_R)


def icosphere(radius: float, subdivisions: int = 3, center=(0.0, 0.0, 0.0)):
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = [
        (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
        (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
        (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
    ]
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]

    def mid(a, b, cache, verts_list):
        key = tuple(sorted((a, b)))
        if key in cache:
            return cache[key]
        va, vb = verts_list[a], verts_list[b]
        m = ((va[0] + vb[0]) / 2, (va[1] + vb[1]) / 2, (va[2] + vb[2]) / 2)
        cache[key] = len(verts_list)
        verts_list.append(m)
        return cache[key]

    for _ in range(subdivisions):
        cache = {}
        new_faces = []
        for i, j, k in faces:
            a = mid(i, j, cache, verts)
            b = mid(j, k, cache, verts)
            c = mid(k, i, cache, verts)
            new_faces.extend([(i, a, c), (j, b, a), (k, c, b), (a, b, c)])
        faces = new_faces

    v = np.array(verts, dtype=np.float64)
    v = (v / np.linalg.norm(v, axis=1, keepdims=True)) * radius
    v += np.array(center, dtype=np.float64)
    return v, np.array(faces, dtype=np.int32)


def cylinder(radius, height, segments=24, center=(0.0, 0.0, 0.0)):
    verts, faces = [], []
    half = height / 2.0
    for z in (-half, half):
        for i in range(segments):
            a = 2 * math.pi * i / segments
            verts.append((radius * math.cos(a), radius * math.sin(a), z))
    top_c, bot_c = len(verts), len(verts) + 1
    verts.append((0.0, 0.0, half))
    verts.append((0.0, 0.0, -half))
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j))
        faces.append((i, segments + j, segments + i))
        faces.append((segments + i, segments + j, top_c))
        faces.append((j, i, bot_c))
    v = np.array(verts, dtype=np.float64) + np.array(center, dtype=np.float64)
    return v, np.array(faces, dtype=np.int32)


def elastic_tube(start, end, radius=ELASTIC_R, segments=8, rings=20):
    start = np.array(start, dtype=np.float64)
    end = np.array(end, dtype=np.float64)
    direction = end - start
    length = float(np.linalg.norm(direction))
    direction /= length
    up = np.array([0.0, 0.0, 1.0]) if abs(direction[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    right = np.cross(direction, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, direction)

    verts, faces = [], []
    for i in range(rings + 1):
        t = i / rings
        p = start + direction * (t * length)
        for j in range(segments):
            a = 2 * math.pi * j / segments
            verts.append(p + (right * math.cos(a) + up * math.sin(a)) * radius)
    for i in range(rings):
        for j in range(segments):
            j2 = (j + 1) % segments
            a = i * segments + j
            b = i * segments + j2
            c = (i + 1) * segments + j2
            d = (i + 1) * segments + j
            faces.append((a, b, c))
            faces.append((a, c, d))
    return np.array(verts, dtype=np.float64), np.array(faces, dtype=np.int32)


def merge_parts(parts):
    all_v, all_f, offset = [], [], 0
    for v, f in parts:
        all_v.append(v)
        all_f.append(f + offset)
        offset += len(v)
    return np.vstack(all_v), np.vstack(all_f)


def to_stl(verts, faces, path: Path):
    data = np.zeros(len(faces), dtype=stl_mesh.Mesh.dtype)
    for i, (a, b, c) in enumerate(faces):
        data["vectors"][i] = np.array([verts[a], verts[b], verts[c]])
    stl_mesh.Mesh(data, remove_empty_areas=False).save(str(path))


def write_obj_mtl(groups, obj_path: Path, mtl_path: Path, materials):
    with mtl_path.open("w", encoding="utf-8") as mf:
        mf.write("# Matières — ballon main + élastique fin\n")
        for name, props in materials.items():
            kd = props["Kd"]
            mf.write(f"newmtl {name}\n")
            mf.write(f"Kd {kd[0]:.4f} {kd[1]:.4f} {kd[2]:.4f}\n")
            mf.write(f"Ks {props['Ks'][0]:.4f} {props['Ks'][1]:.4f} {props['Ks'][2]:.4f}\n")
            mf.write(f"Ns {props['Ns']:.1f}\n\n")

    with obj_path.open("w", encoding="utf-8") as of:
        of.write(f"# Ballon r={BALL_R} mm (taille main), V={BALL_VOLUME_CM3:.3f} cm3 — sans ruban\n")
        of.write(f"mtllib {mtl_path.name}\n")
        offset = 0
        for gname, (verts, faces, mat) in groups.items():
            of.write(f"o {gname}\nusemtl {mat}\n")
            for x, y, z in verts:
                of.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
            for a, b, c in faces:
                of.write(f"f {a + 1 + offset} {b + 1 + offset} {c + 1 + offset}\n")
            offset += len(verts)


def main():
    print(f"Ballon r={BALL_R} mm (taille main), V={BALL_VOLUME_CM3:.3f} cm³")
    print(f"Élastique Ø {ELASTIC_R * 2:.1f} mm, L={ELASTIC_LEN:.0f} mm — pas de ruban")

    base_v, base_f = cylinder(BASE_R, BASE_H, 28, center=(0.0, 0.0, BASE_H / 2))
    ball_v, ball_f = icosphere(BALL_R, 3, center=BALL_CENTER)
    elastic_end = (BALL_CENTER[0], BALL_CENTER[1], BALL_CENTER[2] - BALL_R)
    elastic_v, elastic_f = elastic_tube(ANCHOR, elastic_end)

    materials = {
        "BaseBois": {"Kd": (0.76, 0.55, 0.32), "Ks": (0.2, 0.15, 0.1), "Ns": 40.0},
        "BallonCaoutchouc": {"Kd": (0.92, 0.28, 0.32), "Ks": (0.35, 0.35, 0.35), "Ns": 80.0},
        "ElastiqueLatex": {"Kd": (0.92, 0.86, 0.72), "Ks": (0.3, 0.3, 0.25), "Ns": 50.0},
    }
    groups = {
        "base": (base_v, base_f, "BaseBois"),
        "ballon": (ball_v, ball_f, "BallonCaoutchouc"),
        "elastique": (elastic_v, elastic_f, "ElastiqueLatex"),
    }

    write_obj_mtl(groups, OUT / "ballon_elastique.obj", OUT / "ballon_elastique.mtl", materials)

    to_stl(base_v, base_f, OUT / "base.stl")
    to_stl(ball_v, ball_f, OUT / "ballon.stl")
    to_stl(elastic_v, elastic_f, OUT / "elastique.stl")
    all_v, all_f = merge_parts([(v, f) for v, f, _ in groups.values()])
    to_stl(all_v, all_f, OUT / "ballon_elastique.stl")

    # Supprimer vestiges ruban
    for obsolete in ("ruban.stl", "ballon_ruban.obj", "ballon_ruban.mtl", "ballon_ruban.stl"):
        p = OUT / obsolete
        if p.exists():
            p.unlink()
            print("supprimé", p.name)

    (OUT.parent / "MATIERES.md").write_text(
        f"""# Ballon taille main + élastique fin

**Pas de ruban.** Le personnage tient le ballon à la main ; l’élastique le rappelle vers la main.

| Grandeur | Valeur |
|----------|--------|
| Rayon ballon | {BALL_R:.0f} mm (≈ taille main) |
| Volume | V ≈ {BALL_VOLUME_CM3:.2f} cm³ |
| Élastique | Ø {ELASTIC_R * 2:.1f} mm, L repos {ELASTIC_LEN:.0f} mm |

| Pièce | Couleur | Hex |
|-------|---------|-----|
| Base | Brun miel | `#C28C52` |
| Ballon | Rouge corail | `#EB4752` |
| Élastique | Latex crème | `#EBD9B8` |
""",
        encoding="utf-8",
    )
    print("OK →", OUT)


if __name__ == "__main__":
    main()
