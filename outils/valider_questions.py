# Vérifie que le fichier de questions respecte les règles du projet
import argparse
import json
import sys
from pathlib import Path

TYPES_CONNUS = ["qcm", "saisie", "association", "ordre", "vraifaux", "robot"]
CHAMPS_COMMUNS = ["enonce", "explication"]


def verifier_question(question, numero):
    """Contrôles communs à tous les types, puis aiguillage selon le type."""
    erreurs = []

    for champ in CHAMPS_COMMUNS:
        if champ not in question:
            erreurs.append(f"Question {numero} : champ '{champ}' manquant")

    if "image" in question:
        if "alt" not in question:
            erreurs.append(f"Question {numero} : champ 'alt' manquant pour l'image")
        if not Path(question["image"]).exists():
            erreurs.append(f"Question {numero} : l'image '{question['image']}' n'existe pas")

    if "astuce" in question:
        if not isinstance(question["astuce"], str):
            erreurs.append(f"Question {numero} : champ 'astuce' doit être une chaîne de caractères")
        elif not 1 <= len(question["astuce"]) <= 150:
            erreurs.append(f"Question {numero} : champ 'astuce' trop long ({len(question['astuce'])} caractères)")

    if "defi" in question:
        if not isinstance(question["defi"], bool):
            erreurs.append(f"Question {numero} : champ 'defi' doit être un booléen")

    if "texte" in question:
        if not isinstance(question["texte"], str):
            erreurs.append(f"Question {numero} : champ 'texte' doit être une chaîne de caractères")
        elif not 20 <= len(question["texte"]) <= 1200:
            erreurs.append(f"Question {numero} : champ 'texte' trop court ou trop long ({len(question['texte'])} caractères)")

    type_question = question.get("type", "qcm")   # "qcm" si le champ est absent
    if type_question not in TYPES_CONNUS:
        erreurs.append(f"Question {numero} : type '{type_question}' inconnu")
        return erreurs

    if type_question == "qcm":
        erreurs.extend(verifier_qcm(question, numero))
    elif type_question == "saisie":
        erreurs.extend(verifier_saisie(question, numero))
    elif type_question == "association":
        erreurs.extend(verifier_association(question, numero))
    elif type_question == "ordre":
        erreurs.extend(verifier_ordre(question, numero))
    elif type_question == "vraifaux":
        erreurs.extend(verifier_vraifaux(question, numero))
    elif type_question == "robot":
        erreurs.extend(verifier_robot(question, numero))

    return erreurs


def verifier_qcm(question, numero):
    """Contrôles propres aux QCM."""
    erreurs = []
    # présence de "choix" et "bonneReponse",
    # puis contrôles 1 à 4 (nombre de choix, type, position, doublons)
    for champ in ["choix", "bonneReponse"]:
        if champ not in question:
         erreurs.append(f"Question {numero} : champ '{champ}' manquant pour un QCM")
    if erreurs:
        return erreurs
    
    choix = question["choix"]
    bonne = question["bonneReponse"]

    # Contrôle 1 : il y a exactement 4 choix
    if len(choix) != 4:
        erreurs.append(f"Question {numero} : il y a {len(choix)} choix au lieu de 4")

    # Contrôle 2 : bonneReponse est un nombre entier
    if not isinstance(bonne, int):
        erreurs.append(f"Question {numero} : bonneReponse doit être un nombre entier, pas {bonne!r}")
        return erreurs   # impossible de vérifier la position sans un nombre

    # Contrôle 3 : bonneReponse est une position valide (0 à 3)
    if not (0 <= bonne < len(choix)):
        erreurs.append(f"Question {numero} : bonneReponse = {bonne} n'est pas une position valide dans choix")

    # Contrôle 4 : pas de choix en double
    if len(set(choix)) != len(choix):
        erreurs.append(f"Question {numero} : il y a des choix en double")

    return erreurs

def verifier_saisie(question, numero):
    """Contrôles propres aux questions à saisir au clavier."""
    erreurs = []
    reponses = question.get("reponses")

    # Contrôle 1 : une liste non vide
    if not isinstance(reponses, list) or len(reponses) == 0:
        erreurs.append(f"Question {numero} : 'reponses' doit être une liste non vide")
        return erreurs

    # Contrôle 2 : chaque réponse est courte (4 mots / 30 caractères)
    # ou, si "phrase": true, une phrase complète (20 mots / 120 caractères, majuscule au début, point à la fin)
    phrase = question.get("phrase", False)
    if not isinstance(phrase, bool):
        erreurs.append(f"Question {numero} : 'phrase' doit être un booléen")
        phrase = False
    max_mots, max_caracteres = (20, 120) if phrase else (4, 30)
    for i, rep in enumerate(reponses, start=1):
        if not isinstance(rep, str):
            erreurs.append(f"Question {numero} : réponse {i} n'est pas une chaîne de caractères")
        elif len(rep.split()) > max_mots:
            erreurs.append(f"Question {numero} : réponse {i} est trop longue (plus de {max_mots} mots)")
        elif len(rep) > max_caracteres:
            erreurs.append(f"Question {numero} : réponse {i} est trop longue ({len(rep)} caractères)")
        elif phrase and not (rep and rep[0].isupper() and rep[-1] in ".!?"):
            erreurs.append(f"Question {numero} : réponse {i} doit commencer par une majuscule et finir par . ! ou ?")

    # Contrôle 3 : pas de doublon
    if len(set(reponses)) != len(reponses):
        erreurs.append(f"Question {numero} : il y a des réponses en double")

    # Contrôle 4 : réglage des accents
    accents = question.get("accents", "toleres")  # tolérés par défaut
    if accents not in ["toleres", "stricts"]:
        erreurs.append(f"Question {numero} : 'accents' doit être 'toleres' ou 'stricts', pas {accents!r}")

    # Contrôle 5 : réglage des majuscules (ignorées par défaut)
    majuscules = question.get("majuscules", "tolerees")
    if majuscules not in ["tolerees", "strictes"]:
        erreurs.append(f"Question {numero} : 'majuscules' doit être 'tolerees' ou 'strictes', pas {majuscules!r}")

    return erreurs

def verifier_association(question, numero):
    """Contrôles propres aux exercices « relier » : 3 à 5 paires de textes courts, sans doublon."""
    erreurs = []
    paires = question.get("paires")
    if not isinstance(paires, list) or not 3 <= len(paires) <= 5:
        erreurs.append(f"Question {numero} : 'paires' doit être une liste de 3 à 5 paires")
        return erreurs
    for i, paire in enumerate(paires, start=1):
        if (not isinstance(paire, list) or len(paire) != 2
                or not all(isinstance(texte, str) and 1 <= len(texte) <= 40 for texte in paire)):
            erreurs.append(f"Question {numero} : la paire {i} doit contenir deux textes de 1 à 40 caractères")
            return erreurs
    for cote, nom in ((0, "gauche"), (1, "droite")):
        textes = [paire[cote] for paire in paires]
        if len(set(textes)) != len(textes):
            erreurs.append(f"Question {numero} : il y a des éléments en double à {nom}")
    return erreurs


def verifier_ordre(question, numero):
    """Contrôles propres aux exercices « remettre dans l'ordre » : 3 à 6 étiquettes, sans doublon."""
    erreurs = []
    elements = question.get("elements")
    if not isinstance(elements, list) or not 3 <= len(elements) <= 6:
        erreurs.append(f"Question {numero} : 'elements' doit être une liste de 3 à 6 étiquettes")
        return erreurs
    if not all(isinstance(texte, str) and 1 <= len(texte) <= 60 for texte in elements):
        erreurs.append(f"Question {numero} : chaque étiquette doit être un texte de 1 à 60 caractères")
    elif len(set(elements)) != len(elements):
        erreurs.append(f"Question {numero} : il y a des étiquettes en double")
    return erreurs

def verifier_vraifaux(question, numero):
    """Contrôles propres aux exercices « vrai ou faux » : une affirmation (dans "enonce")
    et la réponse dans "vrai" (true ou false)."""
    erreurs = []

    affirmation = question.get("enonce")
    if not isinstance(affirmation, str) or not 1 <= len(affirmation) <= 200:
        erreurs.append(f"Question {numero} : 'enonce' doit être un texte de 1 à 200 caractères")
    elif affirmation.strip().endswith("?"):
        erreurs.append(f"Question {numero} : 'enonce' doit être une affirmation, pas une question")

    if not isinstance(question.get("vrai"), bool):
        erreurs.append(f"Question {numero} : 'vrai' doit valoir true ou false")

    for champ in ("choix", "bonneReponse", "reponses", "paires", "elements"):
        if champ in question:
            erreurs.append(f"Question {numero} : champ '{champ}' inutile pour un vrai ou faux")

    return erreurs

def deplier(solution):
    """Remplace chaque boucle par ses instructions, répétées le bon nombre de fois."""
    instructions = []
    for instruction in solution:
        if isinstance(instruction, str):
            instructions.append(instruction)
        else:
            for tour in range(instruction["repeter"]):
                instructions.extend(instruction["faire"])
    return instructions

def verifier_robot(question, numero):
    """Contrôles propres aux exercices « robot »."""
    erreurs = []

    # Contrôle 1 : la grille a une largeur et une hauteur entières, de 3 à 8
    grille = question.get("grille")
    if not isinstance(grille, dict):
        erreurs.append(f"Question {numero} : 'grille' manquante")
        return erreurs

    largeur = grille.get("largeur")
    hauteur = grille.get("hauteur")
    if not (isinstance(largeur, int) and 3 <= largeur <= 8):
        erreurs.append(f"Question {numero} : 'largeur' doit être un entier de 3 à 8")
    if not (isinstance(hauteur, int) and 3 <= hauteur <= 8):
        erreurs.append(f"Question {numero} : 'hauteur' doit être un entier de 3 à 8")
    if erreurs:
        return erreurs

    # Contrôle 2 : le départ et la cible sont des cases de la grille
    for nom in ("depart", "cible"):
        position = question.get(nom)
        if not isinstance(position, dict):
            erreurs.append(f"Question {numero} : '{nom}' manquant")
            continue
        x = position.get("x")
        y = position.get("y")
        if not (isinstance(x, int) and 0 <= x < largeur and isinstance(y, int) and 0 <= y < hauteur):
            erreurs.append(f"Question {numero} : '{nom}' doit être une case de la grille")
    if erreurs:
        return erreurs

    depart = question["depart"]
    cible = question["cible"]
    if depart.get("direction") not in ("nord", "est", "sud", "ouest"):
        erreurs.append(f"Question {numero} : la direction du départ doit être nord, est, sud ou ouest")
    if depart["x"] == cible["x"] and depart["y"] == cible["y"]:
        erreurs.append(f"Question {numero} : le départ ne doit pas être sur la cible")

    # Contrôle 3 : les murs (facultatifs) sont des cases de la grille, sans doublon,
    # et jamais sur le départ ni sur la cible
    murs = question.get("murs", [])
    if not isinstance(murs, list):
        erreurs.append(f"Question {numero} : 'murs' doit être une liste")
        return erreurs

    deja_vus = []
    for mur in murs:
        if not (isinstance(mur, list) and len(mur) == 2):
            erreurs.append(f"Question {numero} : chaque mur doit être une case [x, y]")
            continue
        x, y = mur
        if not (isinstance(x, int) and 0 <= x < largeur and isinstance(y, int) and 0 <= y < hauteur):
            erreurs.append(f"Question {numero} : le mur {mur} est hors de la grille")
        if mur in deja_vus:
            erreurs.append(f"Question {numero} : le mur {mur} est en double")
        if mur == [depart["x"], depart["y"]] or mur == [cible["x"], cible["y"]]:
            erreurs.append(f"Question {numero} : le mur {mur} est sur le départ ou sur la cible")
        deja_vus.append(mur)

    # Contrôle 4 : les blocs proposés à l'élève
    BLOCS_CONNUS = ("avancer", "gauche", "droite", "repeter")
    blocs = question.get("blocs")
    if not (isinstance(blocs, list) and len(blocs) > 0 and all(b in BLOCS_CONNUS for b in blocs)):
        erreurs.append(f"Question {numero} : 'blocs' doit être une liste non vide prise parmi {BLOCS_CONNUS}")
        return erreurs

    # Contrôle 5 : la solution n'utilise que des blocs autorisés, et ses boucles sont bien formées
    solution = question.get("solution")
    if not (isinstance(solution, list) and len(solution) > 0):
        erreurs.append(f"Question {numero} : 'solution' doit être une liste d'instructions")
        return erreurs

    nombre_de_blocs = 0
    for instruction in solution:
        if isinstance(instruction, str):
            nombre_de_blocs += 1
            if instruction not in blocs:
                erreurs.append(f"Question {numero} : l'instruction '{instruction}' n'est pas dans 'blocs'")
        elif isinstance(instruction, dict):
            tours = instruction.get("repeter")
            faire = instruction.get("faire")
            if "repeter" not in blocs:
                erreurs.append(f"Question {numero} : la solution utilise une boucle, mais 'repeter' n'est pas dans 'blocs'")
            if not (isinstance(tours, int) and 2 <= tours <= 10):
                erreurs.append(f"Question {numero} : 'repeter' doit être un entier de 2 à 10")
            if not (isinstance(faire, list) and len(faire) > 0 and all(i in blocs and i != "repeter" for i in faire)):
                erreurs.append(f"Question {numero} : 'faire' doit être une liste d'instructions simples autorisées")
            else:
                nombre_de_blocs += 1 + len(faire)
        else:
            erreurs.append(f"Question {numero} : instruction inconnue dans la solution : {instruction}")

    # Contrôle 6 : le nombre de blocs maximum (facultatif)
    max_blocs = question.get("maxBlocs")
    if max_blocs is not None:
        if not isinstance(max_blocs, int):
            erreurs.append(f"Question {numero} : 'maxBlocs' doit être un entier")
        elif nombre_de_blocs > max_blocs:
            erreurs.append(f"Question {numero} : la solution utilise {nombre_de_blocs} blocs, plus que 'maxBlocs' ({max_blocs})")   

    # Contrôle 8 : pas de champs propres aux autres types
    for champ in ("choix", "bonneReponse", "reponses", "paires", "elements", "vrai"):
        if champ in question:
            erreurs.append(f"Question {numero} : champ '{champ}' inutile pour un exercice robot")
            
    # Contrôle 7 : on fait jouer la solution, le robot doit finir sur l'étoile sans se cogner
    if erreurs:
        return erreurs   # inutile de simuler une solution mal écrite

    DIRECTIONS = ["nord", "est", "sud", "ouest"]
    PAS = {"nord": (0, -1), "est": (1, 0), "sud": (0, 1), "ouest": (-1, 0)}

    x = depart["x"]
    y = depart["y"]
    direction = depart["direction"]
    for numero_instruction, instruction in enumerate(deplier(solution), start=1):
        if instruction == "avancer":
            dx, dy = PAS[direction]
            nouveau_x = x + dx
            nouveau_y = y + dy
            dans_la_grille = 0 <= nouveau_x < largeur and 0 <= nouveau_y < hauteur
            if not dans_la_grille or [nouveau_x, nouveau_y] in murs:
                erreurs.append(f"Question {numero} : la solution fait cogner le robot (instruction n°{numero_instruction})")
                return erreurs
            x = nouveau_x
            y = nouveau_y
        elif instruction == "droite":
            direction = DIRECTIONS[(DIRECTIONS.index(direction) + 1) % 4]
        elif instruction == "gauche":
            direction = DIRECTIONS[(DIRECTIONS.index(direction) - 1) % 4]

    if x != cible["x"] or y != cible["y"]:
        erreurs.append(f"Question {numero} : la solution arrête le robot en ({x}, {y}), pas sur l'étoile")

    return erreurs

def resume_question(question):
    """Un résumé qui identifie une question : son énoncé, et pour les exercices « relier » et
    « ordre » (dont l'énoncé est souvent le même, ex. « Relie chaque mot à sa définition. »),
    leur contenu. Sert à repérer les doublons (publier.py) et à les montrer à l'IA (generer_ia.py)."""
    resume = question.get("enonce", "")
    if question.get("type") == "association":
        resume += " [" + " ; ".join(f"{g} → {d}" for g, d in question.get("paires", [])) + "]"
    elif question.get("type") == "ordre":
        resume += " [" + " → ".join(question.get("elements", [])) + "]"
    return resume


def main():
    parser = argparse.ArgumentParser(description="Vérifie un fichier de questions.")
    parser.add_argument("fichier", help="chemin du fichier JSON à vérifier")
    args = parser.parse_args()
    with open(args.fichier, encoding="utf-8") as fichier:
        questions = json.load(fichier)

    toutes_les_erreurs = []
    for numero, question in enumerate(questions, start=1):
        toutes_les_erreurs.extend(verifier_question(question, numero))

    if toutes_les_erreurs:
        print(f"ERREUR : {len(toutes_les_erreurs)} problème(s) dans {args.fichier}")
        for erreur in toutes_les_erreurs:
            print("  -", erreur)
        sys.exit(1)
    else:
        print(f"OK : {len(questions)} questions valides dans {args.fichier}")


if __name__ == "__main__":
    main()