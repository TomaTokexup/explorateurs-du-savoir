# Vérifie que le fichier de questions respecte les règles du projet
import json
import sys

FICHIER = "donnees/maths.json"
CHAMPS_OBLIGATOIRES = ["enonce", "choix", "bonneReponse", "explication"]


def verifier_question(question, numero):
    """Renvoie la liste des erreurs trouvées dans une question."""
    erreurs = []

    # Contrôle 1 : tous les champs sont présents
    for champ in CHAMPS_OBLIGATOIRES:
        if champ not in question:
            erreurs.append(f"Question {numero} : champ '{champ}' manquant")
    if erreurs:
        return erreurs   # inutile de continuer si un champ manque

    choix = question["choix"]
    bonne = question["bonneReponse"]

    # Contrôle 2 : il y a exactement 4 choix
    if len(choix) != 4:
        erreurs.append(f"Question {numero} : il y a {len(choix)} choix au lieu de 4")

    # Contrôle 3 : bonneReponse est une position valide (0 à 3)
    if not (0 <= bonne < len(choix)):
        erreurs.append(f"Question {numero} : bonneReponse = {bonne} n'est pas une position valide dans choix")

    # Contrôle 4 : pas de choix en double
    if len(set(choix)) != len(choix):
        erreurs.append(f"Question {numero} : il y a des choix en double")

    return erreurs


def main():
    with open(FICHIER, encoding="utf-8") as fichier:
        questions = json.load(fichier)

    toutes_les_erreurs = []
    for numero, question in enumerate(questions, start=1):
        toutes_les_erreurs.extend(verifier_question(question, numero))

    if toutes_les_erreurs:
        print(f"ERREUR : {len(toutes_les_erreurs)} problème(s) dans {FICHIER}")
        for erreur in toutes_les_erreurs:
            print("  -", erreur)
        sys.exit(1)
    else:
        print(f"OK : {len(questions)} questions valides dans {FICHIER}")


main()