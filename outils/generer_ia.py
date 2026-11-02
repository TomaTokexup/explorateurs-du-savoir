# Génère des questions avec l'IA, les contrôle, et garde celles qui sont valides
import hashlib
import json
import sys
import argparse
import anthropic

from pathlib import Path
from figures import (COMPOSANTS, DIRECTIONS, dessiner_angle, dessiner_barres, dessiner_billes, dessiner_camembert,
                     dessiner_circuit, dessiner_courbe, dessiner_frise, ecrire_annee, PAS_FRISE, dessiner_horloge, dessiner_polygone, dessiner_rectangle,
                     dessiner_repere, dessiner_rose, dessiner_venn, enregistrer)
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
    # 4. renvoyer quatre valeurs : le titre, les objectifs, les révisions et les défis du domaine
    domaine = programme["domaines"][theme]
    return (domaine["titre"],
            domaine["objectifs"],
            domaine.get("revisions", []),
            domaine.get("defis", []))

def charger_enonces_existants(niveau, matiere, theme):
    """Renvoie la liste des énoncés déjà publiés pour ce thème (vide si le thème n'existe pas)."""
    chemin = Path(f"donnees/{niveau}/{matiere}/{theme}.json")
    if not chemin.exists():
        return []
    with open(chemin, "r", encoding="utf-8") as fichier:
        return [q.get("enonce") for q in json.load(fichier)]

def construire_consignes(niveau, titre_domaine, objectifs, nombre, nb_saisies, enonces_existants, matiere, revisions, defis):
    """Construit le 'system prompt' à partir des objectifs officiels."""
    liste_objectifs = "\n".join(f"- {objectif}" for objectif in objectifs)
    nb_qcm = nombre - nb_saisies

    # En français, l'orthographe fait partie de l'exercice : accents stricts
    accents = "stricts" if matiere == "francais" else "toleres"
    liste_revisions = "\n".join(f"- {r}" for r in revisions) or "- (aucune)"
    liste_defis = "\n".join(f"- {d}" for d in defis) or "- (aucun)"

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

    # Consignes propres à la lecture : envoyées seulement pour ce domaine
    if titre_domaine == "Lecture":
        bloc_lecture = """
Texte support (questions de lecture) :
- Pour une question de compréhension, mets le texte dans un champ "texte", JAMAIS dans l'énoncé : l'énoncé contient seulement la question.
- Le texte est ORIGINAL (jamais un extrait de livre, ni une histoire connue racontée autrement), de 6 à 10 phrases, avec plusieurs personnages, lieux ou moments, pour que l'élève doive chercher et trier les informations.
- Le registre est soigné, comme dans un bon livre jeunesse pour 8-10 ans : vocabulaire riche et précis (« s'emmitoufler », « grommeler », « une ruelle »), adjectifs et comparaisons, phrases de longueurs variées dont certaines avec « qui », « quand », « parce que », « pourtant », et des dialogues entre guillemets. Évite les phrases plates du type « Paul a un chien. Le chien est noir. »
- Écris 2 ou 3 textes seulement, et pose 3 à 5 questions sur chacun, de la plus simple (repérer) à la plus difficile (déduire, interpréter). Recopie le même texte, mot pour mot, dans le champ "texte" de chacune de ses questions.
- Deux questions sur un même texte ne vérifient jamais la même information, et une réponse ne donne jamais la clé d'une autre question.
- Les mauvaises réponses sont plausibles : elles reprennent des éléments vrais du texte (un autre personnage, un autre moment, un autre objet) mais ne répondent pas à la question posée. Aucune réponse absurde.
- Au plus 2 questions où la réponse est un mot recopié tel quel du texte. Les autres demandent de relier deux informations, de deviner une information non écrite (indices), de reformuler, de retrouver ce que remplace un pronom, ou de remettre en ordre des événements qui ne sont pas racontés dans l'ordre.
- Toutes les questions portent sur la lecture : pas de question de conjugaison, de grammaire ou d'orthographe.
"""
    else:
        bloc_lecture = ""
    return f"""Tu rédiges des exercices de révision pour des élèves de {niveau.upper()} des Écoles européennes (section française, enfants de 8 à 11 ans).

Domaine : {titre_domaine}
Objectifs officiels du programme pour ce niveau (syllabus des Écoles européennes, en anglais) :
{liste_objectifs}
{bloc_existants}
Consignes générales :
- Chaque question évalue UN de ces objectifs. Varie les objectifs couverts d'une question à l'autre.
- Ne dépasse jamais le niveau fixé par ces objectifs.
- N'écris « ce », « cette » ou « cet » pour désigner un objet (« ce triangle », « cette figure ») que si la question a une figure.
- Utilise le vocabulaire employé en classe en France (« pavé droit » et non « cuboïde », « sommet » et non « vertex »), même si les objectifs officiels sont en anglais.
- Écris en français, avec des mots simples. Précise toujours les unités.
- L'explication est courte (une ou deux phrases) et naturelle, comme le dirait un enseignant. Pour une question de connaissance (sens d'un mot, définition, mot à apprendre), donne simplement le sens ou la règle, avec un exemple si besoin. Pour une question qui demande un raisonnement, montre la méthode. N'invente jamais de méthode artificielle, et ne te contente pas de répéter la réponse.
- Pars d'un exemple concret (de préférence illustré par une figure) plutôt que de demander une définition abstraite.
- Si l'énoncé contient une liste (par exemple des événements A, B et C), écris chaque élément sur sa propre ligne en les séparant par \\n dans le texte JSON.
- Dans "reponses", inutile de répéter une réponse avec une majuscule : le site ignore les majuscules.

Rédige exactement {nb_qcm} questions de type "qcm" et {nb_saisies} questions de type "saisie".

Type "qcm" :
- exactement 4 choix, dont une seule bonne réponse ;
- les mauvaises réponses correspondent à des erreurs fréquentes d'élèves ;
- "bonneReponse" est la position de la bonne réponse dans "choix", en comptant à partir de 0.

Type "saisie" (l'élève tape sa réponse au clavier) :
- réponse courte et fermée : un nombre, un mot ou au plus 4 mots, jamais une phrase ;
- l'énoncé est assez précis pour qu'une seule réponse soit possible ;
- "reponses" liste toutes les écritures acceptables de cette réponse (par exemple ["0,5", "0.5"] ou ["1 200", "1200"]) ;
- "accents" vaut "{accents}".

Révisions et défis :
- Environ une question sur dix est une RÉVISION d'une notion des années précédentes :
{liste_revisions}
- Environ une question sur dix est un DÉFI, un peu au-dessus du niveau, sur une notion de l'année suivante ; ajoute alors "defi": true à cette question :
{liste_defis}
- N'oublie JAMAIS "defi": true sur une question qui porte sur une notion de l'année suivante.

Astuces (rares) :
- Ajoute un champ "astuce" à 3 questions AU PLUS sur l'ensemble, seulement quand un geste ou un outil concret aide vraiment l'élève à trouver seul.
- Une astuce est un conseil pratique : un outil (cahier de brouillon, dictionnaire, règle ; par exemple, pour un mot difficile : « Cherche ce mot dans ton dictionnaire. »), un geste (poser l'opération, dessiner, compter sur ses doigts), ou une stratégie de vérification (remplacer le sujet par « il » ou « ils », réciter la conjugaison, relire le texte).
- Une astuce n'est PAS un rappel de leçon (une règle, une liste de terminaisons) : les règles vont dans l'explication.
- L'astuce ne doit jamais permettre de trouver la réponse sans réfléchir : elle ne désigne pas un choix par sa terminaison, sa ponctuation ou sa position, et ne reprend pas l'indice déjà présent dans l'énoncé.

{bloc_lecture}
Autres consignes :
- En conjugaison, une saisie attend le pronom et le verbe (par exemple « nous irons »).

Figures (facultatif, surtout en géométrie) :
- Tu peux ajouter à une question un champ "figure" quand un dessin aide l'élève. Formes disponibles :
  {{"forme": "angle", "mesure": <nombre entier de 1 à 180>}}
  {{"forme": "polygone", "cotes": <nombre entier de 3 à 10>}}
  {{"forme": "horloge", "heures": <entier de 1 à 12>, "minutes": <multiple de 5, de 0 à 55>}}  (horloge à aiguilles)
  {{"forme": "repere", "x": <entier de 0 à 6>, "y": <entier de 0 à 6>}}  (quadrillage avec un point nommé A)
  {{"forme": "rose", "direction": "N" | "NE" | "E" | "SE" | "S" | "SO" | "O" | "NO"}}  (rose des vents où seul le nord est écrit ; une flèche rouge montre la direction)
  {{"forme": "rectangle", "longueur": <entier>, "largeur": <entier inférieur ou égal>, "unite": "mm" | "cm" | "m"}}  (rectangle avec ses deux dimensions écrites)
- L'énoncé parle alors de la figure (« cet angle », « cette horloge », « le point A », « la flèche rouge ») et ne donne pas l'information que la figure montre (mesure, nombre de côtés, heure, coordonnées, direction).
  {{"forme": "barres", "titre": "...", "etiquettes": ["...", ...], "valeurs": [<entiers>]}}  (diagramme en barres, 2 à 6 barres)
  {{"forme": "courbe", "titre": "...", "etiquettes": ["...", ...], "valeurs": [<entiers>]}}  (graphique en ligne, ex. une valeur par mois)
  {{"forme": "camembert", "titre": "...", "etiquettes": ["...", ...], "valeurs": [<entiers>]}}  (diagramme circulaire avec légende ; les valeurs ne sont pas écrites sur le dessin)
  {{"forme": "billes", "rouges": <entier>, "bleues": <entier>, "vertes": <entier>, "jaunes": <entier>}}  (sac de billes de couleur, pour le hasard et les probabilités ; 18 billes au plus)
  {{"forme": "venn", "titre_a": "...", "titre_b": "...", "seulement_a": [...], "commun": [...], "seulement_b": [...]}}  (diagramme de Venn à deux cercles ; les éléments sont des mots courts, par exemple des prénoms ; 4 par zone au plus)
  Pour les diagrammes : titre de 30 caractères au plus, étiquettes de 12 caractères au plus (abrège : « Lun », « Jan »), valeurs entières et faciles à lire.
- Pour le rectangle, la figure donne les dimensions : la question porte sur un calcul (périmètre, aire), jamais sur la lecture des dimensions.
  {{"forme": "circuit", "composants": [...], "court_circuit": false, "objet": "..."}}  (circuit électrique en boucle, dessiné avec les symboles de l'école)
    composants : 1 à 4 éléments parmi "pile", "lampe", "moteur", "interrupteur-ouvert", "interrupteur-ferme", "coupure" (fil débranché), "objet" (objet à tester, conducteur ou isolant).
    "court_circuit": true ajoute un fil qui relie directement les deux bornes de la première lampe. "objet" (20 caractères au plus) n'est utile qu'avec le composant "objet", par exemple "clé en fer" ou "règle en plastique".
    Le dessin ne montre jamais si la lampe brille : demande à l'élève de le prévoir et de l'expliquer (circuit fermé ou ouvert, court-circuit, conducteur ou isolant).
  {{"forme": "frise", "debut": <entier>, "fin": <entier>, "pas": <entier>, "evenements": [{{"date": <entier>, "texte": "..."}}], "periodes": false}}  (frise chronologique)
    Les années avant J.-C. sont négatives (-52 pour 52 av. J.-C.). "pas" parmi 1, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000 ; début et fin sont des multiples du pas, avec 2 à 10 graduations.
    1 à 4 événements, chacun avec un texte de 14 caractères au plus ; un seul événement peut avoir le texte "?" (la date ou l'événement à trouver).
    "periodes": true colore les grandes périodes (Antiquité jusqu'en 476, Moyen Âge de 476 à 1492, Temps modernes de 1492 à 1789, Époque contemporaine depuis 1789).
    Utilise les dates retenues à l'école en France, et ne donne pas dans l'énoncé l'information que la frise montre.
- N'utilise aucune autre forme, et n'écris jamais de champ "image" toi-même.

Réponds UNIQUEMENT avec un tableau JSON, sans aucun texte avant ou après :
[
  {{"type": "qcm", "enonce": "...", "choix": ["...", "...", "...", "..."], "bonneReponse": 0, "explication": "..."}},
  {{"type": "saisie", "enonce": "...", "reponses": ["..."], "accents": "{accents}", "explication": "..."}}
]"""

def demander_questions(consignes, demande):
    """Envoie la demande à l'IA et renvoie sa réponse en texte."""
    client = anthropic.Anthropic()
    # Streaming : obligatoire pour les longues réponses (max_tokens élevé).
    # get_final_message() attend la fin et renvoie le même objet "message" qu'avant.
    with client.messages.stream(
        model="claude-haiku-5-5",
        max_tokens=32000,
        system=consignes,
        messages=[
            {"role": "user", "content": demande}
        ],
    ) as flux:
        message = flux.get_final_message()
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

def verifier_serie(etiquettes, valeurs, titre):
    """Contrôle les données d'un diagramme (barres, courbe, camembert). Lève une ValueError si invalides."""
    if not isinstance(etiquettes, list) or not isinstance(valeurs, list):
        raise ValueError("'etiquettes' et 'valeurs' doivent être des listes")
    if not 2 <= len(etiquettes) <= 6 or len(etiquettes) != len(valeurs):
        raise ValueError("il faut de 2 à 6 étiquettes, et autant de valeurs que d'étiquettes")
    for etiquette in etiquettes:
        if not isinstance(etiquette, str) or not 1 <= len(etiquette) <= 12:
            raise ValueError(f"étiquette invalide (texte de 1 à 12 caractères) : {etiquette!r}")
    for valeur in valeurs:
        if not isinstance(valeur, int) or not 0 <= valeur <= 1000:
            raise ValueError(f"valeur invalide (entier de 0 à 1000) : {valeur!r}")
    if max(valeurs) == 0:
        raise ValueError("toutes les valeurs sont nulles")
    if not isinstance(titre, str) or len(titre) > 30:
        raise ValueError(f"titre invalide (texte de 30 caractères au plus) : {titre!r}")


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

    elif forme in ("barres", "courbe", "camembert"):
        etiquettes = description.get("etiquettes")
        valeurs = description.get("valeurs")
        titre = description.get("titre", "")
        verifier_serie(etiquettes, valeurs, titre)
        fonction = {"barres": dessiner_barres, "courbe": dessiner_courbe, "camembert": dessiner_camembert}[forme]
        svg = fonction(etiquettes, valeurs, titre)
        # Nom de fichier unique pour ces données : un court « résumé » (hash) du contenu
        empreinte = hashlib.md5(json.dumps(description, sort_keys=True).encode("utf-8")).hexdigest()[:8]
        nom = f"{forme}-{empreinte}"
        alt = {"barres": "Un diagramme en barres", "courbe": "Un graphique en ligne",
               "camembert": "Un diagramme circulaire"}[forme]

    elif forme == "billes":
        nombres = {couleur: description.get(couleur, 0) for couleur in ("rouges", "bleues", "vertes", "jaunes")}
        for couleur, nombre in nombres.items():
            if not isinstance(nombre, int) or not 0 <= nombre <= 12:
                raise ValueError(f"nombre de billes {couleur} invalide (entier de 0 à 12) : {nombre!r}")
        if not 1 <= sum(nombres.values()) <= 18:
            raise ValueError("le sac doit contenir entre 1 et 18 billes")
        svg = dessiner_billes(**nombres)
        nom = "billes-" + "-".join(str(n) for n in nombres.values())
        alt = "Un sac de billes de couleur"

    elif forme == "venn":
        for cle in ("titre_a", "titre_b"):
            titre = description.get(cle)
            if not isinstance(titre, str) or not 1 <= len(titre) <= 14:
                raise ValueError(f"{cle} invalide (texte de 1 à 14 caractères) : {titre!r}")
        zones = [description.get(cle, []) for cle in ("seulement_a", "commun", "seulement_b")]
        for zone in zones:
            if not isinstance(zone, list) or len(zone) > 4:
                raise ValueError("chaque zone du diagramme de Venn doit être une liste de 4 éléments au plus")
            for element in zone:
                if not isinstance(element, str) or not 1 <= len(element) <= 10:
                    raise ValueError(f"élément de Venn invalide (texte de 1 à 10 caractères) : {element!r}")
        svg = dessiner_venn(description["titre_a"], description["titre_b"], *zones)
        empreinte = hashlib.md5(json.dumps(description, sort_keys=True).encode("utf-8")).hexdigest()[:8]
        nom = f"venn-{empreinte}"
        alt = "Un diagramme de Venn à deux cercles"

    elif forme == "circuit":
        composants = description.get("composants")
        if not isinstance(composants, list) or not 1 <= len(composants) <= 4:
            raise ValueError(f"composants invalides (liste de 1 à 4 éléments) : {composants!r}")
        for composant in composants:
            if composant not in COMPOSANTS:
                raise ValueError(f"composant inconnu : {composant!r}")
        court_circuit = description.get("court_circuit", False)
        if not isinstance(court_circuit, bool) or (court_circuit and "lampe" not in composants):
            raise ValueError("court_circuit doit valoir true ou false, et il faut une lampe pour un court-circuit")
        objet = description.get("objet", "")
        if "objet" in composants and (not isinstance(objet, str) or not 1 <= len(objet) <= 20):
            raise ValueError(f"nom de l'objet à tester invalide (texte de 1 à 20 caractères) : {objet!r}")
        svg = dessiner_circuit(composants, court_circuit, objet)
        empreinte = hashlib.md5(json.dumps(description, sort_keys=True).encode("utf-8")).hexdigest()[:8]
        nom = f"circuit-{empreinte}"
        # Texte alternatif : décrit le circuit pour un élève qui ne voit pas l'image
        noms_alt = {"pile": "une pile", "lampe": "une lampe", "moteur": "un moteur",
                    "interrupteur-ouvert": "un interrupteur ouvert", "interrupteur-ferme": "un interrupteur fermé",
                    "coupure": "un fil débranché", "objet": f"un objet à tester ({objet})"}
        alt = "Un circuit électrique avec " + ", ".join(noms_alt[c] for c in composants)
        if court_circuit:
            alt += ", et un fil qui relie directement les deux bornes de la lampe"

    elif forme == "frise":
        debut, fin, pas = description.get("debut"), description.get("fin"), description.get("pas")
        for valeur in (debut, fin, pas):
            if not isinstance(valeur, int) or isinstance(valeur, bool):
                raise ValueError(f"debut, fin et pas doivent être des nombres entiers : {valeur!r}")
        if pas not in PAS_FRISE or debut >= fin or debut % pas or fin % pas or not 2 <= (fin - debut) // pas <= 10:
            raise ValueError(f"frise invalide : de {debut} à {fin} tous les {pas} ans "
                             f"(pas parmi {PAS_FRISE}, début et fin multiples du pas, 2 à 10 graduations)")
        evenements = description.get("evenements")
        if not isinstance(evenements, list) or not 1 <= len(evenements) <= 4:
            raise ValueError("evenements doit être une liste de 1 à 4 événements")
        liste = []
        for evenement in evenements:
            if not isinstance(evenement, dict):
                raise ValueError(f"événement invalide : {evenement!r}")
            date, texte = evenement.get("date"), evenement.get("texte")
            if not isinstance(date, int) or not debut <= date <= fin:
                raise ValueError(f"date d'événement invalide (entier entre {debut} et {fin}) : {date!r}")
            if not isinstance(texte, str) or not 1 <= len(texte) <= 14:
                raise ValueError(f"texte d'événement invalide (1 à 14 caractères) : {texte!r}")
            liste.append((date, texte))
        if sum(1 for _, texte in liste if texte == "?") > 1:
            raise ValueError("une frise contient au plus un « ? »")
        periodes = description.get("periodes", False)
        if not isinstance(periodes, bool):
            raise ValueError("periodes doit valoir true ou false")
        svg = dessiner_frise(debut, fin, pas, liste, periodes)
        empreinte = hashlib.md5(json.dumps(description, sort_keys=True).encode("utf-8")).hexdigest()[:8]
        nom = f"frise-{empreinte}"
        alt = f"Une frise chronologique de {ecrire_annee(debut)} à {ecrire_annee(fin)}"
        noms = [texte for _, texte in sorted(liste) if texte != "?"]
        if noms:
            alt += ", avec : " + ", ".join(noms)
        if any(texte == "?" for _, texte in liste):
            alt += ", et un point rouge marqué « ? »"

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

    titre, objectifs, revisions, defis = charger_objectifs(args.niveau, args.matiere, args.theme)

    enonces_existants = charger_enonces_existants(args.niveau, args.matiere, args.theme)
    enonces_existants = charger_enonces_existants(args.niveau, args.matiere, args.theme)
    print(f"{len(enonces_existants)} question(s) déjà publiée(s) transmise(s) à l'IA")

    consignes = construire_consignes(args.niveau, titre, objectifs, args.nombre, args.saisies, enonces_existants, args.matiere, revisions, defis)

    demande = f"Rédige les {args.nombre} questions sur le domaine « {titre} »."

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
        # Si l'IA a décrit une figure, Python la dessine ("figure": null = pas de figure)
        description = question.pop("figure", None)
        if description is not None:
            try:
                question["image"], question["alt"] = creer_figure(description, args.niveau, args.matiere)
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

    nb_astuces = sum(1 for question in valides if "astuce" in question)
    if nb_astuces > 3:
        print(f"Attention : {nb_astuces} astuces, plus que les 3 demandées. À trier pendant la relecture.")

    # 6. fichier de sortie : f"donnees/brouillon_{args.niveau}_{args.matiere}_{args.theme}.json"
    fichier_sortie = f"donnees/brouillon_{args.niveau}_{args.matiere}_{args.theme}.json"
    with open(fichier_sortie, "w", encoding="utf-8") as fichier:
        json.dump(valides, fichier, ensure_ascii=False, indent=2)

    print(f"{len(valides)} questions valides enregistrées dans {fichier_sortie}")
    print(f"{len(rejetees)} questions rejetées")


if __name__ == "__main__":
    main()