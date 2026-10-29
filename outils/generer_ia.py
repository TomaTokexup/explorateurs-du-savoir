# Génère des questions avec l'IA, les contrôle, et garde celles qui sont valides
import json
import sys

import anthropic
from dotenv import load_dotenv

from valider_questions import verifier_question   # ta fonction !

THEME = "les fractions"
NIVEAU = "CM1"
NOMBRE = 10
FICHIER_SORTIE = "donnees/brouillon_ia.json"

# Le "system prompt" : les consignes permanentes données à l'IA
CONSIGNES = """Tu es un enseignant de l'école primaire française qui rédige des QCM de révision.

Règles :
- Chaque question a exactement 4 choix, dont une seule bonne réponse.
- Les mauvaises réponses correspondent à des erreurs que font vraiment les élèves.
- La position de la bonne réponse varie d'une question à l'autre.
- L'explication enseigne la méthode en une ou deux phrases simples ; elle ne se contente pas de répéter la réponse.
- Vocabulaire adapté à un enfant de 8 à 10 ans. Les unités sont toujours précisées.

Réponds UNIQUEMENT avec un tableau JSON, sans aucun texte avant ou après, au format :
[
  {"enonce": "...", "choix": ["...", "...", "...", "..."], "bonneReponse": 0, "explication": "..."}
]
"bonneReponse" est la position de la bonne réponse dans "choix", en comptant à partir de 0."""


def demander_questions():
    """Envoie la demande à l'IA et renvoie sa réponse en texte."""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=4000,
        system=CONSIGNES,
        messages=[
            {"role": "user", "content": f"Rédige {NOMBRE} questions de niveau {NIVEAU} sur {THEME}."}
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


def main():
    load_dotenv()
    texte = demander_questions()

    # Transformer le texte en liste Python (peut échouer si l'IA n'a pas respecté le format)
    try:
        questions = json.loads(texte)
    except json.JSONDecodeError as erreur:
        print("L'IA n'a pas renvoyé du JSON valide :", erreur)
        print("--- Réponse brute ---")
        print(texte)
        sys.exit(1)

    valides = []
    rejetees = []

    # À TOI : pour chaque question (numérotée à partir de 1), appelle verifier_question.
    #  - si la liste d'erreurs est vide  -> ajoute la question à "valides"
    #  - sinon -> affiche chaque erreur et ajoute la question à "rejetees"
    for numero, question in enumerate(questions, start=1):
        erreurs = verifier_question(question, numero)
        if not erreurs:
            valides.append(question)
        else:
            print(f"Question {numero} rejetée :")
            for erreur in erreurs:
                print("  -", erreur)
            rejetees.append(question)


    with open(FICHIER_SORTIE, "w", encoding="utf-8") as fichier:
        json.dump(valides, fichier, ensure_ascii=False, indent=2)

    print(f"{len(valides)} questions valides enregistrées dans {FICHIER_SORTIE}")
    print(f"{len(rejetees)} questions rejetées")


if __name__ == "__main__":
    main()