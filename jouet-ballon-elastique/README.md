# Ballon taille main — tirer, paroi, retour main

Personnage qui **tient le ballon à la main** (pas de ruban), tire, lâche.
Le ballon **rebondit sur la paroi**, puis l’élastique fin le **ramène vers la main**.

## Échelle

- Ballon ≈ **taille de la main** (pas plus gros)
- Élastique **fin**, ancré à la **main**
- Volume mesh export ≈ **11,5 cm³** (r = 14 mm)

## Animation

1. Tirer (prise en main)  
2. Rebond sur la paroi  
3. Retour vers la main  

## Lancer

```bash
cd jouet-ballon-elastique && python3 -m http.server 8765 --bind 127.0.0.1
```

http://127.0.0.1:8765/
