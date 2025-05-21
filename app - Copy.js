// === SCREEN SETUP ===
const screens = {
  login:       document.getElementById('login-screen'),
  home:        document.getElementById('home-screen'),
  grade:       document.getElementById('grade-screen'),
  module:      document.getElementById('module-screen'),
  video:       document.getElementById('video-screen'),
  quiz:        document.getElementById('quiz-screen'),
  performance: document.getElementById('performance-screen'),
};

const spinner             = document.getElementById('spinner');
const mainContent         = document.getElementById('main-content');
const loginBtn            = document.getElementById('login-btn');
const logoutBtn           = document.getElementById('logout-btn');
const subjectBtns         = document.querySelectorAll('.subject-btn');
const gradeBtns           = document.querySelectorAll('.grade-btn');
const backHomeBtns        = [
  document.getElementById('back-home-btn'),
  document.getElementById('back-home-btn2')
];
const backGradeBtn        = document.getElementById('back-grade-btn');
const backModuleBtn       = document.getElementById('back-module-btn');

const subjectTitle        = document.getElementById('subject-title');
const moduleHeader        = document.getElementById('module-header');
const accordionContainer  = document.getElementById('learning-accordion');
const rainContainerGrade  = document.getElementById('rain-container');
const rainContainerModule = document.getElementById('rain-container-module');

// Quiz‐screen elements
const quizHeader       = document.getElementById('quiz-header');
const quizProgressText = document.getElementById('quiz-progress');
const quizProgressBar  = document.getElementById('quiz-progress-bar');
const quizForm         = document.getElementById('quiz-form');
const submitQuizBtn    = document.getElementById('submit-quiz-btn');
const backQuizBtn      = document.getElementById('back-video-btn');

let currentSubject = null;
let currentGrade   = null;
let currentLesson  = null;
let currentQIndex  = 0;

// === Helper to show exactly one screen ===
function showScreen(name) {
  Object.values(screens).forEach(s => s.classList.remove('active'));
  screens[name].classList.add('active');
}

// === DEBUG LOG ===
console.log("🔥 app.js loaded!");

// === DATA ===
const topics = {
  Math: {
    1: [
      {
        theme: 'Number Sense & Counting',
        videoId: 'VIDEO_ID_1',
        content: [
          'In this lesson we explore how to count from 1 to 20.',
          'You will practice grouping objects into sets of 10.'
        ]
      },
      {
        theme: 'Place Value',
        videoId: 'VIDEO_ID_2',
        content: [
          'Learn how ones and tens place work together.',
          'We use base-10 blocks to visualize numbers.'
        ]
      }
      // …etc…
    ],
    2: [ /* … Grade-2 … */ ]
  },
  English: {
    1: [ /* … */ ],
    2: [ /* … */ ]
  }
};

const quizzes = {
  Math: {
    1: [
      // Lesson 0
      [
        {
          q: 'How many apples do you see if you count from 1 to 5?',
          options: ['3','5','7','10'],
          answerIndex: 1
        },
        {
          q: 'Group these 12 blocks into sets of 10. How many leftover?',
          options: ['0','1','2','10'],
          answerIndex: 2
        }
      ],
      // Lesson 1
      [
        {
          q: 'In the number 15, the “1” is in the ______ place.',
          options: ['ones','tens','hundreds','thousands'],
          answerIndex: 1
        }
      ]
    ],
    2: [ /* … */ ]
  },
  English: {
    1: [ /* … */ ],
    2: [ /* … */ ]
  }
};

// === Accordion Renderer ===
function renderAccordion(grade) {
  currentGrade = grade;
  moduleHeader.textContent = `${currentSubject} — Grade ${grade}`;
  accordionContainer.innerHTML = '';

  const lessons = topics[currentSubject][grade] || [];
  lessons.forEach((lesson, idx) => {
    const item = document.createElement('div');
    item.className = 'accordion-item';
    item.innerHTML = `
      <h2 class="accordion-header" id="heading${idx}">
        <button
          class="accordion-button collapsed"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#collapse${idx}"
          aria-expanded="false"
          aria-controls="collapse${idx}"
        >
          ${idx + 1}. ${lesson.theme}
        </button>
      </h2>
      <div
        id="collapse${idx}"
        class="accordion-collapse collapse"
        aria-labelledby="heading${idx}"
        data-bs-parent="#learning-accordion"
      >
        <div class="accordion-body">
          <div class="video-container mb-3">
            <iframe
              src="https://www.youtube.com/embed/${lesson.videoId}"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen
            ></iframe>
          </div>
          <div class="learning-content mb-3">
            ${lesson.content.map(p => `<p>${p}</p>`).join('')}
          </div>
          <button
            class="btn btn-success btn-start-quiz"
            data-lesson-index="${idx}"
          >Start Quiz</button>
        </div>
      </div>
    `;
    accordionContainer.appendChild(item);
  });

  // Hook up “Start Quiz” buttons
  accordionContainer.querySelectorAll('.btn-start-quiz')
    .forEach(btn => {
      btn.addEventListener('click', () => {
        currentLesson = +btn.dataset.lessonIndex;
        currentQIndex  = 0;
        startQuiz();
      });
    });
}

// === Quiz Logic ===
function startQuiz() {
  const qList = (quizzes[currentSubject] || {})[currentGrade]?.[currentLesson] || [];
  if (!qList.length) {
    alert('No quiz defined for this lesson yet!');
    return;
  }
  showScreen('quiz');
  renderQuizQuestion();
}

function renderQuizQuestion() {
  const qList = quizzes[currentSubject][currentGrade][currentLesson];
  const qObj  = qList[currentQIndex];

  // 1) Header
  quizHeader.textContent = `Quiz: ${topics[currentSubject][currentGrade][currentLesson].theme}`;

  // 2) Progress
  quizProgressText.textContent = `Question ${currentQIndex+1} / ${qList.length}`;
  quizProgressBar.style.width = `${((currentQIndex+1) / qList.length) * 100}%`;

  // 3) Build form: include the question text!
  quizForm.innerHTML = `
    <div class="mb-3">
      <strong>${qObj.q}</strong>
    </div>
    ${qObj.options.map((opt, i) => `
      <div class="form-check mb-2">
        <input
          class="form-check-input"
          type="radio"
          name="quiz-option"
          id="opt-${i}"
          value="${i}"
        />
        <label class="form-check-label" for="opt-${i}">
          ${opt}
        </label>
      </div>
    `).join('')}
  `;
}

submitQuizBtn.addEventListener('click', () => {
  const selectedInput = quizForm.querySelector('input[name="quiz-option"]:checked');
  if (!selectedInput) {
    alert('Please select an answer.');
    return;
  }
  const selected = +selectedInput.value;
  const correct  = quizzes[currentSubject][currentGrade][currentLesson][currentQIndex].answerIndex;

  if (selected === correct) {
    alert('✅ Correct!');
  } else {
    alert('❌ Incorrect.');
  }

  // Next question or back to module
  const qList = quizzes[currentSubject][currentGrade][currentLesson];
  if (currentQIndex < qList.length - 1) {
    currentQIndex++;
    renderQuizQuestion();
  } else {
    showScreen('module');
  }
});

// Back from quiz → module
backQuizBtn.addEventListener('click', () => showScreen('module'));

// === Rain Effect (unchanged) ===
function renderRain(subject, container) {
  container.innerHTML = '';
  const icon = subject === 'English' ? 'fa-book' : 'fa-calculator';
  for (let i = 0; i < 25; i++) {
    const drop = document.createElement('i');
    drop.className = `fas ${icon} rain-icon`;
    drop.style.left              = `${Math.random() * 100}%`;
    drop.style.fontSize          = `${Math.random() * 24 + 16}px`;
    drop.style.animationDuration = `${Math.random() * 3 + 3}s`;
    container.appendChild(drop);
  }
}

// === INIT & NAVIGATION ===
document.addEventListener('DOMContentLoaded', () => {
  console.log("DOMContentLoaded fired");
  spinner.style.display     = 'none';
  mainContent.style.display = 'block';
  showScreen('login');
});

// Login → Home
loginBtn?.addEventListener('click', () => showScreen('home'));
// Logout → Login
logoutBtn?.addEventListener('click', () => showScreen('login'));

// Subject → Grade
subjectBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    currentSubject = btn.dataset.subject;
    subjectTitle.textContent = currentSubject;
    showScreen('grade');
    renderRain(currentSubject, rainContainerGrade);
  });
});

// Grade → Module
gradeBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    showScreen('module');
    renderRain(currentSubject, rainContainerModule);
    renderAccordion(btn.dataset.grade);
  });
});

// Back to Home
backHomeBtns.forEach(b => b?.addEventListener('click', () => showScreen('home')));

// Back to Grade
backGradeBtn?.addEventListener('click', () => showScreen('grade'));

// Back to Module
backModuleBtn?.addEventListener('click', () => showScreen('module'));
