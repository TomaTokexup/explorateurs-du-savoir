# Ajoute les questions d'un brouillon relu à un fichier de thème publié
import argparse
import json
import sys

from valider_questions import verifier_question


def charger(chemin):
    """Lit un fichier JSON et renvoie son contenu."""
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def main():
    parser = argparse.ArgumentParser(description="Publie un brouillon relu dans un fichier de thème.")
    parser.add_argument("brouillon", help="ex. donnees/brouillon_p4_maths_operations.json")
    parser.add_argument("destination", help="ex. donnees/p4/maths/operations.json")
    args = parser.parse_args()

    nouvelles = charger(args.brouillon)
    existantes = charger(args.destination)
    a_ajouter = []

    # Étape 1 : écarter les doublons
    #  - fabriquer un set avec les énoncés des questions existantes
    enonces_existant = {q["enonce"] for q in existantes}

    #  - parcourir les nouvelles questions :
    for question in nouvelles:
        enonce = question["enonce"]
        if enonce in enonces_existant:
            print(f"Doublon écarté : {enonce}")
        else:
            a_ajouter.append(question)
            enonces_existant.add(enonce)

    # Étape 2 : valider l'ensemble AVANT d'écrire quoi que ce soit

    fusion = existantes + a_ajouter
    #  - vérifier chaque question de fusion avec verifier_question
    toutes_les_erreurs = []
    for numero, question in enumerate(fusion, start=1):
        toutes_les_erreurs.extend(verifier_question(question, numero))
    #  - s'il y a des erreurs : les afficher et sys.exit(1)  → le fichier publié reste intact
    if toutes_les_erreurs:
        print(f"ERREUR : {len(toutes_les_erreurs)} problème(s) dans le fichier fusionné")
        for erreur in toutes_les_erreurs:
            print("  -", erreur)
        sys.exit(1)

    # Étape 3 : écrire le fichier fusionné
    with open(args.destination, "w", encoding="utf-8") as fichier:
        json.dump(fusion, fichier, ensure_ascii=False, indent=2)

    print(f"{len(a_ajouter)} question(s) ajoutée(s) à {args.destination} "
          f"({len(fusion)} au total)")


if __name__ == "__main__":
    main()