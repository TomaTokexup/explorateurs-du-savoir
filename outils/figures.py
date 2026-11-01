# Dessine des figures géométriques au format SVG (images vectorielles, nettes à toutes les tailles)
# Les figures sont calculées par Python : elles sont donc toujours exactes,
# contrairement à une image générée par une IA.
import math
from pathlib import Path

ENCRE = "#23305a"      # couleur des traits (encre bleue du site)
COULEUR = "#2f6fdb"    # couleur des marques (bleu du cahier de maths)


def dessiner_angle(mesure):
    """Renvoie le code SVG d'un angle de `mesure` degrés (entre 1 et 180)."""
    cx, cy = 120, 130          # le sommet de l'angle
    longueur = 100             # longueur des deux côtés
    rayon = 32                 # rayon de l'arc qui marque l'angle

    rad = math.radians(mesure)
    # 1er côté : horizontal, vers la droite
    x1, y1 = cx + longueur, cy
    # 2e côté : tourné de `mesure` degrés vers le haut
    # (en SVG, l'axe y descend : on SOUSTRAIT pour monter)
    x2 = cx + longueur * math.cos(rad)
    y2 = cy - longueur * math.sin(rad)

    # Marque de l'angle : petit carré si l'angle est droit, arc sinon
    if mesure == 90:
        c = 22
        marque = (f'<path d="M {cx + c} {cy} L {cx + c} {cy - c} L {cx} {cy - c}" '
                  f'fill="none" stroke="{COULEUR}" stroke-width="3"/>')
    else:
        ax1, ay1 = cx + rayon, cy
        ax2 = cx + rayon * math.cos(rad)
        ay2 = cy - rayon * math.sin(rad)
        marque = (f'<path d="M {ax1:.1f} {ay1:.1f} A {rayon} {rayon} 0 0 0 {ax2:.1f} {ay2:.1f}" '
                  f'fill="none" stroke="{COULEUR}" stroke-width="3"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 150" width="240" height="150">
  <line x1="{cx}" y1="{cy}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{ENCRE}" stroke-width="4" stroke-linecap="round"/>
  <line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{ENCRE}" stroke-width="4" stroke-linecap="round"/>
  {marque}
  <circle cx="{cx}" cy="{cy}" r="4" fill="{ENCRE}"/>
</svg>
'''
def dessiner_polygone(nombre_cotes):
    """Renvoie le code SVG d'un polygone régulier à `nombre_cotes` côtés."""
    cx, cy = 120, 105     # centre du cercle
    rayon = 85
    depart = math.radians(90 + 180 / nombre_cotes)

    points = []
    for k in range(nombre_cotes):
        angle = depart + k * 2 * math.pi / nombre_cotes
        x = cx + rayon * math.cos(angle)
        y = cy + rayon * math.sin(angle)
        points.append(f"{x:.1f},{y:.1f}")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 210" width="240" height="210">
  <polygon points="{ ' '.join(points) }" fill="#eaf1fc" stroke="{ENCRE}" stroke-width="4" stroke-linejoin="round"/>
</svg>
'''

def enregistrer(svg, chemin):
  """Écrit le code SVG dans un fichier, en créant les dossiers si besoin."""
  # 1. transformer chemin en Path
  chemin = Path(chemin)
  # 2. créer le dossier parent s'il n'existe pas : .parent.mkdir(parents=True, exist_ok=True)
  chemin.parent.mkdir(parents=True, exist_ok=True)
  # 3. écrire le texte svg dans le fichier (open en "w", encoding="utf-8")
  with open(chemin, "w", encoding="utf-8") as fichier:
    fichier.write(svg)
  # 4. afficher "Figure enregistrée : <chemin>"
  print(f"Figure enregistrée : {chemin}")

if __name__ == "__main__":
  enregistrer(dessiner_angle(120), "images/p4/maths/angle-120.svg")
  for n in (3, 4, 5, 6, 8):
    enregistrer(dessiner_polygone(n), f"images/p4/maths/polygone-{n}.svg")