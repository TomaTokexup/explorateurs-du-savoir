# Génère des questions avec l'IA, les contrôle, et garde celles qui sont valides
import json
import sys
import argparse
import anthropic

from pathlib import Path
from figures import (DIRECTIONS, dessiner_angle, dessiner_horloge, dessiner_polygone,
                     dessiner_rectangle, dessiner_repere, dessiner_rose, enregistrer)
from dotenv import load_dotenv
from valider_questions import verifier_question   # ta fonction !

def charger_objectifs(niveau, matiere, theme):
    """Renvoie le titre du domaine et la liste de ses objectifs officiels."""
    # 1. construire le chemin : programme/<niveau>/<matiere>.json  (f-string)
    chemin = f"programme/{niveau}/{matiere}.json"
    # 2. ouvrir et lire le fichier avec json.load
    with open(chemin, "r", encoding="utf-8") as fichier:
        programme = json.load(fichier)
    # 3. si theme n'est pas une clé de programme["domaines"] :
    #       afficher un message qui liste les thèmes disponibles, puis sys.exit(1)
    if theme not in programme["domaines"]:
        print(f"Thème '{theme}' non trouvé dans le programme.")
        print("Thèmes disponibles :")
        for t in programme["domaines"]:
            print(f"  - {t}")
        sys.exit(1)
    # 4. renvoyer deux valeurs : return titre, objectifs
    return programme["domaines"][theme]["titre"], programme["domaines"][theme]["objectifs"]

def charger_enonces_existants(niveau, matiere, theme):
    """Renvoie la liste des énoncés déjà publiés pour ce thème (vide si le thème n'existe pas)."""
    chemin = Path(f"donnees/{niveau}/{matiere}/{theme}.json")
    if not chemin.exists():
        return []
    with open(chemin, "r", encoding="utf-8") as fichier:
        return [q.get("enonce") for q in json.load(fichier)]

def construire_consignes(niveau, titre_domaine, objectifs, nombre, nb_saisies, enonces_existants):
    """Construit le 'system prompt' à partir des objectifs officiels."""
    liste_objectifs = "\n".join(f"- {objectif}" for objectif in objectifs)
    nb_qcm = nombre - nb_saisies
    # Les questions déjà publiées, pour que l'IA ne les reproduise pas
    if enonces_existants:
        liste_existants = "\n".join(f"- {enonce}" for enonce in enonces_existants)
        bloc_existants = f"""
Questions déjà publiées pour ce domaine. Ne les reproduis pas, même reformulées ou avec d'autres nombres ;
couvre plutôt d'autres objectifs, ou d'autres situations de la vie courante :
{liste_existants}
"""
    else:
        bloc_existants = ""
    return f"""Tu rédiges des exercices de révision pour des élèves de {niveau.upper()} des Écoles européennes (section française, enfants de 8 à 11 ans).

Domaine : {titre_domaine}
Objectifs officiels du programme pour ce niveau (syllabus des Écoles européennes, en anglais) :
{liste_objectifs}
{bloc_existants}
Consignes générales :
- Chaque question évalue UN de ces objectifs. Varie les objectifs couverts d'une question à l'autre.
- Ne dépasse jamais le niveau fixé par ces objectifs.
- Utilise le vocabulaire employé en classe en France (« pavé droit » et non « cuboïde », « sommet » et non « vertex »), même si les objectifs officiels sont en anglais.
- Écris en français, avec des mots simples. Précise toujours les unités.
- L'explication enseigne la méthode en une ou deux phrases ; elle ne se contente pas de répéter la réponse.

Rédige exactement {nb_qcm} questions de type "qcm" et {nb_saisies} questions de type "saisie".

Type "qcm" :
- exactement 4 choix, dont une seule bonne réponse ;
- les mauvaises réponses correspondent à des erreurs fréquentes d'élèves ;
- "bonneReponse" est la position de la bonne réponse dans "choix", en comptant à partir de 0.

Type "saisie" (l'élève tape sa réponse au clavier) :
- réponse courte et fermée : un nombre, un mot ou au plus 4 mots, jamais une phrase ;
- l'énoncé est assez précis pour qu'une seule réponse soit possible ;
- "reponses" liste toutes les écritures acceptables de cette réponse (par exemple ["0,5", "0.5"] ou ["1 200", "1200"]) ;
- "accents" vaut "toleres".

Figures (facultatif, surtout en géométrie) :
- Tu peux ajouter à une question un champ "figure" quand un dessin aide l'élève. Formes disponibles :
  {{"forme": "angle", "mesure": <nombre entier de 1 à 180>}}
  {{"forme": "polygone", "cotes": <nombre entier de 3 à 10>}}
  {{"forme": "horloge", "heures": <entier de 1 à 12>, "minutes": <multiple de 5, de 0 à 55>}}  (horloge à aiguilles)
  {{"forme": "repere", "x": <entier de 0 à 6>, "y": <entier de 0 à 6>}}  (quadrillage avec un point nommé A)
  {{"forme": "rose", "direction": "N" | "NE" | "E" | "SE" | "S" | "SO" | "O" | "NO"}}  (rose des vents où seul le nord est écrit ; une flèche rouge montre la direction)
  {{"forme": "rectangle", "longueur": <entier>, "largeur": <entier inférieur ou égal>, "unite": "mm" | "cm" | "m"}}  (rectangle avec ses deux dimensions écrites)
- L'énoncé parle alors de la figure (« cet angle », « cette horloge », « le point A », « la flèche rouge ») et ne donne pas l'information que la figure montre (mesure, nombre de côtés, heure, coordonnées, direction).
- Pour le rectangle, la figure donne les dimensions : la question porte sur un calcul (périmètre, aire), jamais sur la lecture des dimensions.
- N'utilise aucune autre forme, et n'écris jamais de champ "image" toi-même.

Réponds UNIQUEMENT avec un tableau JSON, sans aucun texte avant ou après :
[
  {{"type": "qcm", "enonce": "...", "choix": ["...", "...", "...", "..."], "bonneReponse": 0, "explication": "..."}},
  {{"type": "saisie", "enonce": "...", "reponses": ["..."], "accents": "toleres", "explication": "..."}}
]"""

def demander_questions(consignes, demande):
    """Envoie la demande à l'IA et renvoie sa réponse en texte."""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=8000,
        system=consignes,
        messages=[
            {"role": "user", "content": demande}
        ],
    )
    print(f"Tokens : {message.usage.input_tokens} en entrée, {message.usage.output_tokens} en sortie")

    # La réponse est une liste de blocs (réflexion, texte...) : on ne garde que le texte
    texte = ""
    for bloc in message.content:
        if bloc.type == "text":
            texte = texte + bloc.text

    # Si la limite de tokens est atteinte, la réponse est coupée et le JSON sera incomplet
    if message.stop_reason == "max_tokens":
        print("Attention : réponse coupée, augmente max_tokens")

    return texte

def extraire_json(texte):
    """Garde seulement le tableau JSON, même si l'IA l'a entouré de texte ou de balises."""
    debut = texte.find("[")     # position du premier [
    fin = texte.rfind("]")      # position du dernier ]  (r = en partant de la droite)
    if debut == -1 or fin == -1:
        return texte            # pas de crochets : on laisse json.loads signaler l'erreur
    return texte[debut:fin + 1]

def creer_figure(description, niveau, matiere):
    """Dessine la figure décrite par l'IA et renvoie (chemin de l'image, texte alt).
    Lève une ValueError si la description est invalide."""
    forme = description.get("forme")

    if forme == "angle":
        mesure = description.get("mesure")
        if not isinstance(mesure, int) or not 1 <= mesure <= 180:
            raise ValueError(f"mesure d'angle invalide : {mesure!r}")
        svg = dessiner_angle(mesure)
        nom = f"angle-{mesure}"
        alt = "Un angle"

    elif forme == "polygone":
        nombre_cotes = description.get("cotes")
        if not isinstance(nombre_cotes, int) or not 3 <= nombre_cotes <= 10:
            raise ValueError(f"nombre de côtés invalide : {nombre_cotes!r}")
        svg = dessiner_polygone(nombre_cotes)
        nom = f"polygone-{nombre_cotes}"
        alt = "Un polygone"

    elif forme == "horloge":
        heures = description.get("heures")
        minutes = description.get("minutes")
        if not isinstance(heures, int) or not 1 <= heures <= 12:
            raise ValueError(f"heure invalide : {heures!r}")
        if not isinstance(minutes, int) or not 0 <= minutes <= 55 or minutes % 5 != 0:
            raise ValueError(f"minutes invalides (multiple de 5 entre 0 et 55) : {minutes!r}")
        svg = dessiner_horloge(heures, minutes)
        nom = f"horloge-{heures}h{minutes:02d}"     # :02d → toujours 2 chiffres (2h05, pas 2h5)
        alt = "Une horloge à aiguilles"

    elif forme == "repere":
        x = description.get("x")
        y = description.get("y")
        for valeur in (x, y):
            if not isinstance(valeur, int) or not 0 <= valeur <= 6:
                raise ValueError(f"coordonnée invalide (entier de 0 à 6) : {valeur!r}")
        svg = dessiner_repere(x, y)
        nom = f"repere-{x}-{y}"
        alt = "Un quadrillage avec un point A"

    elif forme == "rose":
        direction = description.get("direction")
        if direction not in DIRECTIONS:
            raise ValueError(f"direction invalide : {direction!r}")
        svg = dessiner_rose(direction)
        nom = f"rose-{direction.lower()}"
        alt = "Une rose des vents avec une flèche rouge"

    elif forme == "rectangle":
        longueur = description.get("longueur")
        largeur = description.get("largeur")
        unite = description.get("unite", "cm")
        for valeur in (longueur, largeur):
            if not isinstance(valeur, int) or not 1 <= valeur <= 50:
                raise ValueError(f"dimension invalide (entier de 1 à 50) : {valeur!r}")
        if largeur > longueur:
            raise ValueError("la largeur doit être inférieure ou égale à la longueur")
        if unite not in ("mm", "cm", "m"):
            raise ValueError(f"unité invalide : {unite!r}")
        svg = dessiner_rectangle(longueur, largeur, unite)
        nom = f"rectangle-{longueur}x{largeur}{unite}"
        alt = f"Un rectangle de {longueur} {unite} sur {largeur} {unite}"

    else:
        raise ValueError(f"forme inconnue : {forme!r}")

    chemin = f"images/{niveau}/{matiere}/{nom}.svg"
    enregistrer(svg, chemin)
    return chemin, alt

def main():

    parser = argparse.ArgumentParser(description="Génère des questions avec l'IA à partir du programme officiel.")
    parser.add_argument("--niveau", required=True, help="ex. p4")
    parser.add_argument("--matiere", required=True, help="ex. maths")
    parser.add_argument("--theme", required=True, help="ex. operations")
    parser.add_argument("--nombre", type=int, default=8, help="nombre total de questions (défaut : 8)")
    parser.add_argument("--saisies", type=int, default=2, help="dont questions à saisir (défaut : 2)")
    args = parser.parse_args()
    load_dotenv()

    # 1. titre, objectifs = charger_objectifs(...)
    titre, objectifs = charger_objectifs(args.niveau, args.matiere, args.theme)

    # 1b. enonces_existants = charger_enonces_existants(...)
    enonces_existants = charger_enonces_existants(args.niveau, args.matiere, args.theme)
    enonces_existants = charger_enonces_existants(args.niveau, args.matiere, args.theme)
    print(f"{len(enonces_existants)} question(s) déjà publiée(s) transmise(s) à l'IA")

    # 2. consignes = construire_consignes(...)
    consignes = construire_consignes(args.niveau, titre, objectifs, args.nombre, args.saisies, enonces_existants)

    # 3. demande = f"Rédige les {args.nombre} questions sur le domaine « {titre} »."
    demande = f"Rédige les {args.nombre} questions sur le domaine « {titre} »."

    # 4. texte = demander_questions(consignes, demande)
    texte = demander_questions(consignes, demande)

    # Transformer le texte en liste Python (peut échouer si l'IA n'a pas respecté le format)
    texte = extraire_json(texte)
    try:
        questions = json.loads(texte)
    except json.JSONDecodeError as erreur:
        print("L'IA n'a pas renvoyé du JSON valide :", erreur)
        print("--- Réponse brute ---")
        print(texte)
        sys.exit(1)

    valides = []
    rejetees = []

    #  - si la liste d'erreurs est vide  -> ajoute la question à "valides"
    #  - sinon -> affiche chaque erreur et ajoute la question à "rejetees"
    for numero, question in enumerate(questions, start=1):
        # Si l'IA a décrit une figure, Python la dessine
        if "figure" in question:
            try:
                question["image"], question["alt"] = creer_figure(
                    question.pop("figure"), args.niveau, args.matiere)
            except ValueError as erreur:
                print(f"Question {numero} rejetée : {erreur}")
                rejetees.append(question)
                continue
        erreurs = verifier_question(question, numero)
        if not erreurs:
            valides.append(question)
        else:
            print(f"Question {numero} rejetée :")
            for erreur in erreurs:
                print("  -", erreur)
            rejetees.append(question)

    # 6. fichier de sortie : f"donnees/brouillon_{args.niveau}_{args.matiere}_{args.theme}.json"
    fichier_sortie = f"donnees/brouillon_{args.niveau}_{args.matiere}_{args.theme}.json"
    with open(fichier_sortie, "w", encoding="utf-8") as fichier:
        json.dump(valides, fichier, ensure_ascii=False, indent=2)

    print(f"{len(valides)} questions valides enregistrées dans {fichier_sortie}")
    print(f"{len(rejetees)} questions rejetées")


if __name__ == "__main__":
    main()