"""Tests d'un quiz, avec une petite banque de questions préparée pour chaque test."""
import json

from playwright.sync_api import Page, expect

ADRESSE_DU_QUIZ = "/cahier.html?niveau=p4&matiere=maths&theme=nombres"


def remplacer_la_banque(page, questions):
    """Quand le site demande le fichier du thème « Nombres », Playwright lui répond
    avec nos questions à la place du vrai fichier : le test sait exactement ce qui s'affiche."""
    def repondre(route):
        route.fulfill(content_type="application/json", body=json.dumps(questions))
    page.route("**/donnees/p4/maths/nombres.json", repondre)


def test_qcm_bonne_reponse(page: Page, site):
    remplacer_la_banque(page, [
        {"type": "qcm", "enonce": "Combien font 2 + 3 ?", "choix": ["4", "5", "6", "7"],
         "bonneReponse": 1, "explication": "2 + 3 = 5."}
    ])
    page.goto(site + ADRESSE_DU_QUIZ)

    expect(page.locator("#enonce")).to_have_text("Combien font 2 + 3 ?")
    page.locator(".reponse", has_text="5").click()

    expect(page.locator("#verdict")).to_have_text("Bravo, c'est juste !")
    page.locator("#bouton-suivant").click()
    expect(page.locator("#score")).to_have_text("1 / 1")


def test_saisie_mauvaise_reponse(page: Page, site):
    remplacer_la_banque(page, [
        {"type": "saisie", "enonce": "Combien font 10 − 4 ?", "reponses": ["6"],
         "accents": "toleres", "explication": "10 − 4 = 6."}
    ])
    page.goto(site + ADRESSE_DU_QUIZ)

    page.locator(".saisie-champ").fill("7")
    page.locator(".saisie-valider").click()

    expect(page.locator("#verdict")).to_have_text("Pas tout à fait…")
    page.locator("#bouton-suivant").click()
    expect(page.locator("#score")).to_have_text("0 / 1")


def test_saisie_accepte_le_point_comme_la_virgule(page: Page, site):
    remplacer_la_banque(page, [
        {"type": "saisie", "enonce": "Combien coûte le cahier ?", "reponses": ["7,20 €"],
         "accents": "toleres", "explication": "Il coûte 7,20 €."}
    ])
    page.goto(site + ADRESSE_DU_QUIZ)

    page.locator(".saisie-champ").fill("7.20 €")
    page.locator(".saisie-valider").click()

    expect(page.locator("#verdict")).to_have_text("Bravo, c'est juste !")