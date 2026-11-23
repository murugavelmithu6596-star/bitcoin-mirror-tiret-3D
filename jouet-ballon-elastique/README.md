# Jouet ballon à élastique

Petit ballon rebondissant relié par un élastique à une base.

## Fichiers

- `models/ballon_elastique.obj` + `.mtl` — modèle coloré
- `models/ballon_elastique.stl` — assemblage monochrome
- `models/{base,ballon,elastique}.stl` — pièces
- `index.html` — simulation simple (ballon, élastique, paroi, 1–2 rebonds)
- `MATIERES.md` — couleurs / matières

## Lancer la simulation

```bash
cd jouet-ballon-elastique && python3 -m http.server 8765
# ouvrir http://127.0.0.1:8765/
```

## Régénérer les meshes

```bash
python3 generate_model.py
```
