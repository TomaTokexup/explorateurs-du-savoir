// =========================================================
// Explorateurs du Savoir — moteur de QCM
// =========================================================

// ---------- 1. Les données : la liste des questions ----------
// Chaque question est un "objet" avec 4 propriétés.
// "bonneReponse" est la POSITION de la bonne réponse dans la liste
// des choix, en comptant à partir de 0 (0 = 1er choix, 1 = 2e choix...).
// À la phase 3, cette liste sortira du code pour aller dans un fichier JSON.
const questions = [
  {
    enonce: "Combien font 7 × 8 ?",
    choix: ["54", "56", "48", "64"],
    bonneReponse: 1,
    explication: "7 × 8 = 56. Astuce : 5, 6, 7, 8 → 56 = 7 × 8 !"
  },
  {
    enonce: "Quel est le double de 45 ?",
    choix: ["80", "85", "90", "95"],
    bonneReponse: 2,
    explication: "Le double, c'est 2 fois le nombre : 45 + 45 = 90."
  },
  {
    enonce: "Combien y a-t-il de minutes dans 2 heures ?",
    choix: ["100", "120", "200", "60"],
    bonneReponse: 1,
    explication: "1 heure = 60 minutes, donc 2 heures = 60 + 60 = 120 minutes."
  },
  {
    enonce: "Quelle fraction représente la moitié ?",
    choix: ["1/3", "1/4", "2/2", "1/2"],
    bonneReponse: 3,
    explication: "La moitié, c'est 1 part sur 2 parts égales : 1/2."
  }
];

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
  numeroQuestion = 0;
  score = 0;
  bilan.hidden = true;
  zoneQuestion.hidden = false;
  afficherQuestion();
});

// ---------- 8. Démarrage ----------
afficherQuestion();
