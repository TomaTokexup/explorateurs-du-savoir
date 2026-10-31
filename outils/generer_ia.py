# Génère des questions avec l'IA, les contrôle, et garde celles qui sont valides
import json
import sys
import argparse
import anthropic
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

def construire_consignes(niveau, titre_domaine, objectifs, nombre, nb_saisies):
    """Construit le 'system prompt' à partir des objectifs officiels."""
    liste_objectifs = "\n".join(f"- {objectif}" for objectif in objectifs)
    nb_qcm = nombre - nb_saisies
    return f"""Tu rédiges des exercices de révision pour des élèves de {niveau.upper()} des Écoles européennes (section française, enfants de 8 à 11 ans).

Domaine : {titre_domaine}
Objectifs officiels du programme pour ce niveau (syllabus des Écoles européennes, en anglais) :
{liste_objectifs}

Consignes générales :
- Chaque question évalue UN de ces objectifs. Varie les objectifs couverts d'une question à l'autre.
- Ne dépasse jamais le niveau fixé par ces objectifs.
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

    # 2. consignes = construire_consignes(...)
    consignes = construire_consignes(args.niveau, titre, objectifs, args.nombre, args.saisies)

    # 3. demande = f"Rédige les {args.nombre} questions sur le domaine « {titre} »."
    demande = f"Rédige les {args.nombre} questions sur le domaine « {titre} »."

    # 4. texte = demander_questions(consignes, demande)
    texte = demander_questions(consignes, demande)

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

    # 6. fichier de sortie : f"donnees/brouillon_{args.niveau}_{args.matiere}_{args.theme}.json"
    fichier_sortie = f"donnees/brouillon_{args.niveau}_{args.matiere}_{args.theme}.json"
    with open(fichier_sortie, "w", encoding="utf-8") as fichier:
        json.dump(valides, fichier, ensure_ascii=False, indent=2)

    print(f"{len(valides)} questions valides enregistrées dans {fichier_sortie}")
    print(f"{len(rejetees)} questions rejetées")


if __name__ == "__main__":
    main()