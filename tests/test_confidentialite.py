"""Tests de la page « Mentions légales et confidentialité », et de la promesse qu'elle fait."""
from urllib.parse import urlparse

from playwright.sync_api import Page, expect


def test_le_lien_du_pied_de_page_ouvre_les_mentions_legales(page: Page, site):
    page.goto(site + "/index.html")

    page.get_by_role("link", name="Mentions légales et confidentialité").click()

    expect(page.locator("h1")).to_have_text("Mentions légales et confidentialité")


def test_l_adresse_de_contact_a_ete_remplie(page: Page, site):
    page.goto(site + "/mentions-legales.html")

    expect(page.locator("main")).not_to_contain_text("A-REMPLACER")


def test_les_pages_ne_contactent_aucun_service_exterieur(page: Page, site):
    """La page de confidentialité promet qu'aucun service extérieur n'est contacté :
    on note chaque fichier demandé par le navigateur et on vérifie qu'il vient du site."""
    adresses = []
    page.on("request", lambda requete: adresses.append(requete.url))

    page.goto(site + "/index.html")
    page.goto(site + "/niveau.html?niveau=p4")
    page.goto(site + "/cahier.html?niveau=p4&matiere=maths&theme=nombres")
    page.wait_for_load_state("networkidle")

    notre_site = urlparse(site).netloc
    exterieures = [a for a in adresses if urlparse(a).netloc != notre_site]
    assert exterieures == [], f"Fichiers demandés ailleurs que sur le site : {exterieures}"