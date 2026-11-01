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

def dessiner_horloge(heures, minutes):
    """Renvoie le code SVG d'une horloge à aiguilles indiquant heures:minutes.
    heures : de 1 à 12 ; minutes : de 0 à 55, multiple de 5."""
    cx, cy = 110, 110
    rayon = 92

    # Le cadran et ses 12 graduations (une toutes les 30°)
    elements = [f'<circle cx="{cx}" cy="{cy}" r="{rayon}" fill="white" stroke="{ENCRE}" stroke-width="5"/>']
    for h in range(1, 13):
        angle = math.radians(h * 30 - 90)        # en trigonométrie 0° = 3 heures, d'où le -90° pour partir de midi
        x1 = cx + (rayon - 12) * math.cos(angle)
        y1 = cy + (rayon - 12) * math.sin(angle)
        x2 = cx + (rayon - 4) * math.cos(angle)
        y2 = cy + (rayon - 4) * math.sin(angle)
        elements.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{ENCRE}" stroke-width="4" stroke-linecap="round"/>')
        # Les chiffres
        xt = cx + (rayon - 28) * math.cos(angle)
        yt = cy + (rayon - 28) * math.sin(angle)
        elements.append(f'<text x="{xt:.1f}" y="{yt:.1f}" font-family="Arial, sans-serif" font-size="17" '
                        f'font-weight="bold" fill="{ENCRE}" text-anchor="middle" dominant-baseline="central">{h}</text>')

    # La petite aiguille avance aussi avec les minutes (à 2 h 30, elle est entre le 2 et le 3)
    angle_heures = math.radians((heures % 12) * 30 + minutes * 0.5 - 90)
    angle_minutes = math.radians(minutes * 6 - 90)
    for angle, longueur, epaisseur, couleur in ((angle_heures, 38, 8, ENCRE), (angle_minutes, 56, 5, COULEUR)):
        x = cx + longueur * math.cos(angle)
        y = cy + longueur * math.sin(angle)
        elements.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" '
                        f'stroke="{couleur}" stroke-width="{epaisseur}" stroke-linecap="round"/>')
    elements.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{ENCRE}"/>')

    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220" width="220" height="220">
  {contenu}
</svg>
'''


def dessiner_repere(x, y, nom="A"):
    """Renvoie le code SVG d'un quadrillage de 0 à 6 avec un point de coordonnées (x ; y)."""
    taille = 6                 # le quadrillage va de 0 à 6 sur chaque axe
    pas = 32                   # taille d'une case en pixels
    ox, oy = 40, 230           # position de l'origine (0 ; 0) — l'axe y du SVG descend

    elements = []
    # Le quadrillage et les graduations
    for k in range(taille + 1):
        elements.append(f'<line x1="{ox + k * pas}" y1="{oy}" x2="{ox + k * pas}" y2="{oy - taille * pas}" '
                        f'stroke="#d4e3f3" stroke-width="2"/>')
        elements.append(f'<line x1="{ox}" y1="{oy - k * pas}" x2="{ox + taille * pas}" y2="{oy - k * pas}" '
                        f'stroke="#d4e3f3" stroke-width="2"/>')
        elements.append(f'<text x="{ox + k * pas}" y="{oy + 20}" font-family="Arial, sans-serif" font-size="14" '
                        f'fill="{ENCRE}" text-anchor="middle">{k}</text>')
        if k > 0:
            elements.append(f'<text x="{ox - 14}" y="{oy - k * pas}" font-family="Arial, sans-serif" font-size="14" '
                            f'fill="{ENCRE}" text-anchor="middle" dominant-baseline="central">{k}</text>')
    # Les axes, avec leur nom
    elements.append(f'<line x1="{ox}" y1="{oy}" x2="{ox + taille * pas + 14}" y2="{oy}" stroke="{ENCRE}" stroke-width="3"/>')
    elements.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy - taille * pas - 14}" stroke="{ENCRE}" stroke-width="3"/>')
    elements.append(f'<text x="{ox + taille * pas + 22}" y="{oy}" font-family="Arial, sans-serif" font-size="16" '
                    f'font-style="italic" fill="{ENCRE}" dominant-baseline="central">x</text>')
    elements.append(f'<text x="{ox}" y="{oy - taille * pas - 24}" font-family="Arial, sans-serif" font-size="16" '
                    f'font-style="italic" fill="{ENCRE}" text-anchor="middle">y</text>')
    # Le point
    px, py = ox + x * pas, oy - y * pas
    elements.append(f'<circle cx="{px}" cy="{py}" r="7" fill="{COULEUR}"/>')
    elements.append(f'<text x="{px + 10}" y="{py - 10}" font-family="Arial, sans-serif" font-size="18" '
                    f'font-weight="bold" fill="{COULEUR}">{nom}</text>')

    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 260" width="280" height="260">
  {contenu}
</svg>
'''


# Les 8 directions de la rose des vents et leur angle (0° = nord, dans le sens des aiguilles d'une montre)
DIRECTIONS = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SO": 225, "O": 270, "NO": 315}


def dessiner_rose(direction):
    """Renvoie le code SVG d'une rose des vents : seul le nord est écrit,
    et une flèche rouge montre la `direction` (N, NE, E, SE, S, SO, O ou NO)."""
    cx, cy = 110, 115
    elements = []
    # Les 8 branches, sans leur nom (sauf le nord) : c'est à l'élève de les retrouver
    for nom, degres in DIRECTIONS.items():
        angle = math.radians(degres - 90)       # -90° : le nord est en haut
        longueur = 80 if len(nom) == 1 else 55  # branches principales plus longues
        x = cx + longueur * math.cos(angle)
        y = cy + longueur * math.sin(angle)
        elements.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" '
                        f'stroke="{ENCRE}" stroke-width="{3 if len(nom) == 1 else 2}" stroke-linecap="round"/>')
    elements.append(f'<text x="{cx}" y="{cy - 92}" font-family="Arial, sans-serif" font-size="20" '
                    f'font-weight="bold" fill="{ENCRE}" text-anchor="middle">N</text>')

    # La flèche rouge de la direction demandée
    angle = math.radians(DIRECTIONS[direction] - 90)
    longueur = 80 if len(direction) == 1 else 55
    pointe_x = cx + longueur * math.cos(angle)
    pointe_y = cy + longueur * math.sin(angle)
    tete = []                                   # les deux autres sommets du triangle de la pointe
    for decalage in (150, -150):
        a = angle + math.radians(decalage)
        tete.append(f"{pointe_x + 16 * math.cos(a):.1f},{pointe_y + 16 * math.sin(a):.1f}")
    elements.append(f'<line x1="{cx}" y1="{cy}" x2="{pointe_x:.1f}" y2="{pointe_y:.1f}" '
                    f'stroke="#e2574c" stroke-width="6" stroke-linecap="round"/>')
    elements.append(f'<polygon points="{pointe_x:.1f},{pointe_y:.1f} {tete[0]} {tete[1]}" fill="#e2574c"/>')
    elements.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{ENCRE}"/>')

    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220" width="220" height="220">
  {contenu}
</svg>
'''


def dessiner_rectangle(longueur, largeur, unite="cm"):
    """Renvoie le code SVG d'un rectangle avec ses deux dimensions écrites (ex. 6 cm et 4 cm).
    Le dessin respecte les proportions : un rectangle allongé paraît allongé."""
    # Échelle choisie pour que le dessin tienne dans 180 × 120 pixels
    echelle = min(180 / longueur, 120 / largeur)
    w, h = longueur * echelle, largeur * echelle
    x0, y0 = (240 - w) / 2, 20
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 {h + 60:.0f}" width="280" height="{h + 60:.0f}">
  <rect x="{x0:.1f}" y="{y0}" width="{w:.1f}" height="{h:.1f}" fill="#eaf1fc" stroke="{ENCRE}" stroke-width="4"/>
  <text x="{x0 + w / 2:.1f}" y="{y0 + h + 26:.1f}" font-family="Arial, sans-serif" font-size="17" font-weight="bold" fill="{ENCRE}" text-anchor="middle">{longueur} {unite}</text>
  <text x="{x0 + w + 8:.1f}" y="{y0 + h / 2:.1f}" font-family="Arial, sans-serif" font-size="17" font-weight="bold" fill="{ENCRE}" dominant-baseline="central">{largeur} {unite}</text>
</svg>
'''


def enregistrer(svg, chemin):
    """Écrit le code SVG dans un fichier, en créant les dossiers si besoin."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write(svg)
    print(f"Figure enregistrée : {chemin}")


if __name__ == "__main__":
    # Démonstration : un exemple de chaque figure dans images/exemples/ (à ouvrir dans le navigateur)
    enregistrer(dessiner_angle(120), "images/exemples/angle-120.svg")
    for n in (3, 4, 5, 6, 8):
        enregistrer(dessiner_polygone(n), f"images/exemples/polygone-{n}.svg")
    enregistrer(dessiner_horloge(2, 30), "images/exemples/horloge-2h30.svg")
    enregistrer(dessiner_horloge(9, 45), "images/exemples/horloge-9h45.svg")
    enregistrer(dessiner_repere(4, 3), "images/exemples/repere-4-3.svg")
    enregistrer(dessiner_rose("NE"), "images/exemples/rose-ne.svg")
    enregistrer(dessiner_rose("O"), "images/exemples/rose-o.svg")
    enregistrer(dessiner_rectangle(6, 4), "images/exemples/rectangle-6x4cm.svg")
    enregistrer(dessiner_rectangle(12, 3, "m"), "images/exemples/rectangle-12x3m.svg")
