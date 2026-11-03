# Vérifie que le fichier de questions respecte les règles du projet
import argparse
import json
import sys
from pathlib import Path

TYPES_CONNUS = ["qcm", "saisie", "association", "ordre"]
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
        elif not 20 <= len(question["texte"]) <= 800:
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