# Ballon 3 cm + ruban + personnage

Petit ballon **3 cm × 3 cm** accroché à un **ruban**, tiré par un **personnage** simple puis relâché vers une paroi.

## Volume du ballon

- Largeur = hauteur = **3 cm** → sphère de rayon **r = 1,5 cm**
- **V = 4/3 π r³ = 4/3 π (1,5)³ = 4,5 π ≈ 14,14 cm³**

## Animation

1. Le personnage s’approche et attrape le ruban  
2. Il tend le ruban  
3. Il lâche → le ballon part et rebondit sur la paroi  

## Lancer

```bash
cd jouet-ballon-elastique && python3 -m http.server 8765 --bind 127.0.0.1
```

Ouvrir : http://127.0.0.1:8765/

## Fichiers

- `models/ballon_ruban.obj` (+ `.mtl` / `.stl`) — ballon, ruban, base  
- `index.html` — scène Three.js + personnage + simulation  
- `generate_model.py` — régénération des meshes  
