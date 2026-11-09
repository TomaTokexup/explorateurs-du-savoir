"""Tests de la programmation : la leçon, puis un exercice avec le robot."""
import json

from playwright.sync_api import Page, expect

ADRESSE = "/cahier.html?niveau=p4&matiere=programmation&theme=sequence"

LECON_DE_TEST = [
    {"titre": "Une leçon de test", "texte": "Un seul écran, pour vérifier que la leçon s'affiche."}
]

ROBOT_DE_TEST = {
    "type": "robot",
    "enonce": "Guide le robot jusqu'à l'étoile.",
    "grille": {"largeur": 4, "hauteur": 3},
    "depart": {"x": 0, "y": 1, "direction": "est"},
    "cible": {"x": 2, "y": 1},
    "blocs": ["avancer", "gauche", "droite"],
    "solution": ["avancer", "avancer"],
    "explication": "Le robot avance de 2 cases."
}


def preparer(page, lecon, questions):
    """Remplace la leçon et les exercices de l'étape « sequence » par ceux du test."""
    def envoyer(contenu):
        def repondre(route):
            route.fulfill(content_type="application/json", body=json.dumps(contenu))
        return repondre
    page.route("**/programmation/lecons/sequence.json", envoyer(lecon))
    page.route("**/programmation/sequence.json", envoyer(questions))


def passer_la_lecon(page):
    expect(page.locator("#lecon-titre")).to_have_text("Une leçon de test")
    page.locator("#lecon-suivant").click()   # dernier écran : « C'est parti : les exercices ! »


def test_le_robot_arrive_sur_l_etoile(page: Page, site):
    preparer(page, LECON_DE_TEST, [ROBOT_DE_TEST])
    page.goto(site + ADRESSE)
    passer_la_lecon(page)

    page.locator('.vitesse button[data-vitesse="rapide"]').click()
    page.locator(".palette .bloc-avancer").click()
    page.locator(".palette .bloc-avancer").click()
    expect(page.locator(".compteur-blocs")).to_have_text("Blocs : 2")
    page.locator(".actions-robot .bouton-lancer").click()

    expect(page.locator("#verdict")).to_have_text("Bravo, c'est juste !")


def test_le_robot_se_cogne_contre_le_bord(page: Page, site):
    preparer(page, LECON_DE_TEST, [ROBOT_DE_TEST])
    page.goto(site + ADRESSE)
    passer_la_lecon(page)

    page.locator('.vitesse button[data-vitesse="rapide"]').click()
    page.locator(".palette .bloc-gauche").click()      # le robot regarde vers le haut…
    page.locator(".palette .bloc-avancer").click()
    page.locator(".palette .bloc-avancer").click()     # … et la 2e case est hors de la grille
    page.locator(".actions-robot .bouton-lancer").click()

    expect(page.locator(".message-robot")).to_contain_text("Bong ! Le robot s'est cogné.")
    expect(page.locator(".programme .bloc.bug")).to_have_count(1)   # le bloc fautif est en rouge