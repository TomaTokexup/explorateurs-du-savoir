# Dessine des figures géométriques au format SVG (images vectorielles, nettes à toutes les tailles)
# Les figures sont calculées par Python : elles sont donc toujours exactes,
# contrairement à une image générée par une IA.
import html
import math
import random
import re
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


# --- Figures pour le traitement des données ---

# Couleurs des catégories (bien distinctes, lisibles aussi en cas de daltonisme léger)
PALETTE = ["#2f6fdb", "#e2574c", "#2e9e6a", "#d9a514", "#7a4cc2", "#1c96a1"]


def _texte(x, y, contenu, taille=14, ancre="middle", gras=False, couleur=ENCRE, extra=""):
    """Petit outil : un élément <text> SVG, avec le contenu protégé (les caractères & < > sont échappés)."""
    poids = ' font-weight="bold"' if gras else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" font-size="{taille}"{poids} '
            f'fill="{couleur}" text-anchor="{ancre}" {extra}>{html.escape(str(contenu))}</text>')


def _pas_graduation(maximum):
    """Choisit un pas de graduation « rond » (1, 2, 5, 10, 20…) pour avoir au plus 10 graduations.
    Des graduations assez serrées permettent à l'élève de LIRE une valeur exacte sur le graphique."""
    for pas in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if maximum / pas <= 10:
            return pas
    return 1000


def _axes(etiquettes, maximum, titre, gauche, bas, largeur, hauteur):
    """Dessine le titre, l'axe vertical gradué et la ligne de base communs aux barres et aux courbes."""
    pas = _pas_graduation(maximum)
    haut_axe = math.ceil(maximum / pas) * pas          # la graduation la plus haute, juste au-dessus du maximum
    elements = [_texte(gauche + largeur / 2, 22, titre, taille=16, gras=True)]
    valeur = 0
    while valeur <= haut_axe:
        y = bas - valeur / haut_axe * hauteur
        elements.append(f'<line x1="{gauche}" y1="{y:.1f}" x2="{gauche + largeur}" y2="{y:.1f}" stroke="#d4e3f3" stroke-width="2"/>')
        elements.append(_texte(gauche - 8, y, valeur, taille=13, ancre="end", extra='dominant-baseline="central"'))
        valeur += pas
    elements.append(f'<line x1="{gauche}" y1="{bas}" x2="{gauche + largeur}" y2="{bas}" stroke="{ENCRE}" stroke-width="3"/>')
    elements.append(f'<line x1="{gauche}" y1="{bas}" x2="{gauche}" y2="{bas - hauteur - 8}" stroke="{ENCRE}" stroke-width="3"/>')
    return elements, haut_axe


def dessiner_barres(etiquettes, valeurs, titre=""):
    """Renvoie le code SVG d'un diagramme en barres (2 à 6 catégories)."""
    gauche, bas, largeur, hauteur = 50, 230, 300, 180
    elements, haut_axe = _axes(etiquettes, max(valeurs), titre, gauche, bas, largeur, hauteur)
    case = largeur / len(valeurs)                       # place disponible pour chaque barre
    for i, (etiquette, valeur) in enumerate(zip(etiquettes, valeurs)):
        h = valeur / haut_axe * hauteur
        x = gauche + i * case + case * 0.2
        elements.append(f'<rect x="{x:.1f}" y="{bas - h:.1f}" width="{case * 0.6:.1f}" height="{h:.1f}" '
                        f'fill="{PALETTE[i % len(PALETTE)]}"/>')
        elements.append(_texte(gauche + (i + 0.5) * case, bas + 20, etiquette, taille=13))
    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 255" width="370" height="255">
  {contenu}
</svg>
'''


def dessiner_courbe(etiquettes, valeurs, titre=""):
    """Renvoie le code SVG d'un graphique en ligne (une valeur par étiquette, ex. une par mois)."""
    gauche, bas, largeur, hauteur = 50, 230, 300, 180
    elements, haut_axe = _axes(etiquettes, max(valeurs), titre, gauche, bas, largeur, hauteur)
    case = largeur / len(valeurs)
    points = []
    for i, (etiquette, valeur) in enumerate(zip(etiquettes, valeurs)):
        x = gauche + (i + 0.5) * case
        y = bas - valeur / haut_axe * hauteur
        points.append((x, y))
        elements.append(_texte(x, bas + 20, etiquette, taille=13))
    ligne = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    elements.append(f'<polyline points="{ligne}" fill="none" stroke="{COULEUR}" stroke-width="4" stroke-linejoin="round"/>')
    for x, y in points:
        elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="white" stroke="{COULEUR}" stroke-width="3"/>')
    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 255" width="370" height="255">
  {contenu}
</svg>
'''


def dessiner_camembert(etiquettes, valeurs, titre=""):
    """Renvoie le code SVG d'un diagramme circulaire, avec une légende.
    Chaque part est proportionnelle à sa valeur (les valeurs ne sont pas écrites sur le dessin)."""
    cx, cy, rayon = 105, 135, 90
    total = sum(valeurs)
    elements = [_texte(185, 22, titre, taille=16, gras=True)]
    debut = -90                                          # on commence en haut (midi), dans le sens des aiguilles d'une montre
    for i, (etiquette, valeur) in enumerate(zip(etiquettes, valeurs)):
        couleur = PALETTE[i % len(PALETTE)]
        angle = valeur / total * 360
        a1, a2 = math.radians(debut), math.radians(debut + angle)
        x1, y1 = cx + rayon * math.cos(a1), cy + rayon * math.sin(a1)
        x2, y2 = cx + rayon * math.cos(a2), cy + rayon * math.sin(a2)
        grand_arc = 1 if angle > 180 else 0
        if angle >= 359.99:                              # une seule part = disque entier
            elements.append(f'<circle cx="{cx}" cy="{cy}" r="{rayon}" fill="{couleur}" stroke="white" stroke-width="3"/>')
        else:
            elements.append(f'<path d="M {cx} {cy} L {x1:.1f} {y1:.1f} A {rayon} {rayon} 0 {grand_arc} 1 {x2:.1f} {y2:.1f} Z" '
                            f'fill="{couleur}" stroke="white" stroke-width="3"/>')
        # Légende
        ly = 70 + i * 28
        elements.append(f'<rect x="215" y="{ly - 9}" width="18" height="18" rx="3" fill="{couleur}"/>')
        elements.append(_texte(241, ly, etiquette, taille=14, ancre="start", extra='dominant-baseline="central"'))
        debut += angle
    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 240" width="370" height="240">
  {contenu}
</svg>
'''


def dessiner_billes(rouges=0, bleues=0, vertes=0, jaunes=0):
    """Renvoie le code SVG d'un sac (vu de face) contenant des billes de couleur,
    pour les questions de probabilité (« est-il probable de tirer une bille rouge ? »)."""
    couleurs = (["#e2574c"] * rouges + ["#2f6fdb"] * bleues + ["#2e9e6a"] * vertes + ["#d9a514"] * jaunes)
    # On mélange les billes, comme dans un vrai sac. La « graine » fixe le hasard :
    # le même contenu donne toujours le même dessin (et donc le même fichier).
    random.Random(f"{rouges}-{bleues}-{vertes}-{jaunes}").shuffle(couleurs)
    elements = [
        # Le sac : un rectangle arrondi ouvert en haut
        f'<path d="M 30 50 L 30 205 Q 30 225 50 225 L 230 225 Q 250 225 250 205 L 250 50" '
        f'fill="#fdfdfb" stroke="{ENCRE}" stroke-width="4" stroke-linejoin="round"/>',
    ]
    # Les billes, rangées par lignes de 6, en partant du fond du sac
    for i, couleur in enumerate(couleurs):
        colonne, ligne = i % 6, i // 6
        x = 58 + colonne * 33
        y = 198 - ligne * 33
        elements.append(f'<circle cx="{x}" cy="{y}" r="14" fill="{couleur}" stroke="{ENCRE}" stroke-width="2"/>')
    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 240" width="280" height="240">
  {contenu}
</svg>
'''


def dessiner_venn(titre_a, titre_b, seulement_a, commun, seulement_b):
    """Renvoie le code SVG d'un diagramme de Venn à deux cercles qui se chevauchent.
    titre_a, titre_b : le nom de chaque groupe (ex. « Aime le sport ») ;
    seulement_a, commun, seulement_b : les éléments (ex. des prénoms) placés dans chaque zone."""
    cx_a, cx_b, cy, rayon = 135, 235, 135, 95
    elements = [
        f'<circle cx="{cx_a}" cy="{cy}" r="{rayon}" fill="{PALETTE[0]}" fill-opacity="0.18" stroke="{PALETTE[0]}" stroke-width="4"/>',
        f'<circle cx="{cx_b}" cy="{cy}" r="{rayon}" fill="{PALETTE[1]}" fill-opacity="0.18" stroke="{PALETTE[1]}" stroke-width="4"/>',
        _texte(cx_a - 25, 26, titre_a, taille=15, gras=True, couleur=PALETTE[0]),
        _texte(cx_b + 25, 26, titre_b, taille=15, gras=True, couleur=PALETTE[1]),
    ]
    # Chaque zone a son centre horizontal ; les éléments s'y empilent verticalement
    for x, liste in ((cx_a - 45, seulement_a), ((cx_a + cx_b) / 2, commun), (cx_b + 45, seulement_b)):
        depart = cy - (len(liste) - 1) * 12
        for k, element in enumerate(liste):
            elements.append(_texte(x, depart + k * 24, element, taille=15, extra='dominant-baseline="central"'))
    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 245" width="370" height="245">
  {contenu}
</svg>
'''


# --- Circuits électriques (Découverte du monde) ---
# Symboles normalisés utilisés à l'école : pile (un grand trait fin « + » et un petit trait épais « − »),
# lampe (cercle barré d'une croix), moteur (cercle avec un M), interrupteur ouvert ou fermé.
# Le dessin ne montre JAMAIS si la lampe brille : c'est à l'élève de le prévoir.

COMPOSANTS = {
    "pile": "pile",
    "lampe": "lampe",
    "moteur": "moteur",
    "interrupteur-ouvert": "interrupteur",
    "interrupteur-ferme": "interrupteur",
    "coupure": "",          # fil débranché : deux bouts de fil qui ne se touchent pas
    "objet": "",            # objet à tester (conducteur ou isolant) : son nom est donné à part
}

# Les 4 emplacements du circuit, dans le sens des aiguilles d'une montre :
# (centre x, centre y, rotation en degrés). Les composants sont dessinés à l'horizontale, puis tournés.
EMPLACEMENTS = [(200, 50, 0), (330, 140, 90), (200, 230, 180), (70, 140, 270)]


def _tourner(x, y, angle):
    """Coordonnées d'un point (x, y) après une rotation de `angle` degrés autour de (0, 0)."""
    a = math.radians(angle)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def _symbole(nom):
    """Le symbole d'un composant, dessiné à l'horizontale autour du point (0, 0)."""
    trait = f'stroke="{ENCRE}" stroke-width="4" stroke-linecap="round"'
    # Un rectangle blanc efface le fil à l'endroit du composant
    cache = '<rect x="-30" y="-6" width="60" height="12" fill="white"/>'
    if nom == "pile":
        return (cache + f'<line x1="-30" y1="0" x2="-6" y2="0" {trait}/><line x1="6" y1="0" x2="30" y2="0" {trait}/>'
                f'<line x1="-6" y1="-22" x2="-6" y2="22" stroke="{ENCRE}" stroke-width="3"/>'
                f'<line x1="6" y1="-11" x2="6" y2="11" stroke="{ENCRE}" stroke-width="9"/>')
    if nom == "lampe":
        d = 13 / math.sqrt(2) * 1.4
        return (f'<circle cx="0" cy="0" r="18" fill="white" {trait}/>'
                f'<line x1="{-d:.1f}" y1="{-d:.1f}" x2="{d:.1f}" y2="{d:.1f}" {trait}/>'
                f'<line x1="{-d:.1f}" y1="{d:.1f}" x2="{d:.1f}" y2="{-d:.1f}" {trait}/>')
    if nom == "moteur":
        return f'<circle cx="0" cy="0" r="18" fill="white" {trait}/>'   # le « M » est écrit à part, sans rotation
    if nom == "interrupteur-ouvert":
        return (cache + f'<line x1="-30" y1="0" x2="-20" y2="0" {trait}/><line x1="20" y1="0" x2="30" y2="0" {trait}/>'
                f'<line x1="-20" y1="0" x2="16" y2="-20" {trait}/>'
                f'<circle cx="-20" cy="0" r="4" fill="{ENCRE}"/><circle cx="20" cy="0" r="4" fill="{ENCRE}"/>')
    if nom == "interrupteur-ferme":
        return (f'<circle cx="-20" cy="0" r="4" fill="{ENCRE}"/><circle cx="20" cy="0" r="4" fill="{ENCRE}"/>')
    if nom == "coupure":
        return (cache + f'<line x1="-30" y1="0" x2="-16" y2="0" {trait}/><line x1="16" y1="0" x2="30" y2="0" {trait}/>'
                f'<circle cx="-16" cy="0" r="4" fill="{ENCRE}"/><circle cx="16" cy="0" r="4" fill="{ENCRE}"/>')
    if nom == "objet":
        return (cache + f'<line x1="-30" y1="0" x2="-24" y2="0" {trait}/><line x1="24" y1="0" x2="30" y2="0" {trait}/>'
                f'<rect x="-24" y="-11" width="48" height="22" rx="6" fill="#fff6d6" stroke="{ENCRE}" stroke-width="3"/>')
    raise ValueError(f"composant inconnu : {nom!r}")


def dessiner_circuit(composants, court_circuit=False, objet=""):
    """Renvoie le code SVG d'un circuit en boucle avec 1 à 4 composants (voir COMPOSANTS),
    placés dans l'ordre : en haut, à droite, en bas, à gauche (un emplacement vide = simple fil).
    court_circuit=True : un fil relie directement les deux bornes de la première lampe.
    objet : le nom de l'objet à tester, écrit sous son symbole (« clé en fer », « gomme »...)."""
    elements = [f'<rect x="70" y="50" width="260" height="180" rx="8" fill="none" stroke="{ENCRE}" stroke-width="4"/>']
    premiere_lampe = True
    for nom, (cx, cy, angle) in zip(composants, EMPLACEMENTS):
        groupe = _symbole(nom)
        if nom == "lampe" and court_circuit and premiere_lampe:
            # Fil de court-circuit : il fait le tour de la lampe, côté extérieur du circuit
            groupe += (f'<path d="M -45 0 L -45 -38 L 45 -38 L 45 0" fill="none" stroke="{ENCRE}" '
                       f'stroke-width="4" stroke-linejoin="round"/>'
                       f'<circle cx="-45" cy="0" r="4" fill="{ENCRE}"/><circle cx="45" cy="0" r="4" fill="{ENCRE}"/>')
            premiere_lampe = False
        elements.append(f'<g transform="translate({cx} {cy}) rotate({angle})">{groupe}</g>')
        # Lettres dans les symboles : écrites après la rotation, pour rester lisibles
        lettre = {"moteur": "M", "objet": "?"}.get(nom)
        if lettre:
            elements.append(_texte(cx, cy + 1, lettre, taille=18, gras=True, extra='dominant-baseline="central"'))
        # Nom du composant, écrit à l'intérieur du circuit et toujours à l'horizontale
        etiquette = objet if nom == "objet" else COMPOSANTS[nom]
        if etiquette:
            dx, dy = _tourner(0, 44, angle)
            ancre = "middle" if angle in (0, 180) else ("end" if angle == 90 else "start")
            if angle in (90, 270):
                dx, dy = _tourner(0, 30, angle)
            elements.append(_texte(cx + dx, cy + dy, etiquette, taille=15, ancre=ancre, gras=True,
                                   extra='dominant-baseline="central"'))
        if nom == "pile":
            # Signes + et − à côté des deux traits de la pile
            for signe, x in (("+", -16), ("−", 16)):
                sx, sy = _tourner(x, -26, angle)
                elements.append(_texte(cx + sx, cy + sy, signe, taille=16, gras=True,
                                       extra='dominant-baseline="central"'))
    contenu = "\n  ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 290" width="400" height="290">
  {contenu}
</svg>
'''


# --- Frises chronologiques (Découverte du monde, histoire) ---

# Les grandes périodes de l'histoire, telles qu'on les apprend à l'école en France
# (début, fin, nom, couleur). Avant -3300 (invention de l'écriture) : la Préhistoire.
PERIODES = [
    (-100000, -3300, "Préhistoire", "#e8dcc4"),
    (-3300, 476, "Antiquité", "#f6d9a8"),
    (476, 1492, "Moyen Âge", "#cfe3c4"),
    (1492, 1789, "Temps modernes", "#c9dcf2"),
    (1789, 100000, "Époque contemporaine", "#e3d2ef"),
]

PAS_FRISE = (1, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000)


def ecrire_annee(annee):
    """Une année écrite comme à l'école : « 3000 av. J.-C. », « 476 », « 0 » pour la naissance de J.-C."""
    if annee < 0:
        return f"{-annee} av. J.-C."
    return str(annee)


def dessiner_frise(debut, fin, pas, evenements, periodes=False):
    """Renvoie le code SVG d'une frise chronologique de `debut` à `fin` (années, négatives avant J.-C.),
    graduée tous les `pas` ans. `evenements` : liste de (date, texte) ; le texte « ? » marque
    la date à trouver. periodes=True colore les grandes périodes de l'histoire au-dessus de la frise."""
    gauche, droite, axe = 70, 590, 150
    largeur = droite - gauche

    def x_de(annee):
        return gauche + (annee - debut) / (fin - debut) * largeur

    elements = []
    legende = []        # périodes trop courtes pour y écrire leur nom : expliquées sous la frise
    if periodes:
        for p_debut, p_fin, nom, couleur in PERIODES:
            a, b = max(p_debut, debut), min(p_fin, fin)
            if a >= b:
                continue
            x1, x2 = x_de(a), x_de(b)
            elements.append(f'<rect x="{x1:.1f}" y="{axe - 34}" width="{x2 - x1:.1f}" height="28" fill="{couleur}" '
                            f'stroke="white" stroke-width="2"/>')
            # Le nom n'est écrit que s'il tient dans la bande (environ 8 pixels par lettre)
            if x2 - x1 >= len(nom) * 8 + 8:
                elements.append(_texte((x1 + x2) / 2, axe - 20, nom, taille=13, gras=True,
                                       extra='dominant-baseline="central"'))
            else:
                legende.append((nom, couleur))

    # L'axe du temps, avec une flèche vers la droite (le temps avance)
    elements.append(f'<line x1="{gauche - 10}" y1="{axe}" x2="{droite + 18}" y2="{axe}" stroke="{ENCRE}" stroke-width="4"/>')
    elements.append(f'<path d="M {droite + 26} {axe} L {droite + 14} {axe - 8} L {droite + 14} {axe + 8} Z" fill="{ENCRE}"/>')

    # Graduations
    annee = debut
    while annee <= fin:
        x = x_de(annee)
        elements.append(f'<line x1="{x:.1f}" y1="{axe - 6}" x2="{x:.1f}" y2="{axe + 6}" stroke="{ENCRE}" stroke-width="3"/>')
        elements.append(_texte(x, axe + 22, ecrire_annee(annee), taille=12, extra='dominant-baseline="central"'))
        annee += pas

    # Événements : un point sur l'axe, un trait, et le texte en dessous (sur 2 hauteurs pour ne pas se chevaucher)
    for rang, (date, texte) in enumerate(sorted(evenements)):
        x = x_de(date)
        y_texte = axe + 62 + (rang % 2) * 34
        couleur = "#e2574c" if texte == "?" else COULEUR
        # Le trait pointillé commence sous la ligne des années, pour ne pas les cacher
        elements.append(f'<line x1="{x:.1f}" y1="{axe + 36}" x2="{x:.1f}" y2="{y_texte - 14}" stroke="{couleur}" '
                        f'stroke-width="2" stroke-dasharray="4 3"/>')
        elements.append(f'<circle cx="{x:.1f}" cy="{axe}" r="7" fill="{couleur}" stroke="white" stroke-width="2"/>')
        x_bulle = min(max(x, gauche + 40), droite - 40)
        elements.append(_texte(x_bulle, y_texte, texte, taille=14 if texte != "?" else 20, gras=True,
                               couleur=couleur, extra='dominant-baseline="central"'))

    # Légende des périodes dont le nom ne tenait pas dans la bande
    bas = axe + 120
    if legende:
        x = gauche
        for nom, couleur in legende:
            elements.append(f'<rect x="{x}" y="{bas - 8}" width="16" height="16" rx="3" fill="{couleur}"/>')
            elements.append(_texte(x + 22, bas, nom, taille=13, ancre="start", extra='dominant-baseline="central"'))
            x += 22 + len(nom) * 8 + 24
        bas += 20

    contenu = "\n  ".join(elements)
    hauteur = bas - (axe - 50)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {axe - 50} 660 {hauteur}" width="660" height="{hauteur}">
  {contenu}
</svg>
'''


# --- Schémas fixes à légender (Découverte du monde : le corps) ---
# Chaque schéma est dessiné une fois pour toutes. L'IA choisit seulement QUELLES parties
# sont numérotées (1, 2, 3...) ; la question demande ensuite le nom d'une partie numérotée.
# Pour chaque partie : (nom affiché, x et y du point visé sur le dessin, côté de l'étiquette).

def _bezier(p0, p1, p2, t):
    """Un point d'une courbe de Bézier quadratique (celle des chemins SVG « Q »)."""
    return tuple((1 - t) ** 2 * a + 2 * t * (1 - t) * b + t ** 2 * c for a, b, c in zip(p0, p1, p2))


def _oeil_face():
    amande = "M 60 150 Q 200 40 340 150 Q 200 245 60 150 Z"     # le contour de l'œil, entre les paupières
    cils = ""
    for t in (0.14, 0.26, 0.38, 0.5, 0.62, 0.74, 0.86):
        x, y = _bezier((60, 150), (200, 40), (340, 150), t)
        dx = (t - 0.5) * 30
        cils += (f'<path d="M {x:.1f} {y - 22:.1f} q {dx / 2:.1f} -12 {dx:.1f} -22" fill="none" stroke="{ENCRE}" '
                 f'stroke-width="3" stroke-linecap="round"/>')
    return f'''<defs><clipPath id="amande"><path d="{amande}"/></clipPath></defs>
  <path d="M 80 52 Q 200 6 320 46" fill="none" stroke="#6b4a2b" stroke-width="13" stroke-linecap="round"/>
  <path d="{amande}" fill="#fdf8f4"/>
  <g clip-path="url(#amande)">
    <circle cx="200" cy="150" r="56" fill="#5b8fcf" stroke="#2d5a91" stroke-width="3"/>
    <circle cx="200" cy="150" r="22" fill="#111"/>
    <circle cx="188" cy="137" r="7" fill="white" opacity="0.85"/>
  </g>
  <path d="{amande}" fill="none" stroke="{ENCRE}" stroke-width="4"/>
  <path d="M 60 150 Q 200 40 340 150 L 336 128 Q 200 16 64 128 Z" fill="#f2d3bf" stroke="{ENCRE}" stroke-width="3"/>
  {cils}'''


def _oeil_coupe():
    # Blanc de l'œil (sclérotique) : un cercle ouvert à l'avant, où se trouve la cornée
    return f'''<path d="M 170 97 A 110 110 0 1 1 170 223" fill="#eef6fc" stroke="{ENCRE}" stroke-width="4"/>
  <path d="M 170 97 Q 80 160 170 223" fill="#dff0fb" stroke="{ENCRE}" stroke-width="4"/>
  <path d="M 225.1 64.2 A 102 102 0 1 1 225.1 255.8" fill="none" stroke="#e2574c" stroke-width="7"/>
  <line x1="174" y1="104" x2="174" y2="142" stroke="#6b4a2b" stroke-width="9" stroke-linecap="round"/>
  <line x1="174" y1="178" x2="174" y2="216" stroke="#6b4a2b" stroke-width="9" stroke-linecap="round"/>
  <ellipse cx="197" cy="160" rx="14" ry="38" fill="#fff6d6" stroke="{ENCRE}" stroke-width="3"/>
  <path d="M 366 138 L 446 126 L 446 194 L 366 182 Z" fill="#f4c27a" stroke="{ENCRE}" stroke-width="3"/>'''


DOSSIER_DESSINS = Path(__file__).parent / "dessins"    # dessins venus d'ailleurs (domaine public)


def _dessin_externe(fichier):
    """Le contenu d'un fichier SVG du dossier dessins/ (tout ce qui est entre <svg ...> et </svg>)."""
    texte = (DOSSIER_DESSINS / fichier).read_text(encoding="utf-8")
    debut = texte.index(">", texte.index("<svg")) + 1
    fin = texte.rindex("</svg>")
    # On retire les blocs <metadata> (ajoutés par certains logiciels) : ils utilisent des
    # préfixes (c2pa:, rdf:...) qui ne sont plus déclarés une fois le dessin inséré dans notre <svg>
    return re.sub(r"<metadata>.*?</metadata>", "", texte[debut:fin], flags=re.DOTALL)


SCHEMAS = {
    "oeil-face": {
        "titre": "un œil vu de face", "largeur": 400, "hauteur": 240, "dessin": _oeil_face,
        "parties": {
            "sourcil": ("le sourcil", 200, 30, "droite"),
            "paupiere": ("la paupière", 296, 114, "droite"),
            "blanc-de-l-oeil": ("le blanc de l'œil", 300, 152, "droite"),
            "cils": ("les cils", 94, 88, "gauche"),
            "pupille": ("la pupille", 200, 145, "gauche"),
            "iris": ("l'iris", 166, 182, "gauche"),
        },
    },
    "oeil-coupe": {
        "titre": "un œil vu en coupe", "largeur": 460, "hauteur": 320, "dessin": _oeil_coupe,
        "parties": {
            "iris": ("l'iris", 174, 118, "gauche", 76),
            "cornee": ("la cornée", 136, 128, "gauche", 120),
            "pupille": ("la pupille", 174, 160, "gauche"),
            "cristallin": ("le cristallin", 200, 190, "gauche", 205),
            "retine": ("la rétine", 326, 82, "droite"),
            "nerf-optique": ("le nerf optique", 430, 160, "droite"),
        },
    },
    "appareil-digestif": {
        # Dessin de Mariana Ruiz (LadyofHats), Wikimedia Commons, domaine public : dessins/appareil-digestif.svg
        # Les coordonnées des parties sont celles du dessin d'origine (351 × 821), réduit à 68 %.
        "titre": "l'appareil digestif", "fichier": "appareil-digestif.svg", "taille": (351, 821), "echelle": 0.68,
        "parties": {
            "bouche": ("la bouche", 100, 142, "gauche"),
            "oesophage": ("l'œsophage", 175, 330, "droite"),
            "foie": ("le foie", 75, 455, "gauche"),
            "estomac": ("l'estomac", 250, 470, "droite"),
            "intestin-grele": ("l'intestin grêle", 185, 640, "droite"),
            "gros-intestin": ("le gros intestin", 72, 640, "gauche"),
            "anus": ("l'anus", 176, 782, "gauche"),
        },
    },
}


def dessiner_schema(nom, parties):
    """Renvoie le code SVG du schéma `nom` (voir SCHEMAS), avec les `parties` numérotées 1, 2, 3...
    dans l'ordre de la liste. Les autres parties ne portent aucun numéro."""
    schema = SCHEMAS[nom]
    marge = 70                       # place pour les numéros, à gauche et à droite du dessin
    if "fichier" in schema:
        # Dessin externe : on l'insère réduit (un <svg> dans le <svg>), et on réduit aussi les coordonnées
        echelle = schema["echelle"]
        largeur, hauteur = round(schema["taille"][0] * echelle), round(schema["taille"][1] * echelle)
        elements = [f'<svg x="{marge}" y="0" width="{largeur}" height="{hauteur}" '
                    f'viewBox="0 0 {schema["taille"][0]} {schema["taille"][1]}">{_dessin_externe(schema["fichier"])}</svg>']
    else:
        echelle = 1
        largeur, hauteur = schema["largeur"], schema["hauteur"]
        elements = [f'<g transform="translate({marge} 0)">{schema["dessin"]()}</g>']
    for numero, partie in enumerate(parties, start=1):
        # (nom, x, y, côté) ou (nom, x, y, côté, hauteur du numéro) quand le trait doit être en biais
        _, x, y, cote, *autre = schema["parties"][partie]
        x, y = x * echelle, y * echelle
        y_num = autre[0] if autre else y
        x += marge
        x_num = 26 if cote == "gauche" else largeur + 2 * marge - 26
        elements.append(f'<line x1="{x_num}" y1="{y_num}" x2="{x}" y2="{y}" stroke="{ENCRE}" stroke-width="2"/>')
        elements.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{ENCRE}" stroke="white" stroke-width="1.5"/>')
        elements.append(f'<circle cx="{x_num}" cy="{y_num}" r="16" fill="white" stroke="{ENCRE}" stroke-width="3"/>')
        elements.append(_texte(x_num, y_num + 1, numero, taille=17, gras=True, extra='dominant-baseline="central"'))
    contenu = "\n  ".join(elements)
    w = largeur + 2 * marge
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {hauteur}" width="{w}" height="{hauteur}">
  {contenu}
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
    enregistrer(dessiner_barres(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"], [12, 7, 15, 9, 4],
                                "Livres empruntés"), "images/exemples/barres.svg")
    enregistrer(dessiner_courbe(["Jan", "Fév", "Mar", "Avr", "Mai", "Juin"], [3, 5, 9, 13, 17, 21],
                                "Température (°C)"), "images/exemples/courbe.svg")
    enregistrer(dessiner_camembert(["Football", "Natation", "Danse", "Judo"], [50, 25, 15, 10],
                                   "Sport préféré"), "images/exemples/camembert.svg")
    enregistrer(dessiner_billes(rouges=5, bleues=2, vertes=1), "images/exemples/billes.svg")
    enregistrer(dessiner_venn("Sport", "Musique", ["Léo", "Inès"], ["Sami"], ["Emma", "Noé", "Lina"]),
                "images/exemples/venn.svg")
    enregistrer(dessiner_circuit(["pile", "lampe", "interrupteur-ferme"]), "images/exemples/circuit-ferme.svg")
    enregistrer(dessiner_circuit(["lampe", "interrupteur-ouvert", "moteur", "pile"]), "images/exemples/circuit-ouvert.svg")
    enregistrer(dessiner_circuit(["lampe", "coupure", "pile"]), "images/exemples/circuit-coupure.svg")
    enregistrer(dessiner_circuit(["lampe", "objet", "pile"], objet="cuillère en métal"), "images/exemples/circuit-objet.svg")
    enregistrer(dessiner_circuit(["lampe", "pile"], court_circuit=True), "images/exemples/circuit-court.svg")
    enregistrer(dessiner_frise(-3000, 2000, 1000, [(-52, "Alésia"), (476, "?"), (1492, "Colomb")], periodes=True),
                "images/exemples/frise-periodes.svg")
    enregistrer(dessiner_frise(1000, 1500, 100, [(1096, "1re croisade"), (1163, "Notre-Dame"), (1431, "?")]),
                "images/exemples/frise-moyen-age.svg")
    for nom, schema in SCHEMAS.items():
        enregistrer(dessiner_schema(nom, list(schema["parties"])), f"images/exemples/schema-{nom}.svg")
