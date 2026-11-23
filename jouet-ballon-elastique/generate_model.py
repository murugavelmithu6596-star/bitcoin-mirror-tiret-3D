#!/usr/bin/env python3
"""
Petit ballon 3×3 cm accroché à un ruban + base.
Dimensions en millimètres. Volume sphère : V = 4/3 π r³.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from stl import mesh as stl_mesh

OUT = Path(__file__).resolve().parent / "models"
OUT.mkdir(parents=True, exist_ok=True)

# Ballon : 3 cm de large × 3 cm de haut → Ø 30 mm, r = 15 mm
BALL_W_MM = 30.0
BALL_H_MM = 30.0
BALL_R = BALL_W_MM / 2.0  # 15 mm
BALL_VOLUME_CM3 = (4.0 / 3.0) * math.pi * (BALL_R / 10.0) ** 3  # r en cm

BASE_R = 12.0
BASE_H = 8.0
RIBBON_W = 6.0   # largeur ruban (mm)
RIBBON_T = 0.6   # épaisseur
RIBBON_LEN = 90.0  # longueur au repos (mm)
ANCHOR = (0.0, 0.0, BASE_H)
BALL_CENTER = (0.0, 0.0, BASE_H + RIBBON_LEN + BALL_R)


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


def ribbon_box(start, end, width=RIBBON_W, thickness=RIBBON_T):
    """Ruban plat (boîte allongée) de start → end, largeur sur X."""
    start = np.array(start, dtype=np.float64)
    end = np.array(end, dtype=np.float64)
    direction = end - start
    length = np.linalg.norm(direction)
    direction /= length
    up = np.array([0.0, 1.0, 0.0]) if abs(direction[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    right = np.cross(direction, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, direction)

    hw, ht = width / 2, thickness / 2
    corners = []
    for s in (0.0, 1.0):
        p = start + direction * (s * length)
        for sx in (-1, 1):
            for sy in (-1, 1):
                corners.append(p + right * (sx * hw) + up * (sy * ht))
    # indices: 0..3 at start, 4..7 at end
    faces = [
        (0, 1, 5), (0, 5, 4),
        (1, 3, 7), (1, 7, 5),
        (3, 2, 6), (3, 6, 7),
        (2, 0, 4), (2, 4, 6),
        (4, 5, 7), (4, 7, 6),
        (0, 2, 3), (0, 3, 1),
    ]
    return np.array(corners, dtype=np.float64), np.array(faces, dtype=np.int32)


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
        mf.write("# Matières jouet — ballon + ruban\n")
        for name, props in materials.items():
            kd = props["Kd"]
            mf.write(f"newmtl {name}\n")
            mf.write(f"Kd {kd[0]:.4f} {kd[1]:.4f} {kd[2]:.4f}\n")
            mf.write(f"Ks {props['Ks'][0]:.4f} {props['Ks'][1]:.4f} {props['Ks'][2]:.4f}\n")
            mf.write(f"Ns {props['Ns']:.1f}\n\n")

    with obj_path.open("w", encoding="utf-8") as of:
        of.write(f"# Ballon {BALL_W_MM:.0f}×{BALL_H_MM:.0f} mm, V={BALL_VOLUME_CM3:.3f} cm³\n")
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
    print(f"Ballon Ø {BALL_W_MM:.0f} mm × {BALL_H_MM:.0f} mm  →  r = {BALL_R:.1f} mm")
    print(f"Volume V = 4/3 π r³ = {BALL_VOLUME_CM3:.3f} cm³  ({BALL_VOLUME_CM3 * 1000:.1f} mm³)")

    base_v, base_f = cylinder(BASE_R, BASE_H, 32, center=(0.0, 0.0, BASE_H / 2))
    ball_v, ball_f = icosphere(BALL_R, 3, center=BALL_CENTER)
    ribbon_end = (BALL_CENTER[0], BALL_CENTER[1], BALL_CENTER[2] - BALL_R)
    ribbon_v, ribbon_f = ribbon_box(ANCHOR, ribbon_end)

    materials = {
        "BaseBois": {"Kd": (0.76, 0.55, 0.32), "Ks": (0.2, 0.15, 0.1), "Ns": 40.0},
        "BallonCaoutchouc": {"Kd": (0.92, 0.28, 0.32), "Ks": (0.35, 0.35, 0.35), "Ns": 80.0},
        "RubanSatin": {"Kd": (0.95, 0.78, 0.35), "Ks": (0.45, 0.4, 0.25), "Ns": 70.0},
    }
    groups = {
        "base": (base_v, base_f, "BaseBois"),
        "ballon": (ball_v, ball_f, "BallonCaoutchouc"),
        "ruban": (ribbon_v, ribbon_f, "RubanSatin"),
    }

    write_obj_mtl(groups, OUT / "ballon_elastique.obj", OUT / "ballon_elastique.mtl", materials)
    # Alias lisible
    write_obj_mtl(groups, OUT / "ballon_ruban.obj", OUT / "ballon_ruban.mtl", materials)

    to_stl(base_v, base_f, OUT / "base.stl")
    to_stl(ball_v, ball_f, OUT / "ballon.stl")
    to_stl(ribbon_v, ribbon_f, OUT / "ruban.stl")
    # Compat anciens noms
    to_stl(ribbon_v, ribbon_f, OUT / "elastique.stl")
    all_v, all_f = merge_parts([(v, f) for v, f, _ in groups.values()])
    to_stl(all_v, all_f, OUT / "ballon_elastique.stl")
    to_stl(all_v, all_f, OUT / "ballon_ruban.stl")

    (OUT.parent / "MATIERES.md").write_text(
        f"""# Ballon 3×3 cm + ruban

## Dimensions & volume

| Grandeur | Valeur |
|----------|--------|
| Largeur | **3 cm** (30 mm) |
| Hauteur | **3 cm** (30 mm) |
| Rayon | 1,5 cm |
| **Volume** | **V = 4/3 π r³ ≈ {BALL_VOLUME_CM3:.2f} cm³** |

Formule : avec \( r = 1{','}5\\,\\mathrm{{cm}} \),
\( V = \\frac{{4}}{{3}}\\pi (1{','}5)^3 = 4{','}5\\pi \\approx {BALL_VOLUME_CM3:.3f}\\,\\mathrm{{cm}}^3 \).

## Matières

| Pièce | Matière | Couleur | Hex |
|-------|---------|---------|-----|
| Base | Bois verni | Brun miel | `#C28C52` |
| Ballon | Caoutchouc / TPE | Rouge corail | `#EB4752` |
| Ruban | Satin / tissu | Or doux | `#F2C759` |

Fichiers : `models/ballon_ruban.obj` (+ `.mtl`), `.stl`.
Simulation : ouvrir `index.html`.
""",
        encoding="utf-8",
    )
    print("OK →", OUT)


if __name__ == "__main__":
    main()
