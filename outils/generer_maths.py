# Génère le fichier de questions de maths au format JSON
import json

# Une liste de dictionnaires : chaque dictionnaire est une question
questions = [
    {
        "enonce": "Combien font 7 × 8 ?",
        "choix": ["54", "56", "48", "64"],
        "bonneReponse": 1,
        "explication": "7 × 8 = 56. Astuce : 5, 6, 7, 8 → 56 = 7 × 8 !"
    },
    {
        "enonce": "Quel est le double de 45 ?",
        "choix": ["80", "85", "90", "95"],
        "bonneReponse": 2,
        "explication": "Le double, c'est 2 fois le nombre : 45 + 45 = 90."
    },
    {
        "enonce": "Quel est l'arrondi de 45,3 a l'entier le plus proche ?",
        "choix": ["45", "45,3", "46", "45,5"],
        "bonneReponse": 0,
        "explication": "L'arrondi à l'entier le plus proche de 45,3 est 45."
    },
    {
        "enonce": "Un triangle rectangle a un angle droit. Quel est son angle ?",
        "choix": ["90", "45", "60", "30"],
        "bonneReponse": 0,
        "explication": "Dans un triangle rectangle, l'angle droit mesure 90 degrés."
    },
    {
        "enonce": "Combien y a-t-il de côtés dans un hexagone ?",
        "choix": ["6", "7", "8", "9"],
        "bonneReponse": 0,
        "explication": "Un hexagone a 6 côtés."
    },
]

# Écriture du fichier
with open("donnees/maths.json", "w", encoding="utf-8") as fichier:
    json.dump(questions, fichier, ensure_ascii=False, indent=2)

print(f"{len(questions)} questions écrites dans donnees/maths.json")