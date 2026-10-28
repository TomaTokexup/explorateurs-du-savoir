// =========================================================
// Explorateurs du Savoir — moteur de QCM
// =========================================================

// ---------- 1. Les données ----------
// Les questions ne sont plus écrites ici : elles sont lues dans un
// fichier JSON produit par un script Python (outils/generer_maths.py).
// Le fichier à lire est indiqué dans maths.html (attribut data-fichier).
// Format d'une question :
//   { "enonce": "...", "choix": ["...", ...], "bonneReponse": 0, "explication": "..." }
// "bonneReponse" est la POSITION de la bonne réponse dans "choix", à partir de 0.
let questions = [];

// Mélange les choix d'une question (pour que la bonne réponse ne soit
// pas toujours au même endroit) et recalcule la position de la bonne réponse.
function melangerChoix(question) {
  const bonneReponseTexte = question.choix[question.bonneReponse];
  const choixMelanges = question.choix.slice();          // copie de la liste
  for (let i = choixMelanges.length - 1; i > 0; i--) {   // mélange de Fisher-Yates
    const j = Math.floor(Math.random() * (i + 1));
    [choixMelanges[i], choixMelanges[j]] = [choixMelanges[j], choixMelanges[i]];
  }
  return {
    enonce: question.enonce,
    choix: choixMelanges,
    bonneReponse: choixMelanges.indexOf(bonneReponseTexte),
    explication: question.explication
  };
}

// Va chercher le fichier JSON, puis démarre le quiz.
// "async/await" : on attend la réponse du serveur sans bloquer la page.
let questionsOriginales = [];

async function chargerQuestions() {
  const fichier = document.body.dataset.fichier;   // ex. "donnees/maths.json"
  try {
    const reponse = await fetch(fichier);
    if (!reponse.ok) {
      throw new Error("fichier introuvable (" + reponse.status + ")");
    }
    questionsOriginales = await reponse.json();
    demarrer();
  } catch (erreur) {
    // Message pour l'adulte qui teste : la cause la plus fréquente est
    // d'avoir ouvert la page en double-cliquant (file://) au lieu de passer par un serveur.
    enonce.textContent = "Impossible de charger les questions.";
    progression.textContent = "Erreur : " + erreur.message;
    console.error(erreur);
  }
}

function demarrer() {
  questions = questionsOriginales.map(melangerChoix);
  numeroQuestion = 0;
  score = 0;
  afficherQuestion();
}

// ---------- 2. L'état du quiz (ce qui change pendant le jeu) ----------
let numeroQuestion = 0;   // index de la question affichée
let score = 0;            // nombre de bonnes réponses

// ---------- 3. Les éléments de la page qu'on va modifier ----------
// document.getElementById("x") retrouve l'élément HTML qui a id="x"
const zoneQuestion = document.getElementById("zone-question");
const progression = document.getElementById("progression");
const enonce = document.getElementById("enonce");
const reponses = document.getElementById("reponses");
const correction = document.getElementById("correction");
const verdict = document.getElementById("verdict");
const explication = document.getElementById("explication");
const boutonSuivant = document.getElementById("bouton-suivant");
const bilan = document.getElementById("bilan");
const scoreTexte = document.getElementById("score");
const messageBilan = document.getElementById("message-bilan");
const boutonRecommencer = document.getElementById("bouton-recommencer");

// ---------- 4. Afficher une question ----------
function afficherQuestion() {
  const question = questions[numeroQuestion];

  // Texte de progression et énoncé
  progression.textContent = "Question " + (numeroQuestion + 1) + " sur " + questions.length;
  enonce.textContent = question.enonce;

  // On vide les anciennes réponses et on cache la correction
  reponses.innerHTML = "";
  correction.hidden = true;
  boutonSuivant.hidden = true;

  // Pour chaque choix, on crée un bouton
  question.choix.forEach(function (texteChoix, position) {
    const bouton = document.createElement("button");
    bouton.className = "reponse";
    bouton.textContent = texteChoix;

    // Quand on clique sur ce bouton, on vérifie la réponse
    bouton.addEventListener("click", function () {
      verifierReponse(position);
    });

    reponses.appendChild(bouton);
  });
}

// ---------- 5. Vérifier la réponse choisie ----------
function verifierReponse(positionChoisie) {
  const question = questions[numeroQuestion];
  const estJuste = positionChoisie === question.bonneReponse;
  const boutons = reponses.querySelectorAll(".reponse");

  // On colore les boutons et on les bloque (un seul essai)
  boutons.forEach(function (bouton, position) {
    bouton.disabled = true;
    if (position === question.bonneReponse) {
      bouton.classList.add("juste");
    } else if (position === positionChoisie) {
      bouton.classList.add("faux");
    } else {
      bouton.classList.add("attenuee");
    }
  });

  // On affiche la correction
  if (estJuste) {
    score = score + 1;
    verdict.textContent = "Bravo, c'est juste !";
    correction.className = "correction juste";
  } else {
    verdict.textContent = "Pas tout à fait…";
    correction.className = "correction faux";
  }
  explication.textContent = question.explication;
  correction.hidden = false;

  // Bouton pour continuer (texte différent à la dernière question)
  const derniereQuestion = numeroQuestion === questions.length - 1;
  boutonSuivant.textContent = derniereQuestion ? "Voir mon score" : "Question suivante";
  boutonSuivant.hidden = false;
  boutonSuivant.focus();
}

// ---------- 6. Passer à la suite ----------
boutonSuivant.addEventListener("click", function () {
  numeroQuestion = numeroQuestion + 1;
  if (numeroQuestion < questions.length) {
    afficherQuestion();
  } else {
    afficherBilan();
  }
});

// ---------- 7. Écran de fin ----------
function afficherBilan() {
  zoneQuestion.hidden = true;
  progression.textContent = "Terminé !";
  bilan.hidden = false;

  scoreTexte.textContent = score + " / " + questions.length;

  if (score === questions.length) {
    messageBilan.textContent = "Parfait ! Tu es un vrai explorateur des maths.";
  } else if (score >= questions.length / 2) {
    messageBilan.textContent = "Bien joué ! Encore un essai pour tout réussir ?";
  } else {
    messageBilan.textContent = "Continue de t'entraîner, tu vas y arriver !";
  }
}

boutonRecommencer.addEventListener("click", function () {
  bilan.hidden = true;
  zoneQuestion.hidden = false;
  demarrer();   // nouveau mélange des choix à chaque partie
});

// ---------- 8. Démarrage ----------
chargerQuestions();
