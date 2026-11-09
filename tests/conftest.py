"""Réglages communs des tests : un petit serveur web qui sert le site pendant les tests."""
import functools
import http.server
import threading
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent   # le dossier du projet


@pytest.fixture(scope="session")
def site():
    """Démarre un serveur web local sur un port libre et renvoie son adresse."""
    gestionnaire = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(RACINE))
    serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestionnaire)
    fil = threading.Thread(target=serveur.serve_forever, daemon=True)
    fil.start()
    yield f"http://127.0.0.1:{serveur.server_port}"
    serveur.shutdown()