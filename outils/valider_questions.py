# Vérifie que le fichier de questions respecte les règles du projet
import argparse
import json
import sys

TYPES_CONNUS = ["qcm", "saisie"]
CHAMPS_COMMUNS = ["enonce", "explication"]


def verifier_question(question, numero):
    """Contrôles communs à tous les types, puis aiguillage selon le type."""
    erreurs = []

    for champ in CHAMPS_COMMUNS:
        if champ not in question:
            erreurs.append(f"Question {numero} : champ '{champ}' manquant")

    type_question = question.get("type", "qcm")   # "qcm" si le champ est absent
    if type_question not in TYPES_CONNUS:
        erreurs.append(f"Question {numero} : type '{type_question}' inconnu")
        return erreurs

    if type_question == "qcm":
        erreurs.extend(verifier_qcm(question, numero))
    elif type_question == "saisie":
        erreurs.extend(verifier_saisie(question, numero))

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

    # Contrôle 2 : chaque réponse est courte
    for i, rep in enumerate(reponses, start=1):
        if not isinstance(rep, str):
            erreurs.append(f"Question {numero} : réponse {i} n'est pas une chaîne de caractères")
        elif len(rep.split()) > 4:
            erreurs.append(f"Question {numero} : réponse {i} est trop longue (plus de 4 mots)")
        elif len(rep) > 30:
            erreurs.append(f"Question {numero} : réponse {i} est trop longue ({len(rep)} caractères)")

    # Contrôle 3 : pas de doublon
    if len(set(reponses)) != len(reponses):
        erreurs.append(f"Question {numero} : il y a des réponses en double")

    # Contrôle 4 : réglage des accents
    accents = question.get("accents", "toleres")  # tolérés par défaut
    if accents not in ["toleres", "stricts"]:
        erreurs.append(f"Question {numero} : 'accents' doit être 'toleres' ou 'stricts', pas {accents!r}")

    return erreurs

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