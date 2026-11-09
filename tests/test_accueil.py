"""Tests de la page d'accueil."""
from playwright.sync_api import Page, expect


def test_accueil_affiche_les_trois_niveaux(page: Page, site):
    page.goto(site + "/index.html")

    expect(page).to_have_title("Explorateurs du Savoir")
    niveaux = page.locator("a.niveau")
    expect(niveaux).to_have_count(3)
    expect(niveaux.nth(0)).to_contain_text("P3")
    expect(niveaux.nth(1)).to_contain_text("P4")
    expect(niveaux.nth(2)).to_contain_text("P5")


def test_un_clic_sur_p4_ouvre_les_cahiers_de_p4(page: Page, site):
    page.goto(site + "/index.html")

    page.locator("a.niveau", has_text="P4").click()

    expect(page).to_have_url(site + "/niveau.html?niveau=p4")
    expect(page.locator(".cahier", has_text="Mathématiques")).to_be_visible()
    