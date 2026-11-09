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
//            + "majuscules": "strictes" (sinon les majuscules sont ignorées)
//            + "phrase": true pour une réponse en phrase complète (anglais)
//   Champs facultatifs, pour tous les types :
//     "image": "images/p4/maths/angle-120.svg", "alt": "description"   → une figure
//     "texte": "Un court texte à lire…"                               → texte support (lecture)
//     "astuce": "Prends ton cahier pour poser l'opération !"            → coup de pouce de méthode
//     "defi": true                                                     → badge « ⭐ Défi »
//   Association : { "type": "association", "enonce": "Relie…", "paires": [["le cœur", "pompe le sang"], …], "explication": "..." }
//   Ordre       : { "type": "ordre", "enonce": "Range…", "elements": ["1er", "2e", "3e"], "explication": "..." }
//                 ("elements" est écrit dans le BON ordre ; le site le mélange)
//   Vrai ou faux : { "type": "vraifaux", "enonce": "Une affirmation.", "vrai": true, "explication": "..." }
//   Robot       : voir la partie 5 ter (programmation), avec les leçons
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
  // Le programme de français est organisé par tranches (P1-P2, P3-P4, P5) :
  // la P3 et la P4 partagent la même banque de questions.
  { id: "francais",      nom: "Français",            icone: "📖", precision: "Langue 1",
    tranches: { p3: "p3-p4", p4: "p3-p4", p5: "p5" } },
  // Le programme d'anglais (Langue 2) est organisé par niveaux européens (A1, A2), pas par année :
  // une seule banque de questions pour la P3, la P4 et la P5.
  { id: "anglais",       nom: "Anglais",             icone: "💬", precision: "Langue 2",
    tranches: { p3: "p3-p5", p4: "p3-p5", p5: "p3-p5" } },
  { id: "decouverte",    nom: "Découverte du monde", icone: "🌍" },
  // La programmation n'est pas au programme de l'école : un seul parcours, commun à la P3, la P4 et la P5
  // "parcours" : des étapes à suivre dans l'ordre, sans révision mélangée ni série Vrai ou faux
  { id: "programmation", nom: "Programmation",       icone: "🤖", precision: "Bonus",
    tranches: { p3: "p3-p5", p4: "p3-p5", p5: "p3-p5" }, parcours: true }
];

// Nombre de questions tirées au hasard à chaque partie, dans la banque de questions.
// S'il y en a moins dans la banque, on les prend toutes.
const NOMBRE_QUESTIONS_THEME = 10;
const NOMBRE_QUESTIONS_MELANGE = 15;
// Série Vrai ou faux : à partir de ce nombre d'affirmations (type "vraifaux") dans la matière,
// on n'utilise plus les QCM transformés
const SEUIL_VRAIFAUX = 20;

// Niveau réel des questions « Défi », selon le dossier de données (niveau ou tranche).
// Exemple : en français P3-P4, les défis sont des notions de P5.
const NIVEAU_DES_DEFIS = { "p3": "P4", "p4": "P5", "p3-p4": "P5", "p5": "S1" };

// ---------- 2. Outils ----------

// Dossier des données d'une matière pour un niveau.
// Par défaut : donnees/<niveau>/<matiere>/ ; si la matière a des tranches : donnees/<tranche>/<matiere>/
function groupeDonnees(idNiveau, matiere) {
  return (matiere.tranches && matiere.tranches[idNiveau]) || idNiveau;
}

function dossierDonnees(idNiveau, matiere) {
  return "donnees/" + groupeDonnees(idNiveau, matiere) + "/" + matiere.id + "/";
}

// Typographie française : espace insécable (\u00A0) entre les guillemets et leur contenu,
// et avant ? ! : ;  → le navigateur ne peut plus couper la ligne à ces endroits.
function typographie(texte) {
  return String(texte)
    .replace(/«\s*/g, "«\u00A0")
    .replace(/\s*»/g, "\u00A0»")
    .replace(/ ([?!:;])/g, "\u00A0$1");
}

// Écrit un texte dans un élément, avec la bonne typographie.
// Les courts passages entre « » (un mot, un petit groupe de mots) sont mis
// dans un <span class="cite"> qui ne se coupe jamais en fin de ligne.
// On construit les nœuds un par un (pas d'innerHTML) : aucun risque d'injection de code.
function ecrireTexte(element, texte) {
  element.textContent = "";
  const morceaux = typographie(texte || "").split(/(«[^«»]*»)/);
  morceaux.forEach(function (morceau) {
    if (morceau.startsWith("«") && morceau.length <= 25) {
      const cite = document.createElement("span");
      cite.className = "cite";
      cite.textContent = morceau;
      element.appendChild(cite);
    } else if (morceau !== "") {
      element.appendChild(document.createTextNode(morceau));
    }
  });
}
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

// ---------- 2 bis. Mémoire du navigateur, étoiles et petites fêtes ----------
// Le navigateur garde quelques nombres (records, étoiles) dans localStorage.
// Il peut être indisponible (navigation privée, réglages) : on fait alors comme si c'était 0.
function lireNombre(cle) {
  try {
    return Number(localStorage.getItem(cle)) || 0;
  } catch (erreur) {
    return 0;
  }
}

function ecrireNombre(cle, valeur) {
  try {
    localStorage.setItem(cle, String(valeur));
  } catch (erreur) {
    // rien d'enregistré, ce n'est pas grave
  }
}

// Étoiles gagnées sur un thème : 1 dès la moitié, 2 dès 80 %, 3 pour un sans-faute
function etoilesPour(bonnes, total) {
  if (total === 0) return 0;
  if (bonnes === total) return 3;
  if (bonnes / total >= 0.8) return 2;
  if (bonnes / total >= 0.5) return 1;
  return 0;
}

function cleEtoilesDe(idNiveau, idMatiere, idTheme) {
  return "etoiles-" + idNiveau + "-" + idMatiere + "-" + idTheme;
}

// Trois étoiles, pleines ou vides (ex. ★★☆ pour 2)
function creerEtoiles(nombre) {
  const bloc = document.createElement("span");
  bloc.className = "etoiles";
  bloc.setAttribute("role", "img");   // un « dessin » d'étoiles, que le lecteur d'écran lit grâce à son étiquette
  bloc.setAttribute("aria-label", nombre + " étoile" + (nombre > 1 ? "s" : "") + " sur 3");
  for (let i = 0; i < 3; i++) {
    const etoile = document.createElement("span");
    etoile.className = "etoile" + (i < nombre ? " pleine" : "");
    etoile.setAttribute("aria-hidden", "true");
    etoile.textContent = "★";
    bloc.appendChild(etoile);
  }
  return bloc;
}

// Si l'enfant a demandé « moins d'animations » à son appareil, on ne fait pas la fête à l'écran
function animationsReduites() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Une gerbe de petites étoiles qui jaillit d'un élément (bonne réponse)
function gerbeEtoiles(element) {
  if (animationsReduites() || !element) return;
  const cadre = element.getBoundingClientRect();
  for (let i = 0; i < 8; i++) {
    const etincelle = document.createElement("span");
    etincelle.className = "etincelle";
    etincelle.textContent = "★";
    const angle = (i / 8) * 2 * Math.PI;
    etincelle.style.left = (cadre.left + 30) + "px";
    etincelle.style.top = (cadre.top + cadre.height / 2) + "px";
    etincelle.style.setProperty("--dx", Math.round(Math.cos(angle) * 60) + "px");
    etincelle.style.setProperty("--dy", Math.round(Math.sin(angle) * 45) + "px");
    document.body.appendChild(etincelle);
    setTimeout(function () { etincelle.remove(); }, 800);
  }
}

// Une pluie de confettis (beau score, nouveau record)
function confettis() {
  if (animationsReduites()) return;
  const couleurs = ["#2f6fdb", "#d9433a", "#7a4cc2", "#2e9e6a", "#ffcf3f", "#ff8a3d"];
  for (let i = 0; i < 70; i++) {
    const morceau = document.createElement("span");
    morceau.className = "confetti";
    morceau.style.left = Math.random() * 100 + "vw";
    morceau.style.background = couleurs[i % couleurs.length];
    morceau.style.animationDelay = Math.random() * 0.6 + "s";
    morceau.style.animationDuration = 1.8 + Math.random() * 1.4 + "s";
    morceau.style.setProperty("--derive", Math.round(Math.random() * 160 - 80) + "px");
    document.body.appendChild(morceau);
    setTimeout(function () { morceau.remove(); }, 4000);
  }
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
    let themes = [];
    try {
      themes = await lireJSON(dossierDonnees(idNiveau, matiere) + "index.json");
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

    // Pastille des étoiles gagnées dans ce cahier (seulement s'il y en a)
    const gagnees = themes.reduce(function (somme, theme) {
      return somme + lireNombre(cleEtoilesDe(idNiveau, matiere.id, theme.id));
    }, 0);
    if (gagnees > 0) {
      const pastille = document.createElement("span");
      pastille.className = "cahier-etoiles";
      pastille.textContent = "★ " + gagnees + " / " + themes.length * 3;
      pastille.setAttribute("aria-label", gagnees + " étoiles gagnées sur " + themes.length * 3);
      cahier.appendChild(pastille);
    }

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

  const dossier = dossierDonnees(idNiveau, matiere);
  niveauDesDefis = NIVEAU_DES_DEFIS[groupeDonnees(idNiveau, matiere)] || "";

  try {
    const themes = await lireJSON(dossier + "index.json");

    // Un seul thème (l'anglais, par exemple) : pas besoin de sommaire, on lance directement le quiz
    if (idTheme === null && themes.length === 1) {
      window.location.replace(lienCahier + "&theme=" + themes[0].id);
      return;
    }

    // Pas de thème choisi : on affiche le sommaire
    if (idTheme === null) {
      document.title = matiere.nom + " " + niveau.nom + " – Explorateurs du Savoir";
      afficherSommaire(themes, lienCahier, dossier, matiere);
      return;
    }

    // Série « Vrai ou faux » : un jeu à part, qui puise dans tous les thèmes
    if (idTheme === "vraifaux") {
      const sousTitre = document.getElementById("sous-titre");
      sousTitre.textContent = "Série Vrai ou faux";
      sousTitre.hidden = false;
      document.title = "Vrai ou faux – " + matiere.nom + " " + niveau.nom;
      const listes = await Promise.all(themes.map(function (t) {
        return lireJSON(dossier + t.id + ".json");
      }));
      const toutes = listes.flat();
      // Les affirmations écrites exprès (type "vraifaux") sont plus naturelles que les QCM transformés.
      // Tant qu'il y en a peu, on complète avec les QCM ; quand il y en a assez, on n'utilise qu'elles.
      const affirmations = toutes.filter(function (q) { return typeDe(q) === "vraifaux"; });
      const qcm = toutes.filter(function (q) { return typeDe(q) === "qcm"; });
      const banque = affirmations.length >= SEUIL_VRAIFAUX ? affirmations : affirmations.concat(qcm);
      lancerSerie(banque, "record-vraifaux-" + idNiveau + "-" + idMatiere);
      return;
    }

    let banque;          // toutes les questions disponibles pour ce quiz
    let lecon = null;    // la leçon du thème, s'il y en a une (programmation)
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
      cleEtoiles = cleEtoilesDe(idNiveau, idMatiere, theme.id);
      banque = await lireJSON(dossier + theme.id + ".json");
      nombreParPartie = NOMBRE_QUESTIONS_THEME;
      // Les leçons n'existent que dans les cahiers « parcours » (programmation) ; ailleurs, on ne
      // les cherche même pas (sinon le navigateur note une erreur 404 à chaque quiz).
      // Une leçon reste facultative : si le fichier n'existe pas, on passe directement aux exercices.
      if (matiere.parcours) {
        lecon = await lireJSON(dossier + "lecons/" + theme.id + ".json").catch(function () { return null; });
      }
    }

    const sousTitre = document.getElementById("sous-titre");
    sousTitre.textContent = nomDuQuiz;
    sousTitre.hidden = false;
    document.title = nomDuQuiz + " – " + matiere.nom + " " + niveau.nom;

    if (!lecon) {
      lancerQuiz(banque, nombreParPartie);
      return;
    }
    // Avec une leçon : on la montre d'abord, puis les exercices. Le bouton « Revoir la leçon »
    // la rouvre à tout moment, et on revient ensuite exactement là où on en était.
    brancherLecon();
    const boutonLecon = document.getElementById("bouton-lecon");
    boutonLecon.addEventListener("click", function () {
      const zones = [document.getElementById("zone-question"), document.getElementById("bilan")];
      const visibles = zones.filter(function (zone) { return !zone.hidden; });
      const progression = document.getElementById("progression").textContent;
      zones.forEach(function (zone) { zone.hidden = true; });
      boutonLecon.hidden = true;
      ouvrirLecon(lecon, function () {
        visibles.forEach(function (zone) { zone.hidden = false; });
        document.getElementById("progression").textContent = progression;
        boutonLecon.hidden = false;
      }, "Reprendre les exercices");
      window.scrollTo(0, 0);
    });
    ouvrirLecon(lecon, function () {
      boutonLecon.hidden = false;
      lancerQuiz(banque, nombreParPartie);
      window.scrollTo(0, 0);
    }, "C'est parti : les exercices !");
  } catch (erreur) {
    afficherErreur("Impossible de charger les exercices : " + erreur.message, erreur);
  }
}

function afficherSommaire(themes, lienCahier, dossier, matiere) {
  document.getElementById("progression").textContent = "Choisis un thème, ou révise tout d'un coup.";
  document.getElementById("lien-melange").href = lienCahier + "&theme=melange";
  document.getElementById("lien-vraifaux").href = lienCahier + "&theme=vraifaux";
  if (matiere.parcours) {
    document.getElementById("progression").textContent =
      "Suis les étapes dans l'ordre : chacune commence par une petite leçon.";
    document.getElementById("lien-melange").hidden = true;
    document.getElementById("lien-vraifaux").hidden = true;
  }

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

    const etoiles = creerEtoiles(lireNombre(cleEtoilesDe(parametres.get("niveau"), parametres.get("matiere"), theme.id)));

    lien.append(titre, pointilles, etoiles, compte);
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
let defisReussis = 0;          // nombre de questions « Défi » réussies
let niveauDesDefis = "";       // niveau réel des défis (ex. "P5"), fixé par pageCahier
let cleEtoiles = null;         // où ranger les étoiles du thème (null pour la révision mélangée)
let debutDuTest = null;        // programmation : position de la 1re question du « petit test » (null sinon)

const ACCENTS = ["é", "è", "ê", "à", "â", "ç", "ù", "û", "ô", "î", "ï", "ë"];

function typeDe(question) {
  return question.type || "qcm";
}

// Prépare une question avant affichage. Pour un QCM : mélange les choix
// et recalcule la position de la bonne réponse. Les autres types sont gardés tels quels.
function preparerQuestion(question) {
  const type = typeDe(question);
  if (type === "association") {
    // On garde les paires telles quelles, mais on mélange l'ordre d'affichage des deux colonnes
    const indices = question.paires.map(function (paire, i) { return i; });
    return Object.assign({}, question, { ordreGauche: melanger(indices), ordreDroite: melanger(indices) });
  }
  if (type === "ordre") {
    // Ordre de départ mélangé, jamais déjà dans le bon ordre
    const indices = question.elements.map(function (element, i) { return i; });
    let depart = melanger(indices);
    while (depart.every(function (valeur, position) { return valeur === position; })) {
      depart = melanger(indices);
    }
    return Object.assign({}, question, { ordreDepart: depart });
  }
  if (type !== "qcm") {
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
// apostrophe typographique ’ remplacée par ', virgule et point décimaux confondus (7,20 = 7.20).
// Si les accents sont tolérés, ils sont aussi retirés (é → e).
function normaliser(texte, accentsToleres, majusculesStrictes) {
  let resultat = (majusculesStrictes ? texte : texte.toLowerCase())
    .replace(/[’`]/g, "'")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[.!?;]+$/, "")
    .trim()
    // Nombre à virgule : on accepte la virgule (écriture française) comme le point (calculatrice, anglais)
    .replace(/(\d),(\d)/g, "$1.$2");
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
  const robots = banqueDuQuiz.filter(function (q) { return typeDe(q) === "robot"; });
  if (robots.length > 0) {
    // Programmation : d'abord TOUS les robots, dans l'ordre du fichier (du plus facile au plus difficile),
    // puis un « petit test » avec les autres questions (QCM, vrai ou faux), mélangées
    const test = melanger(banqueDuQuiz.filter(function (q) { return typeDe(q) !== "robot"; }));
    questions = robots.concat(test).map(preparerQuestion);
    debutDuTest = test.length > 0 ? robots.length : null;
  } else {
    questions = melanger(banqueDuQuiz).slice(0, nombreParPartie).map(preparerQuestion);
    debutDuTest = null;
  }
  numeroQuestion = 0;
  score = 0;
  defisReussis = 0;
  afficherQuestion();
}

function afficherQuestion() {
  const question = questions[numeroQuestion];
  let progression = "Question " + (numeroQuestion + 1) + " sur " + questions.length;
  if (debutDuTest !== null) {
    progression = numeroQuestion < debutDuTest
      ? "Exercice " + (numeroQuestion + 1) + " sur " + debutDuTest
      : "Petit test : question " + (numeroQuestion - debutDuTest + 1) + " sur " + (questions.length - debutDuTest);
  }
  document.getElementById("progression").textContent = progression;
  // Annonce du petit test, seulement sur sa première question
  document.getElementById("annonce-test").hidden = numeroQuestion !== debutDuTest;
  const barre = document.getElementById("barre");
  barre.hidden = false;
  barre.firstElementChild.style.width = ((numeroQuestion + 1) / questions.length) * 100 + "%";
  afficherEnTete(question);

  const type = typeDe(question);
  if (type === "saisie") {
    afficherSaisie(question);
  } else if (type === "association") {
    afficherAssociation(question);
  } else if (type === "ordre") {
    afficherOrdre(question);
  } else if (type === "vraifaux") {
    afficherVraiFaux(question);
  } else if (type === "robot") {
    afficherRobot(question);
  } else {
    afficherQcm(question);
  }
}

// Partie commune à tous les exercices (quiz et série Vrai ou faux) :
// énoncé, texte support, astuce, badge défi, figure, et remise à zéro de la zone de réponse.
function afficherEnTete(question) {
  ecrireTexte(document.getElementById("enonce"), question.enonce);

  // Texte support facultatif (champ "texte"), pour les questions de lecture
  const texte = document.getElementById("texte-support");
  texte.textContent = typographie(question.texte || "");
  texte.hidden = !question.texte;

  // Astuce facultative (champ "astuce") : une méthode ou un outil, jamais la réponse
  const astuce = document.getElementById("astuce");
  ecrireTexte(astuce.querySelector("span"), question.astuce);
  astuce.hidden = !question.astuce;

  // Badge « Défi » (champ "defi": true) : une question un peu au-dessus du niveau
  document.getElementById("badge-defi").hidden = question.defi !== true;

  // Figure facultative : champ "image" (chemin du fichier) et "alt" (sa description)
  const figure = document.getElementById("figure");
  const image = document.getElementById("figure-image");
  if (question.image) {
    image.src = question.image;
    image.alt = question.alt || "";
    figure.hidden = false;
  } else {
    image.removeAttribute("src");
    figure.hidden = true;
  }

  document.getElementById("reponses").innerHTML = "";
  document.getElementById("correction").hidden = true;
  document.getElementById("bouton-suivant").hidden = true;
}

// --- Type "qcm" ---
function afficherQcm(question) {
  const reponses = document.getElementById("reponses");
  reponses.className = "reponses";
  question.choix.forEach(function (texteChoix, position) {
    const bouton = document.createElement("button");
    bouton.className = "reponse";
    ecrireTexte(bouton, texteChoix);
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
  if (question.phrase === true) {
    // Réponse attendue : une phrase complète (en anglais). Le clavier du téléphone met la majuscule.
    champ.placeholder = "Write a full sentence.";
    champ.setAttribute("autocapitalize", "sentences");
    reponses.classList.add("saisie-phrase");
  }

  // Boutons d'accents, seulement si la réponse attendue contient des lettres
  // (pas pour une phrase en anglais : les accents français n'y servent pas)
  const contientDesLettres = question.reponses.some(function (r) { return /\p{L}/u.test(r); });
  if (contientDesLettres && question.phrase !== true) {
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
  const majusculesStrictes = question.majuscules === "strictes";
  const tape = normaliser(texteTape, accentsToleres, majusculesStrictes);
  const estJuste = question.reponses.some(function (reponse) {
    return normaliser(reponse, accentsToleres, majusculesStrictes) === tape;
  });

  // On bloque la saisie et on colore le champ
  const reponses = document.getElementById("reponses");
  reponses.querySelectorAll("input, button").forEach(function (element) {
    element.disabled = true;
  });
  reponses.querySelector(".saisie-champ").classList.add(estJuste ? "juste" : "faux");

  // Faux seulement à cause des majuscules ou des accents ? On le dit, c'est plus utile qu'un simple « faux »
  let presque = "";
  if (!estJuste) {
    const tapeSouple = normaliser(texteTape, true, false);
    const justeSansDetails = question.reponses.some(function (reponse) {
      return normaliser(reponse, true, false) === tapeSouple;
    });
    if (justeSansDetails) {
      presque = "Presque ! Attention aux " + (majusculesStrictes ? "majuscules et aux accents" : "accents") + ". ";
    }
  }

  // Si c'est faux, on montre la réponse attendue avant l'explication
  const rappel = estJuste ? "" : presque + "La bonne réponse : « " + question.reponses[0] + " ». ";
  afficherCorrection(question, estJuste, rappel);
}

// --- Type "association" : relier chaque élément de gauche à un élément de droite ---
// Chaque élément de gauche a sa couleur ; quand on le relie, l'élément de droite prend la même couleur.
const COULEURS_PAIRES = ["#2f6fdb", "#e2574c", "#2e9e6a", "#d9a514", "#7a4cc2"];

function boutonValider(texte) {
  const bouton = document.createElement("button");
  bouton.type = "button";
  bouton.className = "saisie-valider bouton-valider";
  bouton.textContent = texte;
  return bouton;
}

function afficherAssociation(question) {
  const reponses = document.getElementById("reponses");
  reponses.className = "association";
  const colonneGauche = document.createElement("div");
  const colonneDroite = document.createElement("div");
  colonneGauche.className = "assoc-colonne";
  colonneDroite.className = "assoc-colonne";

  let selection = null;   // paire choisie à gauche, en attente d'un élément de droite
  const liens = {};       // numéro de paire à gauche → numéro de paire à droite
  const boutonsGauche = {};
  const boutonsDroite = {};

  function creerBouton(texte) {
    const bouton = document.createElement("button");
    bouton.type = "button";
    bouton.className = "assoc-element";
    const pastille = document.createElement("span");
    pastille.className = "pastille";
    pastille.setAttribute("aria-hidden", "true");
    const libelle = document.createElement("span");
    ecrireTexte(libelle, texte);
    bouton.appendChild(pastille);
    bouton.appendChild(libelle);
    return bouton;
  }

  question.ordreGauche.forEach(function (i, rang) {
    const bouton = creerBouton(question.paires[i][0]);
    bouton.style.setProperty("--pastille", COULEURS_PAIRES[rang % COULEURS_PAIRES.length]);
    bouton.addEventListener("click", function () {
      if (liens[i] !== undefined) {
        delete liens[i];          // toucher un élément déjà relié le détache
      }
      selection = selection === i ? null : i;
      rafraichir();
    });
    boutonsGauche[i] = bouton;
    colonneGauche.appendChild(bouton);
  });

  question.ordreDroite.forEach(function (j) {
    const bouton = creerBouton(question.paires[j][1]);
    bouton.addEventListener("click", function () {
      // On détache l'élément de gauche qui était déjà relié à celui-ci
      Object.keys(liens).forEach(function (cle) {
        if (liens[cle] === j) { delete liens[cle]; }
      });
      if (selection !== null) {
        liens[selection] = j;
        selection = null;
      }
      rafraichir();
    });
    boutonsDroite[j] = bouton;
    colonneDroite.appendChild(bouton);
  });

  const valider = boutonValider("Valider");
  valider.addEventListener("click", function () { corrigerAssociation(question, liens, boutonsGauche, boutonsDroite); });

  function rafraichir() {
    question.ordreDroite.forEach(function (j) {
      boutonsDroite[j].classList.remove("relie");
      boutonsDroite[j].style.removeProperty("--pastille");
    });
    question.ordreGauche.forEach(function (i) {
      const bouton = boutonsGauche[i];
      bouton.classList.toggle("choisi", selection === i);
      bouton.setAttribute("aria-pressed", selection === i ? "true" : "false");
      bouton.classList.toggle("relie", liens[i] !== undefined);
      if (liens[i] !== undefined) {
        const droite = boutonsDroite[liens[i]];
        droite.classList.add("relie");
        droite.style.setProperty("--pastille", bouton.style.getPropertyValue("--pastille"));
      }
    });
    reponses.classList.toggle("en-attente", selection !== null);
    valider.disabled = Object.keys(liens).length < question.paires.length;
  }

  const aide = document.createElement("p");
  aide.className = "consigne-type";
  aide.textContent = "Touche un élément à gauche, puis celui qui va avec à droite.";
  reponses.appendChild(aide);
  const grille = document.createElement("div");
  grille.className = "assoc-grille";
  grille.appendChild(colonneGauche);
  grille.appendChild(colonneDroite);
  reponses.appendChild(grille);
  reponses.appendChild(valider);
  rafraichir();
}

function corrigerAssociation(question, liens, boutonsGauche, boutonsDroite) {
  const reponses = document.getElementById("reponses");
  reponses.querySelectorAll("button").forEach(function (bouton) { bouton.disabled = true; });
  reponses.querySelector(".bouton-valider").hidden = true;
  let nbJustes = 0;
  question.paires.forEach(function (paire, i) {
    const juste = liens[i] === i;
    if (juste) { nbJustes = nbJustes + 1; }
    boutonsGauche[i].classList.add(juste ? "juste" : "faux");
    boutonsDroite[liens[i]].classList.add(juste ? "juste" : "faux");
  });
  const estJuste = nbJustes === question.paires.length;
  let rappel = "";
  if (!estJuste) {
    rappel = nbJustes + " paire" + (nbJustes > 1 ? "s" : "") + " juste" + (nbJustes > 1 ? "s" : "") +
      " sur " + question.paires.length + ". Les bonnes paires : " +
      question.paires.map(function (paire) { return paire[0] + " → " + paire[1]; }).join(" ; ") + ". ";
  }
  afficherCorrection(question, estJuste, rappel);
}

// --- Type "ordre" : remettre des étiquettes dans le bon ordre avec les flèches ---
function afficherOrdre(question) {
  const reponses = document.getElementById("reponses");
  reponses.className = "ordre";
  let ordre = question.ordreDepart.slice();
  const liste = document.createElement("ol");
  liste.className = "ordre-liste";

  function deplacer(position, sens, classeBouton) {
    const cible = position + sens;
    // Hauteur des deux étiquettes AVANT l'échange, pour les faire glisser ensuite
    const hautAvant = liste.children[position].getBoundingClientRect().top;
    const hautCible = liste.children[cible].getBoundingClientRect().top;
    const element = ordre[position];
    ordre[position] = ordre[cible];
    ordre[cible] = element;
    dessiner();
    // Glissement : chaque étiquette repart de son ancienne place et rejoint la nouvelle
    if (!animationsReduites()) {
      glisser(liste.children[cible], hautAvant, true);      // celle qu'on a déplacée
      glisser(liste.children[position], hautCible, false);  // celle qui lui laisse la place
    }
    // On garde le focus sur la même flèche de l'étiquette déplacée (pratique au clavier)
    const bouton = liste.children[cible].querySelector(classeBouton);
    if (bouton && !bouton.disabled) { bouton.focus(); }
  }

  // Fait partir une étiquette de son ancienne hauteur jusqu'à sa nouvelle place.
  // L'étiquette déplacée passe au premier plan et se soulève un peu pendant le trajet.
  function glisser(ligne, ancienHaut, auPremierPlan) {
    const ecart = ancienHaut - ligne.getBoundingClientRect().top;
    if (auPremierPlan) { ligne.classList.add("en-mouvement"); }
    const animation = ligne.animate([
      { transform: "translateY(" + ecart + "px)" + (auPremierPlan ? " scale(1.04)" : "") },
      { transform: "translateY(0)" }
    ], { duration: 280, easing: "cubic-bezier(0.2, 0.8, 0.3, 1)" });
    animation.onfinish = function () { ligne.classList.remove("en-mouvement"); };
  }

  function dessiner() {
    liste.innerHTML = "";
    ordre.forEach(function (indice, position) {
      const ligne = document.createElement("li");
      ligne.className = "ordre-element";
      const texte = document.createElement("span");
      texte.className = "ordre-texte";
      ecrireTexte(texte, question.elements[indice]);
      const monter = document.createElement("button");
      monter.type = "button";
      monter.className = "ordre-fleche monter";
      monter.textContent = "▲";
      monter.setAttribute("aria-label", "Monter");
      monter.disabled = position === 0;
      monter.addEventListener("click", function () { deplacer(position, -1, ".monter"); });
      const descendre = document.createElement("button");
      descendre.type = "button";
      descendre.className = "ordre-fleche descendre";
      descendre.textContent = "▼";
      descendre.setAttribute("aria-label", "Descendre");
      descendre.disabled = position === ordre.length - 1;
      descendre.addEventListener("click", function () { deplacer(position, 1, ".descendre"); });
      ligne.appendChild(texte);
      ligne.appendChild(monter);
      ligne.appendChild(descendre);
      liste.appendChild(ligne);
    });
  }

  const aide = document.createElement("p");
  aide.className = "consigne-type";
  aide.textContent = "Utilise les flèches ▲ ▼ pour ranger les étiquettes.";
  const valider = boutonValider("Valider");
  valider.addEventListener("click", function () {
    liste.querySelectorAll("button").forEach(function (bouton) { bouton.disabled = true; });
    valider.hidden = true;
    let estJuste = true;
    ordre.forEach(function (indice, position) {
      const bienPlace = indice === position;
      if (!bienPlace) { estJuste = false; }
      liste.children[position].classList.add(bienPlace ? "juste" : "faux");
    });
    const rappel = estJuste ? "" : "Le bon ordre : " + question.elements.join(" → ") + ". ";
    afficherCorrection(question, estJuste, rappel);
  });
  dessiner();
  reponses.appendChild(aide);
  reponses.appendChild(liste);
  reponses.appendChild(valider);
}

// --- Commun à tous les types ---
// --- Type "vraifaux" ---
// L'énoncé est une affirmation ; l'élève répond Vrai ou Faux (champ "vrai" : true ou false).
// Ces deux boutons servent aussi dans la série « Vrai ou faux ».
function creerBoutonsVraiFaux(quandOnClique) {
  const boutons = document.createElement("div");
  boutons.className = "vraifaux-boutons";
  [["Vrai", true], ["Faux", false]].forEach(function (choix) {
    const bouton = document.createElement("button");
    bouton.className = "reponse vraifaux-" + (choix[1] ? "vrai" : "faux");
    bouton.textContent = choix[0];
    bouton.addEventListener("click", function () {
      quandOnClique(choix[1], bouton);
    });
    boutons.appendChild(bouton);
  });
  return boutons;
}

// Colore les deux boutons après la réponse : celui choisi (juste ou faux) et, en cas d'erreur, le bon
function colorerBoutonsVraiFaux(estJuste, boutonChoisi) {
  document.querySelectorAll("#reponses .vraifaux-boutons .reponse").forEach(function (bouton) {
    bouton.disabled = true;
    if (bouton === boutonChoisi) {
      bouton.classList.add(estJuste ? "juste" : "faux");
    } else if (!estJuste) {
      bouton.classList.add("juste");
    }
  });
}

function afficherVraiFaux(question) {
  const reponses = document.getElementById("reponses");
  reponses.className = "vraifaux";
  reponses.appendChild(creerBoutonsVraiFaux(function (reponse, bouton) {
    const estJuste = reponse === question.vrai;
    colorerBoutonsVraiFaux(estJuste, bouton);
    afficherCorrection(question, estJuste, "");
  }));
}

function afficherCorrection(question, estJuste, rappel) {
  const correction = document.getElementById("correction");
  const verdict = document.getElementById("verdict");
  const boutonSuivant = document.getElementById("bouton-suivant");

  if (estJuste) {
    score = score + 1;
    if (question.defi === true) {
      defisReussis = defisReussis + 1;
    }
    verdict.textContent = "Bravo, c'est juste !";
    correction.className = "correction juste";
  } else {
    verdict.textContent = "Pas tout à fait…";
    correction.className = "correction faux";
  }
  ecrireTexte(document.getElementById("explication"), rappel + question.explication);
  correction.hidden = false;
  if (estJuste) {
    gerbeEtoiles(verdict);   // après l'affichage : la gerbe part de l'endroit où est écrit « Bravo »
  }

  const derniereQuestion = numeroQuestion === questions.length - 1;
  boutonSuivant.textContent = derniereQuestion ? "Voir mon score" : "Question suivante";
  if (debutDuTest !== null && numeroQuestion < debutDuTest) {
    boutonSuivant.textContent = numeroQuestion === debutDuTest - 1 ? "Passer au petit test" : "Exercice suivant";
  }
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

  // Étoiles du thème : on garde la meilleure partie (pas pour la révision mélangée)
  const zoneEtoiles = document.getElementById("bilan-etoiles");
  zoneEtoiles.innerHTML = "";
  zoneEtoiles.hidden = cleEtoiles === null;
  if (cleEtoiles !== null) {
    const gagnees = etoilesPour(score, questions.length);
    const meilleur = lireNombre(cleEtoiles);
    if (gagnees > meilleur) {
      ecrireNombre(cleEtoiles, gagnees);
    }
    zoneEtoiles.appendChild(creerEtoiles(gagnees));
    const texte = document.createElement("span");
    texte.className = "bilan-etoiles-texte";
    if (gagnees > meilleur && meilleur > 0) {
      texte.textContent = "Nouveau meilleur score sur ce thème !";
    } else if (gagnees === 0) {
      texte.textContent = "La moitié de bonnes réponses = 1 étoile";
    } else if (gagnees < 3) {
      texte.textContent = gagnees === 1 ? "80 % de bonnes réponses = 2 étoiles" : "Un sans-faute = 3 étoiles";
    } else {
      texte.textContent = "Sans-faute !";
    }
    zoneEtoiles.appendChild(texte);
  }
  if (score / questions.length >= 0.8) {
    confettis();
  }

  // Défis réussis : on ne les signale que s'il y en a (un défi raté n'est pas mentionné)
  const messageDefi = document.getElementById("message-defi");
  if (defisReussis > 0) {
    const mot = defisReussis === 1 ? "défi" : "défis";
    messageDefi.textContent = "⭐ Bravo, tu as réussi " + defisReussis + " " + mot +
      (niveauDesDefis ? " de niveau " + niveauDesDefis : "") + " !";
    messageDefi.hidden = false;
  } else {
    messageDefi.hidden = true;
  }
}

// ---------- 5 bis. La série « Vrai ou faux » ----------
// Le site tire une question au hasard :
// - une affirmation (type "vraifaux") : l'élève dit si elle est vraie ou fausse ;
// - un QCM : le site propose une réponse (la bonne une fois sur deux, sinon une mauvaise),
//   et l'élève dit si cette réponse est vraie ou fausse.
// La série s'arrête à la première erreur, ou quand l'élève le décide.
let serie = 0;              // nombre de bonnes réponses d'affilée
let pioche = [];            // questions pas encore tirées (on remélange quand elle est vide)
let banqueSerie = [];
let cleRecord = "";         // nom sous lequel le record est rangé dans le navigateur

// Le record est gardé dans le navigateur (localStorage). Celui-ci peut être indisponible
// (navigation privée, réglages) : dans ce cas, le jeu fonctionne simplement sans record.
function lireRecord() {
  return lireNombre(cleRecord);
}

function ecrireRecord(valeur) {
  ecrireNombre(cleRecord, valeur);
}

function lancerSerie(banque, cle) {
  banqueSerie = banque;
  cleRecord = cle;
  document.getElementById("zone-question").hidden = false;
  document.getElementById("bouton-suivant").addEventListener("click", function () {
    // Le même bouton sert à « Continuer » (après une bonne réponse) et à « Voir mon résultat »
    if (this.dataset.fin === "oui") {
      finirSerie();
    } else {
      questionSerie();
    }
  });
  document.getElementById("bouton-recommencer").addEventListener("click", function () {
    document.getElementById("bilan").hidden = true;
    document.getElementById("zone-question").hidden = false;
    demarrerSerie();
  });
  demarrerSerie();
}

function demarrerSerie() {
  serie = 0;
  pioche = melanger(banqueSerie);
  questionSerie();
}

function questionSerie() {
  if (pioche.length === 0) {
    pioche = melanger(banqueSerie);     // toutes les questions ont été vues : on recommence un tour
  }
  const question = pioche.pop();
  document.getElementById("barre").hidden = true;    // une série n'a pas de fin prévue : pas de barre
  const estAffirmation = typeDe(question) === "vraifaux";
  let estVraie;
  let bonne = "";        // pour un QCM : la bonne réponse, rappelée en cas d'erreur
  let proposition = "";
  if (estAffirmation) {
    estVraie = question.vrai;
  } else {
    bonne = question.choix[question.bonneReponse];
    const mauvaises = question.choix.filter(function (c, i) { return i !== question.bonneReponse; });
    estVraie = Math.random() < 0.5;
    proposition = estVraie ? bonne : mauvaises[Math.floor(Math.random() * mauvaises.length)];
  }

  const record = lireRecord();
  document.getElementById("progression").textContent =
    "Série : " + serie + " bonne" + (serie > 1 ? "s" : "") + " réponse" + (serie > 1 ? "s" : "") +
    " d'affilée" + (record > 0 ? " · Record : " + record : "");
  afficherEnTete(question);

  const reponses = document.getElementById("reponses");
  reponses.className = "vraifaux";
  if (!estAffirmation) {
    // Pour un QCM, on montre la réponse proposée sous l'énoncé
    const carte = document.createElement("p");
    carte.className = "proposition";
    const intitule = document.createElement("span");
    intitule.className = "proposition-intitule";
    intitule.textContent = "Réponse proposée :";
    const valeur = document.createElement("strong");
    ecrireTexte(valeur, proposition);
    carte.appendChild(intitule);
    carte.appendChild(valeur);
    reponses.appendChild(carte);
  }

  reponses.appendChild(creerBoutonsVraiFaux(function (reponse, bouton) {
    corrigerSerie(question, bonne, reponse === estVraie, bouton);
  }));

  const arreter = document.createElement("button");
  arreter.type = "button";
  arreter.className = "lien-arreter";
  arreter.textContent = "J'arrête là";
  arreter.addEventListener("click", finirSerie);
  reponses.appendChild(arreter);
}

function corrigerSerie(question, bonne, estJuste, boutonChoisi) {
  const reponses = document.getElementById("reponses");
  colorerBoutonsVraiFaux(estJuste, boutonChoisi);   // le bouton à choisir apparaît en vert en cas d'erreur
  reponses.querySelector(".lien-arreter").hidden = true;

  const correction = document.getElementById("correction");
  const verdict = document.getElementById("verdict");
  const boutonSuivant = document.getElementById("bouton-suivant");
  if (estJuste) {
    serie = serie + 1;
    verdict.textContent = "Bravo ! Série : " + serie;
    correction.className = "correction juste";
    ecrireTexte(document.getElementById("explication"), question.explication);
    boutonSuivant.textContent = "Continuer";
    boutonSuivant.dataset.fin = "non";
  } else {
    verdict.textContent = "Raté ! La série s'arrête.";
    correction.className = "correction faux";
    // Pour un QCM, on rappelle la bonne réponse ; une affirmation a déjà son « Vrai. » ou « Faux. » dans l'explication
    const rappel = bonne ? "La bonne réponse : « " + bonne + " ». " : "";
    ecrireTexte(document.getElementById("explication"), rappel + question.explication);
    boutonSuivant.textContent = "Voir mon résultat";
    boutonSuivant.dataset.fin = "oui";
  }
  correction.hidden = false;
  if (estJuste) {
    gerbeEtoiles(verdict);
  }
  boutonSuivant.hidden = false;
  boutonSuivant.focus();
}

function finirSerie() {
  const ancienRecord = lireRecord();
  const nouveauRecord = serie > ancienRecord;
  if (nouveauRecord) {
    ecrireRecord(serie);
  }
  document.getElementById("zone-question").hidden = true;
  document.getElementById("progression").textContent = "Terminé !";
  document.getElementById("bilan").hidden = false;
  document.getElementById("score").textContent = serie;
  document.getElementById("bilan-etoiles").hidden = true;   // pas d'étoiles pour la série : c'est le record qui compte
  let message = serie === 0
    ? "Pas de chance ! Retente ta chance."
    : "Tu as enchaîné " + serie + " bonne" + (serie > 1 ? "s" : "") + " réponse" + (serie > 1 ? "s" : "") + " !";
  document.getElementById("message-bilan").textContent = message;
  const messageRecord = document.getElementById("message-defi");
  if (nouveauRecord) {
    confettis();
    messageRecord.textContent = "🏆 Nouveau record !";
    messageRecord.hidden = false;
  } else if (ancienRecord > 0) {
    messageRecord.textContent = "Ton record : " + ancienRecord;
    messageRecord.hidden = false;
  } else {
    messageRecord.hidden = true;
  }
  document.getElementById("bouton-recommencer").textContent = "Rejouer";
}

// ---------- 5 ter. Programmation : le robot sur une grille, et les leçons ----------
// Type "robot" : l'élève assemble des blocs pour guider le robot jusqu'à l'étoile.
// Coordonnées : x = colonne (0 à gauche), y = ligne (0 en haut).
//   { "type": "robot", "enonce": "...", "grille": {"largeur": 5, "hauteur": 5},
//     "depart": {"x": 0, "y": 4, "direction": "est"}, "cible": {"x": 3, "y": 2},
//     "murs": [[2, 3]], "blocs": ["avancer", "gauche", "droite", "repeter", "si_mur"], "maxBlocs": 7,
//     "solution": [...], "explication": "..." }
//   + "programmeDepart": [...] (chasse aux bugs) : un programme faux, déjà écrit, que l'élève corrige
//   + "pieces": [[1, 3], [2, 3]] (variables) : des pièces à ramasser ; la variable « pièces » les compte,
//     et la sortie ne s'ouvre que si elle vaut au moins "piecesNecessaires" (par défaut : toutes les pièces)
// Les instructions d'un programme (même format pour "solution" et pour le programme de l'élève) :
//   "avancer", "gauche", "droite"                         → instructions simples
//   { "repeter": 3, "faire": [ ... ] }                    → boucle (instructions simples et « si »)
//   { "si": "mur_devant", "faire": [ ... ] }               → condition (instructions simples)
// Le validateur Python simule "solution" pour vérifier qu'elle mène bien à l'étoile.

const DIRECTIONS = ["nord", "est", "sud", "ouest"];       // dans le sens des aiguilles d'une montre
const PAS = { nord: [0, -1], est: [1, 0], sud: [0, 1], ouest: [-1, 0] };
const ESSAIS_ROBOT = 3;                                   // nombre de lancements avant la correction
const BLOCS = {
  avancer: { icone: "⬆️", texte: "Avancer" },
  gauche:  { icone: "↩️", texte: "Tourner à gauche" },
  droite:  { icone: "↪️", texte: "Tourner à droite" },
  repeter: { icone: "🔁", texte: "Répéter" },
  si_mur:  { icone: "❓", texte: "Si mur devant" }
};

// Les deux sortes de blocs « conteneurs » (qui contiennent d'autres blocs)
function estBoucle(bloc) { return typeof bloc === "object" && "repeter" in bloc; }
function estCondition(bloc) { return typeof bloc === "object" && "si" in bloc; }
function nomDuBloc(bloc) {
  if (typeof bloc === "string") { return bloc; }
  return estBoucle(bloc) ? "repeter" : "si_mur";
}

// Nombre de blocs d'un programme : un conteneur compte 1, plus ce qu'il contient
function compterBlocs(programme) {
  return programme.reduce(function (total, bloc) {
    return total + (typeof bloc === "string" ? 1 : 1 + compterBlocs(bloc.faire));
  }, 0);
}

// Texte lisible d'un programme, pour la correction :
// « Répéter 8 fois (Si mur devant (Tourner à droite), Avancer) »
function programmeEnTexte(programme) {
  return programme.map(function (bloc) {
    if (typeof bloc === "string") { return BLOCS[bloc].texte; }
    const debut = estBoucle(bloc) ? "Répéter " + bloc.repeter + " fois" : "Si mur devant";
    return debut + " (" + programmeEnTexte(bloc.faire) + ")";
  }).join(", ");
}

// Y a-t-il un conteneur vide dans le programme ? (on prévient l'élève avant de lancer)
function contientUnBlocVide(programme) {
  return programme.some(function (bloc) {
    return typeof bloc !== "string" && (bloc.faire.length === 0 || contientUnBlocVide(bloc.faire));
  });
}

// Exécute un programme « sur le papier » et renvoie la liste des étapes successives.
// Chaque étape garde le bloc affiché qui l'a produite (pour l'allumer pendant l'animation).
// La simulation s'arrête au premier choc contre un mur ou le bord de la grille.
function simulerRobot(config, programme, blocsAffiches) {
  const murs = new Set((config.murs || []).map(function (m) { return m[0] + "," + m[1]; }));
  let x = config.depart.x;
  let y = config.depart.y;
  let direction = config.depart.direction;
  const etapes = [];
  let choc = false;
  // La variable « pièces » : combien de pièces le robot a ramassées
  const pieces = new Set((config.pieces || []).map(function (p) { return p[0] + "," + p[1]; }));
  let ramassees = 0;

  // La case devant le robot est-elle un mur ou en dehors de la grille ?
  function murDevant() {
    const nx = x + PAS[direction][0];
    const ny = y + PAS[direction][1];
    const dehors = nx < 0 || ny < 0 || nx >= config.grille.largeur || ny >= config.grille.hauteur;
    return dehors || murs.has(nx + "," + ny);
  }

  function executer(liste, elements) {
    for (let i = 0; i < liste.length && !choc; i++) {
      const bloc = liste[i];
      const element = elements ? elements[i] : null;
      const enfants = element ? element.enfants : null;
      if (estBoucle(bloc)) {
        for (let tour = 0; tour < bloc.repeter && !choc; tour++) {
          etapes.push({ x: x, y: y, direction: direction, element: element, tour: tour + 1, tours: bloc.repeter });
          executer(bloc.faire, enfants);
        }
        continue;
      }
      if (estCondition(bloc)) {
        const oui = murDevant();
        etapes.push({ x: x, y: y, direction: direction, element: element, reponse: oui });
        if (oui) { executer(bloc.faire, enfants); }
        continue;
      }
      if (bloc === "avancer") {
        if (murDevant()) {
          choc = true;
          etapes.push({ x: x, y: y, direction: direction, element: element, choc: true });
          return;
        }
        x = x + PAS[direction][0];
        y = y + PAS[direction][1];
      } else {
        const sens = bloc === "droite" ? 1 : 3;
        direction = DIRECTIONS[(DIRECTIONS.indexOf(direction) + sens) % 4];
      }
      const etape = { x: x, y: y, direction: direction, element: element };
      // Une pièce sur la case : le robot la ramasse (une seule fois) et la variable augmente de 1
      if (bloc === "avancer" && pieces.has(x + "," + y)) {
        pieces.delete(x + "," + y);
        ramassees++;
        etape.ramasse = true;
        etape.pieces = ramassees;
      }
      etapes.push(etape);
    }
  }
  executer(programme, blocsAffiches);
  const surLaSortie = !choc && x === config.cible.x && y === config.cible.y;
  const necessaires = piecesNecessaires(config);
  return {
    etapes: etapes,
    choc: choc,
    surLaSortie: surLaSortie,
    pieces: ramassees,
    necessaires: necessaires,
    arrive: surLaSortie && ramassees >= necessaires
  };
}

// Nombre de pièces qu'il faut pour ouvrir la sortie (0 s'il n'y a pas de pièces)
function piecesNecessaires(config) {
  const total = (config.pieces || []).length;
  return config.piecesNecessaires !== undefined ? config.piecesNecessaires : total;
}

// Dessine la grille, l'étoile, les murs, les pièces et le robot. Renvoie de quoi déplacer le robot.
// "element" est un cadre qui contient la grille et, s'il y a des pièces, la boîte de la variable.
function creerTerrain(config) {
  const cadre = document.createElement("div");
  cadre.className = "terrain-cadre";
  cadre.style.setProperty("--colonnes", config.grille.largeur);
  const terrain = document.createElement("div");
  terrain.className = "terrain";
  terrain.style.setProperty("--colonnes", config.grille.largeur);
  terrain.style.setProperty("--lignes", config.grille.hauteur);
  terrain.setAttribute("role", "img");

  const murs = new Set((config.murs || []).map(function (m) { return m[0] + "," + m[1]; }));
  const piecesSet = new Set((config.pieces || []).map(function (p) { return p[0] + "," + p[1]; }));
  const avecPieces = piecesSet.size > 0;
  const necessaires = piecesNecessaires(config);
  for (let y = 0; y < config.grille.hauteur; y++) {
    for (let x = 0; x < config.grille.largeur; x++) {
      const case_ = document.createElement("span");
      case_.className = "case" + ((x + y) % 2 ? " sombre" : "");
      if (murs.has(x + "," + y)) { case_.classList.add("mur"); }
      if (x === config.cible.x && y === config.cible.y) {
        case_.classList.add("cible");
        const etoile = document.createElement("span");
        etoile.textContent = "⭐";
        case_.appendChild(etoile);
      }
      if (piecesSet.has(x + "," + y)) {
        const piece = document.createElement("span");
        piece.className = "piece";
        piece.textContent = "🪙";
        case_.appendChild(piece);
      }
      terrain.appendChild(case_);
    }
  }

  // Le robot : une petite tête dessinée en SVG, dont les yeux montrent où il regarde
  const pion = document.createElement("span");
  pion.className = "robot-pion";
  pion.innerHTML =
    '<svg viewBox="0 0 40 40" aria-hidden="true">' +
    '<line x1="20" y1="2" x2="20" y2="8" stroke="#2b2b52" stroke-width="2.5"/>' +
    '<circle cx="20" cy="3" r="2.6" fill="#ff7eb0"/>' +
    '<rect x="6" y="8" width="28" height="26" rx="8" fill="#5b8def" stroke="#2b2b52" stroke-width="2.5"/>' +
    '<circle cx="14" cy="15" r="3.6" fill="white"/><circle cx="26" cy="15" r="3.6" fill="white"/>' +
    '<circle cx="14" cy="14" r="1.8" fill="#2b2b52"/><circle cx="26" cy="14" r="1.8" fill="#2b2b52"/>' +
    '<rect x="13" y="24" width="14" height="4" rx="2" fill="#2b2b52"/>' +
    '</svg>';
  terrain.appendChild(pion);
  cadre.appendChild(terrain);

  // La variable « pièces », comme une boîte avec une étiquette, sous la grille
  const boite = document.createElement("div");
  boite.className = "variable";
  const valeur = document.createElement("span");
  const etoileCible = terrain.children[config.cible.y * config.grille.largeur + config.cible.x].firstChild;
  if (avecPieces) {
    const etiquette = document.createElement("span");
    etiquette.className = "variable-etiquette";
    etiquette.textContent = "pièces";
    valeur.className = "variable-valeur";
    const but = document.createElement("span");
    but.className = "variable-but";
    but.textContent = "La sortie s'ouvre à " + necessaires + (necessaires > 1 ? " pièces." : " pièce.");
    boite.append(etiquette, valeur, but);
    cadre.appendChild(boite);
  }

  // Change la valeur de la variable ; la sortie s'ouvre quand il y a assez de pièces
  function changerPieces(nombre, avecAnimation) {
    if (!avecPieces) { return; }
    valeur.textContent = nombre;
    const ouverte = nombre >= necessaires;
    etoileCible.textContent = ouverte ? "⭐" : "🔒";
    etoileCible.parentNode.classList.toggle("fermee", !ouverte);
    if (avecAnimation) {
      valeur.classList.remove("nouveau-tour");
      valeur.getBoundingClientRect();
      valeur.classList.add("nouveau-tour");
    }
  }
  function ramasser(x, y, nombre) {
    const piece = terrain.children[y * config.grille.largeur + x].querySelector(".piece");
    if (piece) { piece.classList.add("ramassee"); }
    changerPieces(nombre, true);
  }

  let angle = 0;   // on cumule l'angle pour que le robot tourne toujours du bon côté
  let directionActuelle = config.depart.direction;
  function placer(x, y, direction, sansAnimation) {
    const ecart = (DIRECTIONS.indexOf(direction) - DIRECTIONS.indexOf(directionActuelle) + 4) % 4;
    angle += ecart === 3 ? -90 : ecart * 90;
    directionActuelle = direction;
    if (sansAnimation) { pion.classList.add("sans-transition"); }
    pion.style.left = (x / config.grille.largeur) * 100 + "%";
    pion.style.top = (y / config.grille.hauteur) * 100 + "%";
    pion.style.transform = "rotate(" + angle + "deg)";
    if (sansAnimation) {
      pion.getBoundingClientRect();           // force le navigateur à appliquer la position tout de suite
      pion.classList.remove("sans-transition");
    }
    terrain.setAttribute("aria-label", "Grille de " + config.grille.largeur + " cases sur " +
      config.grille.hauteur + ". Le robot regarde vers le " + direction + ".");
  }
  function revenirAuDepart() {
    angle = { nord: 0, est: 90, sud: 180, ouest: 270 }[config.depart.direction];
    directionActuelle = config.depart.direction;
    pion.classList.remove("cogne", "arrive");
    if (typeof eteindreRegard === "function") { eteindreRegard(); }
    // Les pièces reviennent à leur place et la variable repart de 0
    terrain.querySelectorAll(".piece.ramassee").forEach(function (p) { p.classList.remove("ramassee"); });
    changerPieces(0, false);
    placer(config.depart.x, config.depart.y, config.depart.direction, true);
  }
  // Pendant une question « mur devant ? », la case regardée s'allume un instant :
  // en jaune si elle est libre, en rouge si c'est un mur. Si c'est le bord, c'est le cadre qui clignote.
  function montrerDevant(x, y, direction, mur) {
    terrain.querySelectorAll(".regard, .regard-mur").forEach(function (c) { c.classList.remove("regard", "regard-mur"); });
    terrain.classList.remove("regard-bord");
    const nx = x + PAS[direction][0];
    const ny = y + PAS[direction][1];
    const dehors = nx < 0 || ny < 0 || nx >= config.grille.largeur || ny >= config.grille.hauteur;
    if (dehors) {
      terrain.getBoundingClientRect();
      terrain.classList.add("regard-bord");
    } else {
      terrain.children[ny * config.grille.largeur + nx].classList.add(mur ? "regard-mur" : "regard");
    }
  }
  function eteindreRegard() {
    terrain.querySelectorAll(".regard, .regard-mur").forEach(function (c) { c.classList.remove("regard", "regard-mur"); });
    terrain.classList.remove("regard-bord");
  }
  revenirAuDepart();
  return { element: cadre, pion: pion, placer: placer, revenirAuDepart: revenirAuDepart,
    montrerDevant: montrerDevant, eteindreRegard: eteindreRegard, ramasser: ramasser };
}

// Vitesse du robot, choisie par l'élève (et gardée dans le navigateur pour la prochaine fois).
// "pas" : durée d'un déplacement ou d'une rotation ; "question" : durée d'un début de tour
// ou d'une question « mur devant ? » (sans mouvement), en millisecondes.
const VITESSES = {
  lente:   { nom: "🐢 Lente",   pas: 1000, question: 1000 },
  normale: { nom: "🚶 Normale", pas: 450,  question: 250 },
  rapide:  { nom: "🐇 Rapide",  pas: 180,  question: 90 }
};
let vitesseRobot = lireVitesse();

function lireVitesse() {
  try {
    const vitesse = localStorage.getItem("vitesse-robot");
    if (VITESSES[vitesse]) { return vitesse; }
  } catch (erreur) {
    // navigateur qui refuse la mémoire locale : on garde la vitesse normale
  }
  return "normale";
}

function choisirVitesse(vitesse) {
  vitesseRobot = vitesse;
  try { localStorage.setItem("vitesse-robot", vitesse); } catch (erreur) { /* tant pis */ }
  // Tous les sélecteurs de la page (leçon et exercice) montrent le même choix
  document.querySelectorAll(".vitesse button").forEach(function (bouton) {
    bouton.setAttribute("aria-pressed", bouton.dataset.vitesse === vitesse ? "true" : "false");
  });
}

// Trois boutons « 🐢 Lente / 🚶 Normale / 🐇 Rapide ». On peut changer même pendant que le robot joue.
function creerSelecteurVitesse() {
  const groupe = document.createElement("div");
  groupe.className = "vitesse";
  groupe.setAttribute("role", "group");
  groupe.setAttribute("aria-label", "Vitesse du robot");
  const titre = document.createElement("span");
  titre.className = "vitesse-titre";
  titre.textContent = "Vitesse :";
  groupe.appendChild(titre);
  Object.keys(VITESSES).forEach(function (vitesse) {
    const bouton = document.createElement("button");
    bouton.type = "button";
    bouton.dataset.vitesse = vitesse;
    bouton.textContent = VITESSES[vitesse].nom;
    bouton.setAttribute("aria-pressed", vitesse === vitesseRobot ? "true" : "false");
    bouton.addEventListener("click", function () { choisirVitesse(vitesse); });
    groupe.appendChild(bouton);
  });
  return groupe;
}

// Joue les étapes d'une simulation une par une, en allumant le bloc en cours.
// La vitesse est relue à chaque étape : un changement de vitesse agit tout de suite.
// "quandFini" reçoit le résultat de la simulation.
function animerRobot(terrain, resultat, quandFini) {
  let i = 0;
  let allume = null;
  function suivante() {
    if (allume) { allume.classList.remove("en-cours"); }
    if (i >= resultat.etapes.length) {
      terrain.eteindreRegard();
      if (resultat.arrive) { terrain.pion.classList.add("arrive"); }
      quandFini(resultat);
      return;
    }
    const etape = resultat.etapes[i];
    allume = etape.element ? etape.element.ligne : null;
    if (allume) { allume.classList.add("en-cours"); }
    if (etape.tour && allume) { afficherPastille(allume, "tour " + etape.tour + " / " + etape.tours, ""); }
    terrain.eteindreRegard();
    if (etape.reponse !== undefined) {
      terrain.montrerDevant(etape.x, etape.y, etape.direction, etape.reponse);
      if (allume) { afficherPastille(allume, etape.reponse ? "oui, mur !" : "non", etape.reponse ? "oui" : "non"); }
    }
    if (etape.choc) {
      terrain.pion.classList.add("cogne");
      if (allume) { allume.classList.add("bug"); }
      allume = null;
    } else {
      // Le glissement du robot dure un peu moins qu'une étape (au plus 0,6 s)
      terrain.pion.style.transitionDuration = Math.min(600, VITESSES[vitesseRobot].pas * 0.75) + "ms";
      terrain.placer(etape.x, etape.y, etape.direction);
      if (etape.ramasse) { terrain.ramasser(etape.x, etape.y, etape.pieces); }
    }
    i++;
    const sansMouvement = etape.tour !== undefined || etape.reponse !== undefined;
    const vitesse = VITESSES[vitesseRobot];
    setTimeout(suivante, sansMouvement ? vitesse.question : vitesse.pas);
  }
  suivante();
}

// Pastille à côté du titre d'un conteneur pendant l'exécution :
// « tour 2 / 3 » pour une boucle, « oui, mur ! » ou « non » pour une condition
function afficherPastille(ligne, texte, sorte) {
  const titre = ligne.querySelector(".bloc-titre");
  let pastille = titre.querySelector(".pastille-execution");
  if (!pastille) {
    pastille = document.createElement("span");
    titre.appendChild(pastille);
  }
  pastille.className = "pastille-execution " + sorte;
  pastille.textContent = texte;
  // On relance la petite animation à chaque nouveau passage
  pastille.classList.remove("nouveau-tour");
  pastille.getBoundingClientRect();
  pastille.classList.add("nouveau-tour");
}

// Titre d'un conteneur, en texte simple (leçons) : « 🔁 Répéter 3 fois » ou « ❓ Si mur devant : »
function titreConteneur(bloc) {
  return estBoucle(bloc) ? "🔁 Répéter " + bloc.repeter + " fois" : "❓ Si mur devant :";
}

// Une étiquette de bloc, pour les démonstrations des leçons (sans bouton)
function etiquetteBloc(bloc) {
  const ligne = document.createElement("li");
  ligne.className = "bloc bloc-" + nomDuBloc(bloc);
  if (typeof bloc === "string") {
    ligne.textContent = BLOCS[bloc].icone + " " + BLOCS[bloc].texte;
    return { ligne: ligne, enfants: null };
  }
  const titre = document.createElement("span");
  titre.className = "bloc-titre";
  titre.textContent = titreConteneur(bloc);
  const dedans = document.createElement("ol");
  dedans.className = "programme-dedans";
  const enfants = bloc.faire.map(function (b) {
    const e = etiquetteBloc(b);
    dedans.appendChild(e.ligne);
    return e;
  });
  ligne.append(titre, dedans);
  return { ligne: ligne, enfants: enfants };
}

// Petite démonstration (dans les leçons) : une grille et un programme qu'on regarde s'exécuter
function creerDemo(demo) {
  const boite = document.createElement("div");
  boite.className = "demo-robot";
  const terrain = creerTerrain(demo);
  const liste = document.createElement("ol");
  liste.className = "programme programme-demo";
  const elements = demo.programme.map(function (bloc) {
    const e = etiquetteBloc(bloc);
    liste.appendChild(e.ligne);
    return e;
  });
  const bouton = document.createElement("button");
  bouton.type = "button";
  bouton.className = "bouton-lancer";
  bouton.textContent = "▶ Regarder";
  bouton.addEventListener("click", function () {
    bouton.disabled = true;
    terrain.revenirAuDepart();
    liste.querySelectorAll(".bug").forEach(function (b) { b.classList.remove("bug"); });
    liste.querySelectorAll(".pastille-execution").forEach(function (p) { p.remove(); });
    setTimeout(function () {
      animerRobot(terrain, simulerRobot(demo, demo.programme, elements), function () {
        bouton.disabled = false;
        bouton.textContent = "↺ Revoir";
      });
    }, 300);
  });
  const cote = document.createElement("div");
  cote.className = "demo-cote";
  const legende = document.createElement("p");
  legende.className = "consigne-type";
  legende.textContent = "Le programme :";
  cote.append(legende, liste, bouton, creerSelecteurVitesse());
  boite.append(terrain.element, cote);
  return boite;
}

// --- L'exercice "robot" ---
// Le programme de l'élève a le même format que "solution". Les nouveaux blocs vont dans
// le conteneur « ouvert » (entouré de jaune) : on garde la pile des conteneurs ouverts,
// par exemple [] (programme principal), [boucle], ou [boucle, condition].
function afficherRobot(question) {
  const reponses = document.getElementById("reponses");
  reponses.className = "robot";
  const terrain = creerTerrain(question);
  const autorises = question.blocs || ["avancer", "gauche", "droite"];
  const max = question.maxBlocs || null;
  // Chasse aux bugs : l'exercice peut fournir un programme de départ (faux) que l'élève corrige
  const depart = question.programmeDepart || null;
  function copieDuDepart() { return depart ? JSON.parse(JSON.stringify(depart)) : []; }
  let programme = copieDuDepart();
  let ouverts = [];            // pile des conteneurs ouverts, du plus extérieur au plus intérieur
  let essais = 0;
  let enCours = false;
  let elementsLances = [];     // les blocs affichés pendant le dernier lancement

  function conteneurOuvert() { return ouverts.length ? ouverts[ouverts.length - 1] : null; }
  function listeOuverte() { return ouverts.length ? conteneurOuvert().faire : programme; }

  const aide = document.createElement("p");
  aide.className = "consigne-type";
  aide.textContent = (depart
    ? "🐞 Ce programme a un bug ! Lance-le pour voir où ça coince, puis corrige-le."
    : "Touche les blocs pour construire ton programme, puis appuie sur ▶ Lancer.") +
    " Tu peux aussi attraper un bloc et le faire glisser où tu veux.";

  const palette = document.createElement("div");
  palette.className = "palette";
  const zone = document.createElement("div");
  zone.className = "zone-programme";
  const compteur = document.createElement("p");
  compteur.className = "compteur-blocs";
  const liste = document.createElement("ol");
  liste.className = "programme";
  const message = document.createElement("p");
  message.className = "message-robot";
  message.setAttribute("aria-live", "polite");

  const actions = document.createElement("div");
  actions.className = "actions-robot";
  const lancer = boutonValider("▶ Lancer");
  lancer.classList.add("bouton-lancer");
  const effacer = document.createElement("button");
  effacer.type = "button";
  effacer.className = "bouton-effacer";
  effacer.textContent = "🗑️ Tout effacer";
  actions.append(lancer, effacer);
  // Pour un programme à corriger : revenir au programme de départ, si l'élève s'est perdu
  const recommencer = document.createElement("button");
  recommencer.type = "button";
  recommencer.className = "bouton-effacer";
  recommencer.textContent = "↺ Programme de départ";
  recommencer.hidden = depart === null;
  recommencer.addEventListener("click", function () {
    programme = copieDuDepart();
    ouverts = [];
    effacerMessage();
    terrain.revenirAuDepart();
    dessiner();
  });
  actions.appendChild(recommencer);

  // Les boutons de la palette (un par bloc autorisé) + le bouton qui ferme le conteneur ouvert
  const boutonsPalette = [];
  autorises.forEach(function (nom) {
    const bouton = document.createElement("button");
    bouton.type = "button";
    bouton.className = "bloc bloc-" + nom;
    bouton.textContent = BLOCS[nom].icone + " " + BLOCS[nom].texte;
    bouton.addEventListener("click", function () {
      if (!clicBloque) { ajouter(nom); }
    });
    bouton.dataset.nom = nom;
    rendreDeplacable(bouton, null, null, null, nom);   // on peut aussi le faire glisser dans le programme
    boutonsPalette.push(bouton);
    palette.appendChild(bouton);
  });
  const fermer = document.createElement("button");
  fermer.type = "button";
  fermer.className = "bloc bloc-fin";
  fermer.addEventListener("click", function () { ouverts.pop(); dessiner(); });
  palette.appendChild(fermer);

  // Peut-on ajouter ce bloc à l'endroit ouvert ?
  //  - une boucle seulement dans le programme principal (pas de boucle dans une boucle) ;
  //  - une condition dans le programme principal ou dans une boucle (pas dans une condition).
  function permis(nom) {
    const ouvert = conteneurOuvert();
    if (nom === "repeter") { return ouvert === null; }
    if (nom === "si_mur") { return ouvert === null || estBoucle(ouvert); }
    return true;
  }

  function nouveauBloc(nom) {
    if (nom === "repeter") { return { repeter: 2, faire: [] }; }
    if (nom === "si_mur") { return { si: "mur_devant", faire: [] }; }
    return nom;
  }

  function ajouter(nom) {
    if (enCours || (max && compterBlocs(programme) >= max) || !permis(nom)) { return; }
    const bloc = nouveauBloc(nom);
    listeOuverte().push(bloc);
    if (typeof bloc !== "string") { ouverts.push(bloc); }   // un nouveau conteneur s'ouvre
    effacerMessage();
    dessiner();
  }

  function effacerMessage() {
    message.textContent = "";
    message.className = "message-robot";
  }

  // Redessine le programme de l'élève. Chaque bloc a une croix pour le retirer ;
  // une boucle a des boutons − et + pour choisir le nombre de tours.
  // Renvoie la liste des éléments affichés, dans la même forme que le programme (pour l'animation).
  function dessiner() {
    liste.innerHTML = "";
    // Chaque liste affichée garde le tableau qu'elle représente (pour savoir où lâcher un bloc)
    liste.listeBlocs = programme;
    liste.conteneur = null;
    const elements = programme.map(function (bloc, i) {
      return dessinerBloc(bloc, liste, [], programme, i);
    });
    const nombre = compterBlocs(programme);
    compteur.textContent = max ? "Blocs : " + nombre + " / " + max : "Blocs : " + nombre;
    compteur.classList.toggle("plein", max !== null && nombre >= max);
    boutonsPalette.forEach(function (b) {
      b.disabled = enCours || (max !== null && nombre >= max) || !permis(b.dataset.nom);
    });
    const ouvert = conteneurOuvert();
    fermer.hidden = ouvert === null;
    fermer.textContent = ouvert && estCondition(ouvert) ? "✔ Fin du si" : "✔ Fin de la boucle";
    fermer.disabled = enCours;
    lancer.disabled = enCours || programme.length === 0;
    effacer.disabled = enCours || programme.length === 0;
    recommencer.disabled = enCours;
    if (programme.length === 0) {
      const vide = document.createElement("li");
      vide.className = "programme-vide";
      vide.textContent = "Ton programme est vide.";
      liste.appendChild(vide);
    }
    return elements;
  }

  // "parents" : les conteneurs qui entourent ce bloc (pour le rouvrir au bon endroit) ;
  // "listeParent" et "index" : où se trouve ce bloc dans le programme (pour le retirer ou le déplacer)
  function dessinerBloc(bloc, parent, parents, listeParent, index) {
    const ligne = document.createElement("li");
    ligne.className = "bloc bloc-" + nomDuBloc(bloc);
    rendreDeplacable(ligne, bloc, listeParent, index, null);
    function retirer() { listeParent.splice(index, 1); }
    const croix = document.createElement("button");
    croix.type = "button";
    croix.className = "bloc-retirer";
    croix.textContent = "✕";
    croix.setAttribute("aria-label", "Retirer ce bloc");
    croix.disabled = enCours;
    croix.addEventListener("click", function () {
      // Si on retire un conteneur ouvert (ou qui contient le conteneur ouvert), on le referme
      const position = ouverts.indexOf(bloc);
      if (position >= 0) { ouverts = ouverts.slice(0, position); }
      retirer();
      effacerMessage();
      dessiner();
    });

    if (typeof bloc === "string") {
      const texte = document.createElement("span");
      texte.textContent = BLOCS[bloc].icone + " " + BLOCS[bloc].texte;
      ligne.append(texte, croix);
      parent.appendChild(ligne);
      return { ligne: ligne, enfants: null };
    }

    // Un conteneur : son titre, puis les blocs qu'il contient
    if (bloc === conteneurOuvert()) { ligne.classList.add("ouverte"); }
    const titre = document.createElement("span");
    titre.className = "bloc-titre";
    if (estBoucle(bloc)) {
      // « Répéter [−] 2 [+] fois »
      const moins = document.createElement("button");
      moins.type = "button";
      moins.className = "tours";
      moins.textContent = "−";
      moins.setAttribute("aria-label", "Un tour de moins");
      moins.disabled = enCours || bloc.repeter <= 2;
      moins.addEventListener("click", function () { bloc.repeter--; dessiner(); });
      const nombre = document.createElement("strong");
      nombre.textContent = bloc.repeter;
      const plus = document.createElement("button");
      plus.type = "button";
      plus.className = "tours";
      plus.textContent = "+";
      plus.setAttribute("aria-label", "Un tour de plus");
      plus.disabled = enCours || bloc.repeter >= 10;
      plus.addEventListener("click", function () { bloc.repeter++; dessiner(); });
      titre.append("🔁 Répéter ", moins, nombre, plus, " fois");
    } else {
      titre.append("❓ Si mur devant :");
    }
    titre.addEventListener("click", function (evenement) {
      // Toucher le titre d'un conteneur le rouvre : les prochains blocs iront dedans
      if (evenement.target === titre && !enCours) {
        ouverts = parents.concat([bloc]);
        dessiner();
      }
    });
    const dedans = document.createElement("ol");
    dedans.className = "programme-dedans";
    dedans.listeBlocs = bloc.faire;
    dedans.conteneur = bloc;
    const enfants = bloc.faire.map(function (b, j) {
      return dessinerBloc(b, dedans, parents.concat([bloc]), bloc.faire, j);
    });
    if (bloc.faire.length === 0) {
      const vide = document.createElement("li");
      vide.className = "programme-vide";
      vide.textContent = estBoucle(bloc) ? "Ajoute des blocs dans la boucle." : "Ajoute ce que le robot fait s'il y a un mur.";
      dedans.appendChild(vide);
    }
    ligne.append(titre, croix, dedans);
    parent.appendChild(ligne);
    return { ligne: ligne, enfants: enfants };
  }

  // --- Attraper-glisser ---
  // On peut faire glisser un bloc de la palette jusqu'à l'endroit voulu du programme, ou déplacer
  // un bloc du programme (y compris pour le mettre dans une boucle ou l'en sortir).
  // Écrit avec les « pointer events » : ça marche à la souris comme au doigt (tablette, téléphone).
  let glisse = null;        // le glissement en cours (null s'il n'y en a pas)
  let clicBloque = false;   // après un glissement, on ignore le « clic » que le navigateur envoie au lâcher

  // Mêmes règles que pour la palette : une boucle seulement dans le programme principal,
  // une condition dans le programme principal ou dans une boucle
  function peutAllerDans(nom, conteneur) {
    if (nom === "repeter") { return conteneur === null; }
    if (nom === "si_mur") { return conteneur === null || estBoucle(conteneur); }
    return true;
  }

  // "bloc", "listeOrigine", "indexOrigine" : pour un bloc du programme ; "nomNouveau" : pour un bloc de la palette
  function rendreDeplacable(element, bloc, listeOrigine, indexOrigine, nomNouveau) {
    element.addEventListener("pointerdown", function (evenement) {
      if (enCours || glisse || evenement.button > 0) { return; }
      // Les petits boutons d'un bloc (✕, −, +) gardent leur rôle : on ne glisse pas depuis eux
      if (evenement.target !== element && evenement.target.closest("button")) { return; }
      evenement.stopPropagation();   // un bloc dans une boucle : c'est lui qu'on attrape, pas la boucle
      glisse = {
        element: element, bloc: bloc, listeOrigine: listeOrigine, indexOrigine: indexOrigine,
        nom: nomNouveau || nomDuBloc(bloc), nouveau: nomNouveau !== null,
        x0: evenement.clientX, y0: evenement.clientY, actif: false, cible: null
      };
      window.addEventListener("pointermove", pendantGlisser);
      window.addEventListener("pointerup", finGlisser);
      window.addEventListener("pointercancel", annulerGlisser);
    });
  }

  function pendantGlisser(evenement) {
    if (!glisse) { return; }
    if (!glisse.actif) {
      // On ne commence à glisser qu'après quelques pixels : un simple toucher reste un clic
      if (Math.hypot(evenement.clientX - glisse.x0, evenement.clientY - glisse.y0) < 6) { return; }
      if (glisse.nouveau && max !== null && compterBlocs(programme) >= max) { nettoyerGlisser(); return; }
      commencerGlisser();
    }
    evenement.preventDefault();
    glisse.fantome.style.left = evenement.clientX - glisse.decalX + "px";
    glisse.fantome.style.top = evenement.clientY - glisse.decalY + "px";
    chercherCible(evenement.clientX, evenement.clientY);
    // Près du haut ou du bas de l'écran, la page défile toute seule
    if (evenement.clientY < 50) { window.scrollBy(0, -12); }
    if (evenement.clientY > window.innerHeight - 50) { window.scrollBy(0, 12); }
  }

  function commencerGlisser() {
    glisse.actif = true;
    const cadre = glisse.element.getBoundingClientRect();
    glisse.decalX = glisse.x0 - cadre.left;
    glisse.decalY = glisse.y0 - cadre.top;
    // Le « fantôme » : une copie du bloc qui suit le doigt ou la souris
    glisse.fantome = glisse.element.cloneNode(true);
    glisse.fantome.classList.add("fantome");
    glisse.fantome.style.width = cadre.width + "px";
    document.body.appendChild(glisse.fantome);
    if (!glisse.nouveau) { glisse.element.classList.add("en-deplacement"); }
    glisse.repere = document.createElement("li");
    glisse.repere.className = "repere-insertion";
    zone.classList.add("depot-possible");
  }

  // Trouve où le bloc serait lâché, et y montre un trait jaune
  function chercherCible(x, y) {
    glisse.repere.remove();
    glisse.cible = null;
    const dessous = document.elementFromPoint(x, y);
    if (!dessous || !zone.contains(dessous)) { return; }
    let ol = dessous.closest("ol.programme, ol.programme-dedans");
    if (!ol || !zone.contains(ol)) { ol = liste; }   // dans la zone, mais sous la liste : à la fin
    if (!glisse.nouveau && glisse.element.contains(ol)) { return; }   // pas un conteneur dans lui-même
    if (!peutAllerDans(glisse.nom, ol.conteneur)) { return; }
    // On s'insère avant le premier bloc dont le milieu est plus bas que le doigt
    const blocs = Array.from(ol.children).filter(function (li) { return li.classList.contains("bloc"); });
    let index = blocs.length;
    for (let i = 0; i < blocs.length; i++) {
      const cadre = blocs[i].getBoundingClientRect();
      if (y < cadre.top + cadre.height / 2) { index = i; break; }
    }
    ol.insertBefore(glisse.repere, blocs[index] || null);
    glisse.cible = { liste: ol.listeBlocs, conteneur: ol.conteneur, index: index };
  }

  function finGlisser() {
    const g = glisse;
    nettoyerGlisser();
    if (!g || !g.actif) { return; }   // simple toucher : le navigateur enverra un « clic » normal
    clicBloque = true;
    setTimeout(function () { clicBloque = false; }, 0);
    if (!g.cible) { dessiner(); return; }   // lâché ailleurs : rien ne change
    let bloc;
    let index = g.cible.index;
    if (g.nouveau) {
      bloc = nouveauBloc(g.nom);
    } else {
      bloc = g.bloc;
      g.listeOrigine.splice(g.indexOrigine, 1);
      // Dans la même liste, vers le bas : retirer le bloc a décalé les suivants d'un cran
      if (g.listeOrigine === g.cible.liste && g.indexOrigine < index) { index--; }
    }
    g.cible.liste.splice(index, 0, bloc);
    // Un nouveau conteneur s'ouvre (comme avec un clic) ; sinon, on referme tout
    ouverts = [];
    if (g.nouveau && typeof bloc !== "string") {
      ouverts = g.cible.conteneur ? [g.cible.conteneur, bloc] : [bloc];
    }
    effacerMessage();
    dessiner();
  }

  function annulerGlisser() {
    const actif = glisse && glisse.actif;
    nettoyerGlisser();
    if (actif) { dessiner(); }
  }

  function nettoyerGlisser() {
    window.removeEventListener("pointermove", pendantGlisser);
    window.removeEventListener("pointerup", finGlisser);
    window.removeEventListener("pointercancel", annulerGlisser);
    if (glisse && glisse.actif) {
      glisse.fantome.remove();
      glisse.repere.remove();
      glisse.element.classList.remove("en-deplacement");
      zone.classList.remove("depot-possible");
    }
    glisse = null;
  }

  effacer.addEventListener("click", function () {
    programme = [];
    ouverts = [];
    effacerMessage();
    terrain.revenirAuDepart();
    dessiner();
  });

  lancer.addEventListener("click", function () {
    // Un conteneur vide ne fait rien : on prévient l'élève plutôt que de lancer
    if (contientUnBlocVide(programme)) {
      message.textContent = "Un bloc « Répéter » ou « Si » est vide : ajoute-lui des blocs, ou retire-le.";
      message.className = "message-robot attention";
      return;
    }
    ouverts = [];
    enCours = true;
    effacerMessage();
    terrain.revenirAuDepart();
    elementsLances = dessiner();
    const resultat = simulerRobot(question, programme, elementsLances);
    setTimeout(function () { animerRobot(terrain, resultat, finDuLancement); }, 250);
  });

  function finDuLancement(resultat) {
    essais++;
    enCours = false;
    if (resultat.arrive) {
      dessiner();
      terminer(true);
      return;
    }
    const restants = ESSAIS_ROBOT - essais;
    if (restants <= 0) {
      dessiner();
      terminer(false);
      return;
    }
    let explication = "Le robot s'est arrêté, mais pas sur l'étoile.";
    if (resultat.choc) {
      explication = "Bong ! Le robot s'est cogné. Le bloc en rouge est celui qui pose problème.";
    } else if (resultat.surLaSortie) {
      explication = "Le robot est sur la sortie, mais la variable « pièces » vaut " + resultat.pieces +
        " : il en faut " + resultat.necessaires + ". La sortie reste fermée !";
    }
    message.textContent = explication +
      " Corrige ton programme et relance ! (" + restants + (restants > 1 ? " essais restants)" : " essai restant)");
    message.className = "message-robot attention";
    const nouveaux = dessiner();
    // Le programme a été redessiné : on retrouve le bloc fautif à la même place pour le laisser en rouge
    if (resultat.choc) {
      const chemin = cheminDe(elementsLances, resultat.etapes[resultat.etapes.length - 1].element);
      let fautif = null;
      if (chemin) {
        fautif = { enfants: nouveaux };
        chemin.forEach(function (position) { fautif = fautif.enfants[position]; });
      }
      if (fautif) { fautif.ligne.classList.add("bug"); }
    }
  }

  // Position d'un bloc affiché dans l'arbre du programme : [i], [i, j] ou [i, j, k]
  function cheminDe(elements, cible) {
    for (let i = 0; i < elements.length; i++) {
      if (elements[i] === cible) { return [i]; }
      if (elements[i].enfants) {
        const suite = cheminDe(elements[i].enfants, cible);
        if (suite) { return [i].concat(suite); }
      }
    }
    return null;
  }

  function terminer(estJuste) {
    enCours = true;   // plus rien ne bouge
    dessiner();
    liste.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
    actions.hidden = true;
    palette.hidden = true;
    selecteur.hidden = true;
    message.hidden = true;
    const rappel = estJuste ? "" : "Une solution : " + programmeEnTexte(question.solution) + ". ";
    afficherCorrection(question, estJuste, rappel);
  }

  zone.append(compteur, liste);
  const cote = document.createElement("div");
  cote.className = "robot-cote";
  const selecteur = creerSelecteurVitesse();
  cote.append(palette, zone, actions, selecteur, message);
  const plateau = document.createElement("div");
  plateau.className = "robot-plateau";
  plateau.append(terrain.element, cote);
  reponses.append(aide, plateau);
  dessiner();
}

// --- Les leçons (programmation) ---
// donnees/<groupe>/<matiere>/lecons/<theme>.json : une liste d'écrans
//   [ { "titre": "...", "texte": "Un paragraphe.\nUn autre paragraphe.", "image": "...", "alt": "...",
//       "demo": { "grille": ..., "depart": ..., "cible": ..., "murs": [...], "programme": [...] } }, ... ]
let ecransLecon = [];
let numeroEcran = 0;
let quandLeconFinie = null;    // ce qu'on fait en quittant la leçon (lancer ou reprendre le quiz)

let texteFinLecon = "";        // texte du bouton du dernier écran

function ouvrirLecon(ecrans, quandFinie, texteFin) {
  ecransLecon = ecrans;
  texteFinLecon = texteFin;
  numeroEcran = 0;
  quandLeconFinie = quandFinie;
  document.getElementById("lecon").hidden = false;
  afficherEcran();
}

function afficherEcran() {
  const ecran = ecransLecon[numeroEcran];
  const dernier = numeroEcran === ecransLecon.length - 1;
  document.getElementById("progression").textContent =
    "Leçon – écran " + (numeroEcran + 1) + " sur " + ecransLecon.length;
  ecrireTexte(document.getElementById("lecon-titre"), ecran.titre);

  const texte = document.getElementById("lecon-texte");
  texte.innerHTML = "";
  (ecran.texte || "").split("\n").forEach(function (paragraphe) {
    const p = document.createElement("p");
    ecrireTexte(p, paragraphe);
    texte.appendChild(p);
  });

  const figure = document.getElementById("lecon-figure");
  const image = figure.querySelector("img");
  if (ecran.image) {
    image.src = ecran.image;
    image.alt = ecran.alt || "";
    figure.hidden = false;
  } else {
    image.removeAttribute("src");
    figure.hidden = true;
  }

  const demo = document.getElementById("lecon-demo");
  demo.innerHTML = "";
  if (ecran.demo) { demo.appendChild(creerDemo(ecran.demo)); }

  document.getElementById("lecon-precedent").hidden = numeroEcran === 0;
  const suivant = document.getElementById("lecon-suivant");
  suivant.textContent = dernier ? texteFinLecon : "Suivant →";
  suivant.classList.toggle("dernier", dernier);
}

function brancherLecon() {
  document.getElementById("lecon-precedent").addEventListener("click", function () {
    numeroEcran--;
    afficherEcran();
  });
  document.getElementById("lecon-suivant").addEventListener("click", function () {
    if (numeroEcran < ecransLecon.length - 1) {
      numeroEcran++;
      afficherEcran();
    } else {
      document.getElementById("lecon").hidden = true;
      quandLeconFinie();
    }
  });
}

// ---------- 6. Démarrage selon la page ----------
// Chaque page HTML indique son type dans <body data-page="...">
const page = document.body.dataset.page;
if (page === "niveau") {
  pageNiveau();
} else if (page === "cahier") {
  pageCahier();
}
