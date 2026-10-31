// =========================================================
// Explorateurs du Savoir — script commun à toutes les pages
// =========================================================
//
// Parcours de l'élève :
//   index.html                                   → choix du niveau (P3, P4, P5)
//   niveau.html?niveau=p4                        → les cahiers (matières) du niveau
//   cahier.html?niveau=p4&matiere=maths          → le sommaire des thèmes
//   cahier.html?niveau=p4&matiere=maths&theme=nombres  → le quiz d'un thème
//   cahier.html?niveau=p4&matiere=maths&theme=melange  → révision mélangée
//
// Organisation des données (produites par les scripts Python) :
//   donnees/<niveau>/<matiere>/index.json     → sommaire : liste des thèmes
//   donnees/<niveau>/<matiere>/<theme>.json   → questions d'un thème
//
// Format du sommaire :
//   [ { "id": "nombres", "titre": "Nombres" }, ... ]   ("id" = nom du fichier)
// Format d'une question (voir la partie 5 pour les différents types) :
//   QCM    : { "type": "qcm", "enonce": "...", "choix": [...], "bonneReponse": 0, "explication": "..." }
//   Saisie : { "type": "saisie", "enonce": "...", "reponses": ["il va"], "accents": "stricts", "explication": "..." }
//
// Un cahier s'active tout seul dès que son index.json existe :
// pas besoin de modifier ce code pour ajouter une matière ou un thème.

// ---------- 1. Configuration : niveaux et matières (programme des Écoles européennes) ----------
const NIVEAUX = {
  p3: { nom: "P3", equivalent: "CE2" },
  p4: { nom: "P4", equivalent: "CM1" },
  p5: { nom: "P5", equivalent: "CM2" }
};

const MATIERES = [
  { id: "maths",         nom: "Mathématiques",       icone: "🔢" },
  { id: "francais",      nom: "Français",            icone: "📖", precision: "Langue 1" },
  { id: "anglais",       nom: "Anglais",             icone: "💬", precision: "Langue 2" },
  { id: "decouverte",    nom: "Découverte du monde", icone: "🌍" },
  { id: "programmation", nom: "Programmation",       icone: "🤖", precision: "Bonus" }
];

// Nombre de questions tirées au hasard à chaque partie, dans la banque de questions.
// S'il y en a moins dans la banque, on les prend toutes.
const NOMBRE_QUESTIONS_THEME = 10;
const NOMBRE_QUESTIONS_MELANGE = 15;

// ---------- 2. Outils ----------
const parametres = new URLSearchParams(window.location.search);

// Lit un fichier JSON. "async/await" : on attend la réponse sans bloquer la page.
async function lireJSON(chemin) {
  const reponse = await fetch(chemin);
  if (!reponse.ok) {
    throw new Error(chemin + " introuvable (" + reponse.status + ")");
  }
  return reponse.json();
}

// Mélange une liste (algorithme de Fisher-Yates) et renvoie une copie
function melanger(liste) {
  const copie = liste.slice();
  for (let i = copie.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copie[i], copie[j]] = [copie[j], copie[i]];
  }
  return copie;
}

function afficherErreur(message, erreur) {
  // Message pour l'adulte qui teste. Cause fréquente : page ouverte par
  // double-clic (file://) au lieu de passer par un serveur (python -m http.server).
  const zone = document.getElementById("progression");
  if (zone) zone.textContent = message;
  console.error(erreur);
}

// ---------- 3. Page "niveau" : les cahiers ----------
async function pageNiveau() {
  const idNiveau = parametres.get("niveau");
  const niveau = NIVEAUX[idNiveau];
  if (!niveau) {
    window.location.href = "index.html";   // niveau inconnu : retour à l'accueil
    return;
  }

  document.getElementById("titre-niveau").textContent = "Mes cahiers de " + niveau.nom;
  document.title = "Cahiers " + niveau.nom + " – Explorateurs du Savoir";

  const liste = document.getElementById("liste-cahiers");

  for (const matiere of MATIERES) {
    // Un cahier est disponible si son sommaire existe
    let disponible = true;
    try {
      await lireJSON("donnees/" + idNiveau + "/" + matiere.id + "/index.json");
    } catch (erreur) {
      disponible = false;
    }

    const cahier = document.createElement(disponible ? "a" : "div");
    cahier.className = "cahier " + matiere.id + (disponible ? "" : " bientot");
    if (disponible) {
      cahier.href = "cahier.html?niveau=" + idNiveau + "&matiere=" + matiere.id;
    }

    const etiquette = document.createElement("span");
    etiquette.className = "etiquette";
    etiquette.innerHTML =
      '<span class="icone" aria-hidden="true"></span><span class="nom"></span><span class="precision"></span>';
    etiquette.querySelector(".icone").textContent = matiere.icone;
    etiquette.querySelector(".nom").textContent = matiere.nom;
    etiquette.querySelector(".precision").textContent = matiere.precision || "";
    cahier.appendChild(etiquette);

    if (!disponible) {
      const tampon = document.createElement("span");
      tampon.className = "tampon";
      tampon.textContent = "Bientôt";
      cahier.appendChild(tampon);
    }

    const element = document.createElement("li");
    element.appendChild(cahier);
    liste.appendChild(element);
  }
}

// ---------- 4. Page "cahier" : sommaire ou quiz ----------
async function pageCahier() {
  const idNiveau = parametres.get("niveau");
  const idMatiere = parametres.get("matiere");
  const idTheme = parametres.get("theme");            // null si on affiche le sommaire
  const niveau = NIVEAUX[idNiveau];
  const matiere = MATIERES.find(function (m) { return m.id === idMatiere; });

  if (!niveau || !matiere) {
    window.location.href = "index.html";
    return;
  }

  // Couleur, titre et liens de retour
  document.body.classList.add(matiere.id);
  const lienCahier = "cahier.html?niveau=" + idNiveau + "&matiere=" + idMatiere;
  document.getElementById("retour").href = "niveau.html?niveau=" + idNiveau;
  document.getElementById("retour").textContent = "← Mes cahiers de " + niveau.nom;
  const titre = document.getElementById("titre-matiere");
  titre.querySelector("a").textContent = matiere.nom;
  titre.querySelector("a").href = lienCahier;
  document.getElementById("niveau-matiere").textContent = niveau.nom;
  document.getElementById("lien-sommaire").href = lienCahier;

  const dossier = "donnees/" + idNiveau + "/" + idMatiere + "/";

  try {
    const themes = await lireJSON(dossier + "index.json");

    // Pas de thème choisi : on affiche le sommaire
    if (idTheme === null) {
      document.title = matiere.nom + " " + niveau.nom + " – Explorateurs du Savoir";
      afficherSommaire(themes, lienCahier, dossier);
      return;
    }

    let banque;          // toutes les questions disponibles pour ce quiz
    let nombreParPartie; // combien on en tire à chaque partie
    let nomDuQuiz;

    if (idTheme === "melange") {
      // Révision mélangée : la banque regroupe les questions de TOUS les thèmes
      nomDuQuiz = "Révision mélangée";
      const listes = await Promise.all(themes.map(function (t) {
        return lireJSON(dossier + t.id + ".json");
      }));
      banque = listes.flat();
      nombreParPartie = NOMBRE_QUESTIONS_MELANGE;
    } else {
      const theme = themes.find(function (t) { return t.id === idTheme; });
      if (!theme) {
        throw new Error("thème « " + idTheme + " » absent du sommaire");
      }
      nomDuQuiz = theme.titre;
      banque = await lireJSON(dossier + theme.id + ".json");
      nombreParPartie = NOMBRE_QUESTIONS_THEME;
    }

    const sousTitre = document.getElementById("sous-titre");
    sousTitre.textContent = nomDuQuiz;
    sousTitre.hidden = false;
    document.title = nomDuQuiz + " – " + matiere.nom + " " + niveau.nom;

    lancerQuiz(banque, nombreParPartie);
  } catch (erreur) {
    afficherErreur("Impossible de charger les exercices : " + erreur.message, erreur);
  }
}

function afficherSommaire(themes, lienCahier, dossier) {
  document.getElementById("progression").textContent = "Choisis un thème, ou révise tout d'un coup.";
  document.getElementById("lien-melange").href = lienCahier + "&theme=melange";

  // Comme dans une table des matières : titre ........ nombre de questions
  const liste = document.getElementById("liste-themes");
  themes.forEach(function (theme) {
    const lien = document.createElement("a");
    lien.className = "chapitre";
    lien.href = lienCahier + "&theme=" + encodeURIComponent(theme.id);

    const titre = document.createElement("span");
    titre.className = "chapitre-titre";
    titre.textContent = theme.titre;

    const pointilles = document.createElement("span");
    pointilles.className = "chapitre-pointilles";

    const compte = document.createElement("span");
    compte.className = "chapitre-compte";
    lireJSON(dossier + theme.id + ".json")
      .then(function (questions) { compte.textContent = questions.length + " questions"; })
      .catch(function () { compte.textContent = "fichier manquant"; });

    lien.append(titre, pointilles, compte);
    const element = document.createElement("li");
    element.appendChild(lien);
    liste.appendChild(element);
  });
  document.getElementById("sommaire").hidden = false;
}

// ---------- 5. Le moteur de quiz ----------
// Chaque question a un "type" qui décide de son affichage et de sa correction :
//   "qcm"    → 4 boutons, une seule bonne réponse        (type par défaut si absent)
//   "saisie" → l'élève tape une réponse courte au clavier
let banqueDuQuiz = [];         // toutes les questions disponibles (lues dans le JSON)
let nombreParPartie = 10;      // combien on en tire au hasard à chaque partie
let questions = [];            // les questions de la partie en cours, préparées
let numeroQuestion = 0;        // index de la question affichée
let score = 0;                 // nombre de bonnes réponses

const ACCENTS = ["é", "è", "ê", "à", "â", "ç", "ù", "û", "ô", "î", "ï", "ë"];

function typeDe(question) {
  return question.type || "qcm";
}

// Prépare une question avant affichage. Pour un QCM : mélange les choix
// et recalcule la position de la bonne réponse. Les autres types sont gardés tels quels.
function preparerQuestion(question) {
  if (typeDe(question) !== "qcm") {
    return question;
  }
  const bonneReponseTexte = question.choix[question.bonneReponse];
  const choixMelanges = melanger(question.choix);
  return Object.assign({}, question, {
    choix: choixMelanges,
    bonneReponse: choixMelanges.indexOf(bonneReponseTexte)
  });
}

// Met une réponse tapée sous une forme "standard" avant de la comparer :
// minuscules, espaces en trop supprimés, ponctuation finale ignorée,
// apostrophe typographique ’ remplacée par '.
// Si les accents sont tolérés, ils sont aussi retirés (é → e).
function normaliser(texte, accentsToleres) {
  let resultat = texte
    .toLowerCase()
    .replace(/[’`]/g, "'")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[.!?;]+$/, "")
    .trim();
  if (accentsToleres) {
    resultat = resultat.normalize("NFD").replace(/[̀-ͯ]/g, "");
  }
  return resultat;
}

function lancerQuiz(banque, nombre) {
  banqueDuQuiz = banque;
  nombreParPartie = nombre;
  document.getElementById("zone-question").hidden = false;
  document.getElementById("bouton-suivant").addEventListener("click", questionSuivante);
  document.getElementById("bouton-recommencer").addEventListener("click", function () {
    document.getElementById("bilan").hidden = true;
    document.getElementById("zone-question").hidden = false;
    demarrer();
  });
  demarrer();
}

// Une nouvelle partie : on tire au hasard des questions dans la banque
// (un nouveau tirage à chaque fois qu'on clique sur "Recommencer")
function demarrer() {
  questions = melanger(banqueDuQuiz).slice(0, nombreParPartie).map(preparerQuestion);
  numeroQuestion = 0;
  score = 0;
  afficherQuestion();
}

function afficherQuestion() {
  const question = questions[numeroQuestion];

  document.getElementById("progression").textContent =
    "Question " + (numeroQuestion + 1) + " sur " + questions.length;
  document.getElementById("enonce").textContent = question.enonce;

  document.getElementById("reponses").innerHTML = "";
  document.getElementById("correction").hidden = true;
  document.getElementById("bouton-suivant").hidden = true;

  if (typeDe(question) === "saisie") {
    afficherSaisie(question);
  } else {
    afficherQcm(question);
  }
}

// --- Type "qcm" ---
function afficherQcm(question) {
  const reponses = document.getElementById("reponses");
  reponses.className = "reponses";
  question.choix.forEach(function (texteChoix, position) {
    const bouton = document.createElement("button");
    bouton.className = "reponse";
    bouton.textContent = texteChoix;
    bouton.addEventListener("click", function () {
      corrigerQcm(question, position);
    });
    reponses.appendChild(bouton);
  });
}

function corrigerQcm(question, positionChoisie) {
  // On colore les boutons et on les bloque (un seul essai)
  document.querySelectorAll("#reponses .reponse").forEach(function (bouton, position) {
    bouton.disabled = true;
    if (position === question.bonneReponse) {
      bouton.classList.add("juste");
    } else if (position === positionChoisie) {
      bouton.classList.add("faux");
    } else {
      bouton.classList.add("attenuee");
    }
  });
  afficherCorrection(question, positionChoisie === question.bonneReponse, "");
}

// --- Type "saisie" ---
function afficherSaisie(question) {
  const reponses = document.getElementById("reponses");
  reponses.className = "saisie";

  // Un formulaire : la touche Entrée valide la réponse
  const formulaire = document.createElement("form");
  formulaire.className = "saisie-formulaire";
  formulaire.innerHTML =
    '<input class="saisie-champ" type="text" autocomplete="off" autocapitalize="off" ' +
    'spellcheck="false" aria-label="Ta réponse" placeholder="Tape ta réponse">' +
    '<button class="saisie-valider" type="submit">Valider</button>';
  reponses.appendChild(formulaire);

  const champ = formulaire.querySelector(".saisie-champ");

  // Boutons d'accents, seulement si la réponse attendue contient des lettres
  const contientDesLettres = question.reponses.some(function (r) { return /\p{L}/u.test(r); });
  if (contientDesLettres) {
    const accents = document.createElement("div");
    accents.className = "saisie-accents";
    accents.setAttribute("aria-label", "Lettres accentuées");
    ACCENTS.forEach(function (lettre) {
      const bouton = document.createElement("button");
      bouton.type = "button";
      bouton.className = "accent";
      bouton.textContent = lettre;
      // On insère la lettre à l'endroit du curseur, puis on remet le curseur juste après
      bouton.addEventListener("click", function () {
        const debut = champ.selectionStart;
        const fin = champ.selectionEnd;
        champ.value = champ.value.slice(0, debut) + lettre + champ.value.slice(fin);
        champ.focus();
        champ.setSelectionRange(debut + 1, debut + 1);
      });
      accents.appendChild(bouton);
    });
    reponses.appendChild(accents);
  }

  formulaire.addEventListener("submit", function (evenement) {
    evenement.preventDefault();          // sinon le navigateur rechargerait la page
    if (champ.value.trim() === "") {
      champ.focus();                     // réponse vide : on ne corrige pas
      return;
    }
    corrigerSaisie(question, champ.value);
  });

  champ.focus();
}

function corrigerSaisie(question, texteTape) {
  const accentsToleres = question.accents === "toleres";
  const tape = normaliser(texteTape, accentsToleres);
  const estJuste = question.reponses.some(function (reponse) {
    return normaliser(reponse, accentsToleres) === tape;
  });

  // On bloque la saisie et on colore le champ
  const reponses = document.getElementById("reponses");
  reponses.querySelectorAll("input, button").forEach(function (element) {
    element.disabled = true;
  });
  reponses.querySelector(".saisie-champ").classList.add(estJuste ? "juste" : "faux");

  // Si c'est faux, on montre la réponse attendue avant l'explication
  const rappel = estJuste ? "" : "La bonne réponse : « " + question.reponses[0] + " ». ";
  afficherCorrection(question, estJuste, rappel);
}

// --- Commun à tous les types ---
function afficherCorrection(question, estJuste, rappel) {
  const correction = document.getElementById("correction");
  const verdict = document.getElementById("verdict");
  const boutonSuivant = document.getElementById("bouton-suivant");

  if (estJuste) {
    score = score + 1;
    verdict.textContent = "Bravo, c'est juste !";
    correction.className = "correction juste";
  } else {
    verdict.textContent = "Pas tout à fait…";
    correction.className = "correction faux";
  }
  document.getElementById("explication").textContent = rappel + question.explication;
  correction.hidden = false;

  const derniereQuestion = numeroQuestion === questions.length - 1;
  boutonSuivant.textContent = derniereQuestion ? "Voir mon score" : "Question suivante";
  boutonSuivant.hidden = false;
  boutonSuivant.focus();
}

function questionSuivante() {
  numeroQuestion = numeroQuestion + 1;
  if (numeroQuestion < questions.length) {
    afficherQuestion();
  } else {
    afficherBilan();
  }
}

function afficherBilan() {
  document.getElementById("zone-question").hidden = true;
  document.getElementById("progression").textContent = "Terminé !";
  document.getElementById("bilan").hidden = false;
  document.getElementById("score").textContent = score + " / " + questions.length;

  let message;
  if (score === questions.length) {
    message = "Parfait ! Tu es un vrai explorateur.";
  } else if (score >= questions.length / 2) {
    message = "Bien joué ! Encore un essai pour tout réussir ?";
  } else {
    message = "Continue de t'entraîner, tu vas y arriver !";
  }
  document.getElementById("message-bilan").textContent = message;
}

// ---------- 6. Démarrage selon la page ----------
// Chaque page HTML indique son type dans <body data-page="...">
const page = document.body.dataset.page;
if (page === "niveau") {
  pageNiveau();
} else if (page === "cahier") {
  pageCahier();
}
