"""Vérifie toutes les banques de questions du site d'un coup.
Utilisé à la main avant un commit, et automatiquement par GitHub à chaque push."""
import json
import sys
from pathlib import Path

from valider_questions import verifier_question


def main():
    fichiers = sorted(Path("donnees").glob("*/*/*.json"))
    nombre_de_questions = 0
    fichiers_en_erreur = 0

    for chemin in fichiers:
        if chemin.name == "index.json":
            continue   # ce n'est pas une banque de questions
        with open(chemin, encoding="utf-8") as fichier:
            questions = json.load(fichier)

        erreurs = []
        for numero, question in enumerate(questions, start=1):
            erreurs.extend(verifier_question(question, numero))
        nombre_de_questions += len(questions)

        if erreurs:
            fichiers_en_erreur += 1
            print(f"❌ {chemin} : {len(erreurs)} problème(s)")
            for erreur in erreurs:
                print("   -", erreur)

    print(f"{nombre_de_questions} questions vérifiées.")
    if fichiers_en_erreur:
        print(f"ÉCHEC : {fichiers_en_erreur} fichier(s) à corriger.")
        sys.exit(1)
    print("Tout est bon ✅")


if __name__ == "__main__":
    main()