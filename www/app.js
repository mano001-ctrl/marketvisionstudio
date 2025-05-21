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

// grab the new container
const moduleHeader       = document.getElementById('module-header');
const moduleMenuContainer = document.getElementById('module-menu-container');

// after your existing screens.themeMenu = …
screens.library   =      document.getElementById('library');
screens.profile   =      document.getElementById('profile');
// after your other screens
screens.themeMenu =    document.getElementById('theme-menu-screen');



// after your other back-buttons:
document.getElementById('back-home-library')
  .addEventListener('click', () => showScreen('home'));

document.getElementById('back-home-profile')
  .addEventListener('click', () => showScreen('home'));


// — Theme-Menu screen —
screens.themeMenu        = document.getElementById('theme-menu-screen');
const themeMenuHeader    = document.getElementById('theme-menu-header');
const themeMenuContainer = document.getElementById('theme-menu-container');
const backToGradeBtn     = document.getElementById('back-to-grade-btn');
const performanceBtn     = document.getElementById('performance-btn');



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
const accordionContainer  = document.getElementById('learning-accordion');
const rainContainerGrade  = document.getElementById('rain-container');
const rainContainerModule = document.getElementById('rain-container-module');

// === MOTIVATIONAL QUOTES ===
const motivationalQuotes = [
  "✨ Believe you can and you’re halfway there.",
  "🚀 Dream big and dare to fail.",
  "🌟 Every day is a second chance.",
  // … (32 more lines)
  "💪 Tough times never last but tough people do."
];


//const playVideoBtn   = document.getElementById('play-video-btn');
const proceedQuizBtn = document.getElementById('proceed-quiz-btn');


// Quiz–screen elements
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
let currentCorrectCount = 0; 
let perfChart = null;
let perfBarChart = null;
let isLibraryFlow = false;


function showScreen(name, replace = false) {
  // 1) hide every screen
  Object.values(screens).forEach(s => s.classList.remove('active'));

  // 2) show the one we want
  screens[name].classList.add('active');

  // 3) sync bottom-nav: add .active only to the matching tab
  document.querySelectorAll('.bottom-nav .nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.screen === name);
  });

  // 4) special case: if it’s the performance panel, rebuild its list
  if (name === 'performance') {
    renderPerformance();
  }

  // 5) update URL & history
  const url = `#${name}`;
  if (replace) {
    history.replaceState({screen: name}, '', url);
  } else {
    history.pushState({screen: name}, '', url);
  }
}



// wire up bottom-nav clicks
document.querySelectorAll('.bottom-nav .nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    // 1) remove .active from all
    document.querySelectorAll('.bottom-nav .nav-item')
      .forEach(b => b.classList.remove('active'));

    // 2) mark this one active
    btn.classList.add('active');

    // 3) show the corresponding screen
    const screenName = btn.dataset.screen;
    showScreen(screenName);
  });
});


// handle browser Back/Forward
window.addEventListener('popstate', e => {
  const name = (e.state && e.state.screen) || 'login';
  showScreen(name, true);
});

// on first load, read existing hash or default
document.addEventListener('DOMContentLoaded', () => {
  // ————————————
  // PROFILE PIC SETUP
  // ————————————
  const img   = document.getElementById('profile-pic');
  const input = document.getElementById('profile-upload');

  // load saved avatar
  const saved = localStorage.getItem('profilePic');
  if (saved) img.src = saved;

  // wire up new uploads
  input.addEventListener('change', e => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      img.src = ev.target.result;
      localStorage.setItem('profilePic', ev.target.result);
    };
    input.value = '';
    reader.readAsDataURL(file);
  });

  // ————————————
  // EXPORT PDF SETUP
  // ————————————
  // fire this after you _create_ perfChart & perfBarChart, and
// put it inside your DOMContentLoaded so html2pdf & Chart.js are both loaded
const exportBtn = document.getElementById('export-pdf-btn');
exportBtn.addEventListener('click', () => {
  if (typeof html2pdf !== 'function') {
    console.error('html2pdf.js not found');
    return;
  }

  // 1) Clone & strip off nav/back links
  const perfCard = document.querySelector('#performance-screen .screen-card');
  const clone    = perfCard.cloneNode(true);
  clone.querySelector('.bottom-nav')?.remove();
  clone.querySelector('#back-home-btn2')?.remove();

  // 2) Inject your two Chart images at the top:
  // — Line chart
  if (perfChart) {
    const lineImg = perfChart.toBase64Image();
    const imgEl   = document.createElement('img');
    imgEl.src     = lineImg;
    imgEl.style.width        = '100%';
    imgEl.style.marginBottom = '16px';
    clone.insertBefore(imgEl, clone.firstChild);
  }
  // — Bar chart
  if (perfBarChart) {
    const barImg = perfBarChart.toBase64Image();
    const imgEl  = document.createElement('img');
    imgEl.src    = barImg;
    imgEl.style.width        = '100%';
    imgEl.style.marginBottom = '16px';
    // right after the line chart
    clone.insertBefore(imgEl, clone.children[1] || null);
  }

  // 3) Build your raw‐scores table
  const data = JSON.parse(localStorage.getItem('performanceData') || '[]');
  const table = document.createElement('table');
  table.style.width          = '100%';
  table.style.borderCollapse = 'collapse';
  table.style.marginTop      = '20px';

  // header
  const thead = table.createTHead();
  const hrow  = thead.insertRow();
  ['Subject','Grade','Lesson','Correct','Total'].forEach(txt => {
    const th = document.createElement('th');
    th.textContent      = txt;
    th.style.border     = '1px solid #ddd';
    th.style.padding    = '8px';
    th.style.background = '#f2f2f2';
    hrow.appendChild(th);
  });

  // rows
  const tbody = table.createTBody();
  data.forEach(({subject, grade, lesson, correct, total}) => {
    const row = tbody.insertRow();
    [subject, grade, lesson, correct, total].forEach(val => {
      const td = row.insertCell();
      td.textContent   = val;
      td.style.border  = '1px solid #ddd';
      td.style.padding = '8px';
    });
  });

  clone.appendChild(table);

  // 4) Wrap and hand to html2pdf
  const wrapper = document.createElement('div');
  wrapper.style.background = '#fff';
  wrapper.style.padding    = '20px';
  wrapper.appendChild(clone);
  document.body.appendChild(wrapper);

  html2pdf()
    .set({
      margin:      [10,10,10,10],
      filename:    'performance-report.pdf',
      html2canvas: { scale: 2, logging: false, useCORS: true },
      jsPDF:       { unit: 'pt', format: 'a4', orientation: 'portrait' }
    })
    .from(wrapper)
    .save()
    .then(() => document.body.removeChild(wrapper));
});


// === DATA ===
const topics = {
  Math: {
    1: [
      {
        theme: 'Number Sense & Counting',
        description: `Playing with numbers from one to twenty builds a strong counting foundation. 
You’ll use catchy songs and colorful visuals to practice counting forwards and backwards. 
By the end of this lesson, you’ll recognize every number in the sequence with confidence.`,
        videoId: 'D0Ajq682yrA',
        content: [ /* … */ ]
      },
      {
        theme: 'Place Value',
        description: `Understanding tens and ones unlocks the secret of two-digit numbers. 
You will use base-10 blocks and diagrams to see how each digit’s place gives it value. 
Hands-on examples will help you master numbers up to ninety-nine.`,
        videoId: '1F3AycEDksY',
        content: [ /* … */ ]
      },
      {
        theme: 'Simple Addition within 20',
        description: `Adding single-digit numbers becomes fun with games and visual tools. 
Practice combining numbers up to twenty using counters, drawings, and story problems. 
By the end, you’ll write correct sums with ease.`,
        videoId: 'uQiUTFO78Jk',
        content: [ /* … */ ]
      },
      {
        theme: 'Simple Subtraction within 20',
        description: `Subtracting within twenty is easier when you break problems into steps. 
You’ll practice taking away objects and using a number line to see each move. 
Multiple examples will help you master subtraction facts confidently.`,
        videoId: 'fny08Url8ik',
        content: [ /* … */ ]
      },
      {
        theme: 'Comparing Numbers & Ordering',
        description: `Learning to compare numbers shows which are bigger, smaller, or equal. 
You will use the >, <, and = symbols and arrange lists of numbers in order. 
Hands-on sorting activities will cement your understanding of number order.`,
        videoId: 'Qn87cKHa7v4',
        content: [ /* … */ ]
      }
    ],
    2: [
      {
        theme: 'Addition & Subtraction within 100',
        description: `Working with two-digit numbers introduces regrouping strategies. 
You will practice carrying over in addition and borrowing in subtraction step by step. 
Real-world problems will show you how to manage sums and differences up to one hundred.`,
        videoId: 'h_Wkwhvug4s',
        content: [ /* … */ ]
      },
      {
        theme: 'Understanding Money',
        description: `Counting coins and notes is a valuable everyday skill. 
You will identify South African coins, calculate totals, and practice making change. 
Interactive exercises will build your practical money sense.`,
        videoId: 'MbtmucV-U2c',
        content: [ /* … */ ]
      },
      {
        theme: 'Telling Time on an Analog Clock',
        description: `Reading the clock face helps you know hour, half-hour, and quarter-hour times. 
This lesson teaches you to spot the positions of both hands and tell time accurately. 
You’ll draw clocks and match them to written times in fun activities.`,
        videoId: 'bZY8WNMRcQ8',
        content: [ /* … */ ]
      },
      {
        theme: '2D Shapes & Their Properties',
        description: `Polygons come in all shapes, each with its own sides and angles. 
You will explore triangles, squares, pentagons, and more, counting sides and vertices. 
Sorting shapes and identifying right angles will sharpen your geometry skills.`,
        videoId: 'eVeEOJuuKLc',
        content: [ /* … */ ]
      },
      {
        theme: 'Data & Bar Graphs',
        description: `Collecting and displaying information makes data easy to understand. 
You will gather simple categories, build bar graphs, and interpret what the bars show. 
Questions will guide you in reading charts accurately.`,
        videoId: 'nDaKJBjZszQ',
        content: [ /* … */ ]
      }
    ]
  },

  English: {
    1: [
      {
        theme: 'Alphabet & Letter Sounds',
        description: `Letters and their sounds are the first step toward reading. 
You’ll practice recognizing uppercase and lowercase letters and matching them to phonetic sounds. 
Engaging activities will help you master each letter in the alphabet.`,
        videoId: '75p-N9YKqNo',
        content: [ /* … */ ]
      },
      {
        theme: 'Building Sight Word Vocabulary',
        description: `Common sight words let you read smoothly without sounding out every letter. 
In this lesson, you’ll learn high-frequency words and practice them through fun word games. 
Instantly recognizing these words will boost your reading fluency.`,
        videoId: 'gIZjrcG9pW0',
        content: [ /* … */ ]
      },
      {
        theme: 'Simple Sentence Structure',
        description: `Putting words in the correct order creates clear sentences. 
You’ll identify the subject and verb in simple two-word sentences and practice writing your own. 
Reading and writing exercises will build your confidence.`,
        videoId: 'A2-zPYGvKro',
        content: [ /* … */ ]
      },
      {
        theme: 'Listening & Speaking Skills',
        description: `Good communication begins with listening carefully and speaking clearly. 
You’ll follow one- and two-step directions and answer questions accurately. 
Show-and-tell activities will help you practice speaking in front of others.`,
        videoId: 'CdM_rrHTYDU',
        content: [ /* … */ ]
      },
      {
        theme: 'Rhyming & Word Families',
        description: `Rhymes make words fun and easier to remember. 
You will group words by common endings like –at, –an, and –ig in word-family activities. 
Rhyming games will strengthen your reading and spelling skills.`,
        videoId: 'B5-y__faQrY',
        content: [ /* … */ ]
      }
    ],
    2: [
      {
        theme: 'Reading Fluency & Expression',
        description: `Fluent reading sounds smooth and full of expression. 
You’ll practice reading passages with the right pace, tone, and emotion. 
Echo and choral reading will help you bring stories to life.`,
        videoId: 'i0cQu7vnDzs',
        content: [ /* … */ ]
      },
      {
        theme: 'Expanding Vocabulary',
        description: `A rich vocabulary helps you understand and enjoy every text. 
You will learn new words, use context clues to guess meanings, and match words to pictures. 
Activities will reinforce your understanding and word usage.`,
        videoId: '3dztlsaWrjw',
        content: [ /* … */ ]
      },
      {
        theme: 'Grammar: Nouns & Verbs',
        description: `Sentences need nouns (things) and verbs (actions) to make sense. 
In this lesson, you’ll identify nouns and verbs in simple sentences. 
Writing exercises will help you use both parts of speech correctly.`,
        videoId: '8irI5t3ZLPs',
        content: [ /* … */ ]
      },
      {
        theme: 'Creative Writing: Short Stories',
        description: `Writing your own stories sparks imagination and creativity. 
You’ll brainstorm characters, settings, and plot ideas before you write. 
By structuring a clear beginning, middle, and end, you’ll craft engaging short stories.`,
        videoId: 'M7jmKm5EuRs',
        content: [ /* … */ ]
      },
      {
        theme: 'Reading Comprehension',
        description: `Understanding a story means answering who, what, when, and where questions. 
You’ll practice making inferences and summarizing key details from passages. 
Comprehension activities will deepen your reading insights.`,
        videoId: 'n9lDqCO0pBQ',
        content: [ /* … */ ]
      }
    ]
  }
};



const quizzes = {
  Math: {
    1: [
      // Lesson 0: Number Sense & Counting
      [
        { q: 'How many apples do you see if you count from 1 to 5?', 
          options: ['3','5','7','10'], answerIndex: 1 },

        { q: 'Group these 12 blocks into sets of 10. How many leftover?', 
          options: ['0','1','2','10'], answerIndex: 2 },

        { q: 'What number comes after 17?', 
          options: ['16','18','19','20'], answerIndex: 1 },

        { q: 'If you have 4 oranges and pick 2 more, how many total?', 
          options: ['4','6','8','10'], answerIndex: 1 },

        { q: 'Which is an even number?', 
          options: ['3','7','8','11'], answerIndex: 2 }
      ],

      // Lesson 1: Place Value
      [
        { q: 'In the number 32, what digit is in the tens place?', 
          options: ['3','2','5','0'], answerIndex: 0 },

        { q: 'What is the value of the digit 5 in the number 157?', 
          options: ['5','50','500','5000'], answerIndex: 1 },

        { q: 'When you see 4 tens and 3 ones, that number is ____.', 
          options: ['34','43','40','3'], answerIndex: 0 },

        { q: 'Which of these numbers has a 6 in the ones place?', 
          options: ['56','61','46','64'], answerIndex: 0 },

        { q: 'How many tens make 50?', 
          options: ['2','3','4','5'], answerIndex: 3 }
      ],

      // Lesson 2: Simple Addition within 20
      [
        { q: 'What is 7 + 5?', 
          options: ['10','11','12','13'], answerIndex: 2 },

        { q: 'What is 9 + 6?', 
          options: ['14','15','16','13'], answerIndex: 1 },

        { q: 'What is 4 + 8?', 
          options: ['11','12','13','14'], answerIndex: 1 },

        { q: 'What is 10 + 7?', 
          options: ['16','17','18','19'], answerIndex: 1 },

        { q: 'What is 5 + 5?', 
          options: ['9','10','11','12'], answerIndex: 1 }
      ],

      // Lesson 3: Simple Subtraction within 20
      [
        { q: 'What is 15 − 7?', 
          options: ['6','7','8','9'], answerIndex: 2 },

        { q: 'What is 12 − 4?', 
          options: ['7','8','9','10'], answerIndex: 1 },

        { q: 'What is 10 − 3?', 
          options: ['6','7','8','9'], answerIndex: 1 },

        { q: 'What is 18 − 9?', 
          options: ['8','9','10','11'], answerIndex: 1 },

        { q: 'What is 20 − 5?', 
          options: ['14','15','16','17'], answerIndex: 1 }
      ],

      // Lesson 4: Comparing Numbers & Ordering
      [
        { q: 'Which number is greater: 8 or 5?', 
          options: ['5','8','Both equal','Neither'], answerIndex: 1 },

        { q: 'Which number is less: 3 or 9?', 
          options: ['3','9','Both','Neither'], answerIndex: 0 },

        { q: 'Which symbol makes 4 _ 7 true?', 
          options: ['>','<','='], answerIndex: 1 },

        { q: 'Order these from least to greatest: 5, 2, 7.', 
          options: ['2,5,7','5,2,7','7,5,2','2,7,5'], answerIndex: 0 },

        { q: 'Which symbol makes 6 _ 6 true?', 
          options: ['>','<','='], answerIndex: 2 }
      ]
    ],

    2: [
      // Lesson 0: Addition & Subtraction within 100
      [
        { q: 'What is 23 + 45?', 
          options: ['68','67','69','70'], answerIndex: 0 },

        { q: 'What is 80 − 19?', 
          options: ['61','60','62','63'], answerIndex: 0 },

        { q: 'What is 56 + 44?', 
          options: ['100','99','101','102'], answerIndex: 0 },

        { q: 'What is 100 − 37?', 
          options: ['63','62','61','64'], answerIndex: 0 },

        { q: 'What is 30 + 0?', 
          options: ['30','29','31','32'], answerIndex: 0 }
      ],

      // Lesson 1: Understanding Money
      [
        { q: 'A quarter is worth how many cents?', 
          options: ['10','25','5','50'], answerIndex: 1 },

        { q: 'Which coin is worth half a rand?', 
          options: ['10c','20c','50c','5c'], answerIndex: 2 },

        { q: 'If you pay with a 2 R coin for a 1 R snack, how much change?', 
          options: ['R0.50','R1','R2','R0'], answerIndex: 1 },

        { q: 'You have two 50c and three 20c coins. Total?', 
          options: ['R1.60','R1.30','R1.20','R1.50'], answerIndex: 0 },

        { q: 'Which coin is the smallest value?', 
          options: ['5c','10c','20c','50c'], answerIndex: 0 }
      ],

      // Lesson 2: Telling Time on an Analog Clock
      [
        { q: 'What time is it when the hour hand is on 3 and the minute hand on 12?', 
          options: ['3:00','12:15','3:30','6:00'], answerIndex: 0 },

        { q: 'What time is “half past 7”?', 
          options: ['7:15','7:30','8:15','8:30'], answerIndex: 1 },

        { q: 'When minute hand points to 6, how many minutes past?', 
          options: ['10','20','30','40'], answerIndex: 2 },

        { q: 'At 5:45, minute hand is pointing at which number?', 
          options: ['9','3','6','12'], answerIndex: 0 },

        { q: 'Which shows quarter past 2?', 
          options: ['2:15','2:30','2:45','3:15'], answerIndex: 0 }
      ],

      // Lesson 3: 2D Shapes & Their Properties
      [
        { q: 'How many sides does a pentagon have?', 
          options: ['4','5','6','7'], answerIndex: 1 },

        { q: 'Which shape has all sides equal and all angles 90°?', 
          options: ['Rectangle','Triangle','Square','Circle'], answerIndex: 2 },

        { q: 'A rectangle has how many right angles?', 
          options: ['1','2','3','4'], answerIndex: 3 },

        { q: 'Which of these is NOT a polygon?', 
          options: ['Circle','Triangle','Square','Hexagon'], answerIndex: 0 },

        { q: 'How many vertices does a triangle have?', 
          options: ['2','3','4','5'], answerIndex: 1 }
      ],

      // Lesson 4: Data & Bar Graphs
      [
        { q: 'On a bar graph, if apples=3, bananas=5, cherries=2, which sold most?', 
          options: ['Apples','Bananas','Cherries','All equal'], answerIndex: 1 },

        { q: 'How many cherries were sold?', 
          options: ['2','3','4','5'], answerIndex: 0 },

        { q: 'If you sold one more apple, how many apples?', 
          options: ['4','3','5','6'], answerIndex: 0 },

        { q: 'Total fruits sold (3+5+2)?', 
          options: ['8','9','10','11'], answerIndex: 2 },

        { q: 'How many more bananas than cherries sold?', 
          options: ['1','2','3','4'], answerIndex: 2 }
      ]
    ]
  },

  English: {
    1: [
      // Lesson 0: Alphabet & Letter Sounds
      [
        { q: 'Which letter comes after C?', 
          options: ['A','B','D','E'], answerIndex: 2 },

        { q: 'Which letter makes the “mmm” sound?', 
          options: ['B','M','N','P'], answerIndex: 1 },

        { q: 'Which of these is a vowel?', 
          options: ['B','C','E','T'], answerIndex: 2 },

        { q: 'What sound does the letter “K” make?', 
          options: ['kuh','sss','mmm','rrr'], answerIndex: 0 },

        { q: 'Which is the uppercase form of “t”?', 
          options: ['T','t','L','l'], answerIndex: 0 }
      ],

      // Lesson 1: Building Sight Word Vocabulary
      [
        { q: 'Which of these is a sight word?', 
          options: ['dog','and','cat','run'], answerIndex: 1 },

        { q: 'Which word is spelled correctly?', 
          options: ['the','teh','eht','th'], answerIndex: 0 },

        { q: 'Which is also a sight word?', 
          options: ['we','me','be','see'], answerIndex: 0 },

        { q: 'Which word means “not in the house”?', 
          options: ['out','in','on','up'], answerIndex: 0 },

        { q: 'Which of these is a sight word?', 
          options: ['have','happy','horse','ham'], answerIndex: 0 }
      ],

      // Lesson 2: Simple Sentence Structure
      [
        { q: 'Which sentence is correct?', 
          options: ['The cat runs.','Cat the runs.','Runs cat the.','Cat runs the.'], answerIndex: 0 },

        { q: 'What is the subject in “The dog barked.”?', 
          options: ['The','dog','barked','.'], answerIndex: 1 },

        { q: 'What is the verb in “She jumps high.”?', 
          options: ['She','jumps','high','.'], answerIndex: 1 },

        { q: 'Which is a complete sentence?', 
          options: ['ran fast','I ran','ran I','fast ran'], answerIndex: 1 },

        { q: 'How many words are in “I like to play”?', 
          options: ['3','4','5','6'], answerIndex: 1 }
      ],

      // Lesson 3: Listening & Speaking Skills
      [
        { q: 'If someone says “Please sit down and listen,” what should you do?', 
          options: ['Sit and listen','Run','Sing','Play'], answerIndex: 0 },

        { q: 'Which is speaking politely?', 
          options: ['Give me that!','Could you please pass that?','Hey you!','Give me now.'], answerIndex: 1 },

        { q: 'If teacher says “Open your book,” what do you open?', 
          options: ['Door','Book','Window','Bag'], answerIndex: 1 },

        { q: 'Which shows you are a good listener?', 
          options: ['Talking while teacher talks','Looking at speaker','Playing','Sleeping'], answerIndex: 1 },

        { q: 'Should you speak in a loud or quiet voice in class?', 
          options: ['Loud','Quiet','Silent','Off'], answerIndex: 1 }
      ],

      // Lesson 4: Rhyming & Word Families
      [
        { q: 'Which word rhymes with “cat”?', 
          options: ['bat','car','dog','pen'], answerIndex: 0 },

        { q: 'Which group shows the –at family?', 
          options: ['cat, bat, rat','dog, log, fog','pen, hen, ten','map, cap, pan'], answerIndex: 0 },

        { q: 'Which word rhymes with “sing”?', 
          options: ['ring','sink','sung','song'], answerIndex: 0 },

        { q: 'Which word ends with –an?', 
          options: ['fan','fun','fin','fen'], answerIndex: 0 },

        { q: 'Which is NOT in the –ig family?', 
          options: ['pig','wig','big','bag'], answerIndex: 3 }
      ]
    ],

    2: [
      // Lesson 0: Reading Fluency & Expression
      [
        { q: 'Which sentence should be read with expression?', 
          options: ['I am so happy!','I am happy.','I am happy,','I am happy?'], answerIndex: 0 },

        { q: 'Which is a question you read with a rising tone?', 
          options: ['What time is it?','It is noon.','I like pie.','Go outside.'], answerIndex: 0 },

        { q: 'What does fluent reading sound like?', 
          options: [
            'Smooth and expressive',
            'Word-by-word slowly',
            'With many pauses',
            'Reading wrong words'
          ], answerIndex: 0 },

        { q: 'Which punctuation mark tells you to pause briefly?', 
          options: ['Comma','Period','Exclamation','Question'], answerIndex: 0 },

        { q: 'Which sentence is shouted in a louder voice?', 
          options: [
            'Wow, that’s amazing!',
            'I like apples.',
            'It is raining.',
            'My name is Tim.'
          ], answerIndex: 0 }
      ],

      // Lesson 1: Expanding Vocabulary
      [
        { q: 'What is a synonym for “happy”?', 
          options: ['sad','joyful','angry','tired'], answerIndex: 1 },

        { q: 'What is an antonym for “big”?', 
          options: ['small','large','tiny','huge'], answerIndex: 0 },

        { q: 'What does “delicious” mean?', 
          options: ['tasty','loud','big','colorful'], answerIndex: 0 },

        { q: 'Which word best completes: “She is very ___ today.”?', 
          options: ['excited','silent','hungry','ancient'], answerIndex: 0 },

        { q: 'Which of these is a compound word?', 
          options: ['toothpaste','table','happy','pillow'], answerIndex: 0 }
      ],

      // Lesson 2: Grammar: Nouns & Verbs
      [
        { q: 'Identify the noun in “The cat slept.”', 
          options: ['The','cat','slept','.'], answerIndex: 1 },

        { q: 'Identify the verb in “He jumps high.”', 
          options: ['He','jumps','high','!'], answerIndex: 1 },

        { q: 'Which word is a noun?', 
          options: ['run','play','park','jump'], answerIndex: 2 },

        { q: 'Which word is a verb?', 
          options: ['apple','banana','sing','chair'], answerIndex: 2 },

        { q: 'In “Birds fly west.”, what part of speech is “birds”?', 
          options: ['Verb','Noun','Adjective','Adverb'], answerIndex: 1 }
      ],

      // Lesson 3: Creative Writing: Short Stories
      [
        { q: 'What is the first part of a story?', 
          options: ['Plot','Beginning','Middle','End'], answerIndex: 1 },

        { q: 'Who are characters in a story?', 
          options: [
            'People or animals in the story',
            'The place of the story',
            'The title of the book',
            'The cover illustration'
          ], answerIndex: 0 },

        { q: 'Where do you describe the setting?', 
          options: ['Start','Middle','End','Never'], answerIndex: 0 },

        { q: 'Which is a good story ending?', 
          options: [
            'They lived happily ever after.',
            'Then they got up.',
            'He walked away.',
            'It was.'
          ], answerIndex: 0 },

        { q: 'Which part of a story tells “what happens”?', 
          options: ['Characters','Plot','Setting','Title'], answerIndex: 1 }
      ],

      // Lesson 4: Reading Comprehension
      [
        { q: 'Who is the main character in “Mia rode her bike to school”?', 
          options: ['Mia','Bike','School','Rode'], answerIndex: 0 },

        { q: 'What did Mia ride?', 
          options: ['Car','Scooter','Bike','Bus'], answerIndex: 2 },

        { q: 'Where did Mia go?', 
          options: ['Park','School','Home','Store'], answerIndex: 1 },

        { q: 'How many words are in “She reads a book”?', 
          options: ['3','4','5','6'], answerIndex: 1 },

        { q: 'What is the verb in “She reads a book”?', 
          options: ['She','reads','a','book'], answerIndex: 1 }
      ]
    ]
  }
};

function getRandomQuote() {
  const idx = Math.floor(Math.random() * motivationalQuotes.length);
  return motivationalQuotes[idx];
}

function showMotivation() {
  const el = document.getElementById('motivation-message');
  if (!el) return;
  el.textContent = getRandomQuote();
}



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
        <button class="accordion-button collapsed" type="button"
                data-bs-toggle="collapse" data-bs-target="#collapse${idx}"
                aria-expanded="false" aria-controls="collapse${idx}">
          ${idx + 1}. ${lesson.theme}
        </button>
      </h2>
      <div id="collapse${idx}" class="accordion-collapse collapse"
           aria-labelledby="heading${idx}" data-bs-parent="#learning-accordion">
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
          <button class="btn btn-success btn-start-quiz"
                  data-lesson-index="${idx}">Start Quiz</button>
        </div>
      </div>
    `;
    accordionContainer.appendChild(item);
  });

  accordionContainer.querySelectorAll('.btn-start-quiz').forEach(btn => {
    btn.addEventListener('click', () => {
      currentLesson = +btn.dataset.lessonIndex;
      currentQIndex = 0;
      startQuiz();
    });
  });
}

// === Theme-Menu Renderer ===
function renderThemeMenu(grade) {
  currentGrade = grade;
  themeMenuHeader.textContent   = `${currentSubject} — Grade ${grade}`;
  themeMenuContainer.innerHTML  = '';

  (topics[currentSubject][grade] || []).forEach((lesson, idx) => {
    const btn = document.createElement('button');
    btn.className           = 'btn btn-outline-primary btn-rounded';
    btn.textContent         = lesson.theme;
    btn.dataset.lessonIndex = idx;
    btn.addEventListener('click', () => {
      currentLesson = idx;
      renderVideoScreen();
    });
    themeMenuContainer.appendChild(btn);
  });
}

// === Video Screen Renderer ===
function renderVideoScreen() {
  const lesson = topics[currentSubject][currentGrade][currentLesson];
  const videoHeader      = document.getElementById('video-header');
  const videoPlaceholder = document.getElementById('video-placeholder');

  // 1) Heading stays the same
  videoHeader.textContent = lesson.theme;

  // 2) Inject description + video
  videoPlaceholder.innerHTML = `
    <p class="theme-description">${lesson.description || ''}</p>
    <div class="video-container mb-3">
      <iframe
        src="https://www.youtube.com/embed/${lesson.videoId}"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
      ></iframe>
    </div>
  `;

  showScreen('video');
}


// === Quiz Logic ===
function startQuiz() {
  // grab this lesson’s questions
  const qList = (quizzes[currentSubject] || {})[currentGrade]?.[currentLesson] || [];
  if (!qList.length) {
    alert('No quiz defined for this lesson yet!');
    return;
  }

  // reset state
  currentQIndex       = 0;
  currentCorrectCount = 0;

  // make sure those buttons are showing again
  submitQuizBtn.style.display = '';
  backQuizBtn  .style.display = '';

  // switch to the quiz screen & show Q1
  showScreen('quiz');
  renderQuizQuestion();
}
const libraryContainer = document.getElementById('library-content');

  // 2) flag so videos/quizzes know we’re in library mode
  let isLibraryFlow = false;

  // 3) wire up the bottom-nav “Library” button
  document
    .querySelector('.bottom-nav .nav-item[data-screen="library"]')
    .addEventListener('click', () => {
      renderLibrary();
      showScreen('library');
    });

  // 4) define renderLibrary at top level here (not inside another handler)
  function renderLibrary() {
  libraryContainer.innerHTML = '';
  isLibraryFlow = true;    // ← turn the flag on

  const subjects = [
    { key: 'Math',    icon: 'fa-calculator',  disabled: false },
    { key: 'English', icon: 'fa-book-open',   disabled: false },
    { key: 'Sepedi',  icon: 'fa-language',    disabled: true  },
    { key: 'Science', icon: 'fa-flask',       disabled: true  },
  ];

  subjects.forEach(s => {
    const card = document.createElement('button');
    card.className = 'book-card';
    card.disabled  = s.disabled;
    card.innerHTML = `
      <i class="fas ${s.icon} book-icon"></i>
      <span class="book-title">${s.key}</span>
      ${s.disabled ? '<span class="book-sub">(Coming Soon)</span>' : ''}
    `;
    card.addEventListener('click', () => {
      if (s.disabled) return;
      currentSubject = s.key;
      subjectTitle.textContent = s.key;
      renderRain(s.key, rainContainerGrade);
      showScreen('grade');    // ← exactly the same call as subject-flow
    });
    libraryContainer.appendChild(card);
  });
}


function renderQuizQuestion() {
  const qList = quizzes[currentSubject][currentGrade][currentLesson];
  const qObj  = qList[currentQIndex];

  // build the card markup
  quizForm.innerHTML = `
    <div class="card quiz-card mb-3">
      <div class="card-body">
        <div class="progress mb-2">
          <div
            class="progress-bar"
            style="width: ${((currentQIndex+1)/qList.length)*100}%"
          ></div>
        </div>
        <h5 class="card-title">
          Question ${currentQIndex+1} of ${qList.length}
        </h5>
        <p class="card-text"><strong>${qObj.q}</strong></p>
        <div class="list-group">
          ${qObj.options.map((opt,i) => `
            <label class="list-group-item list-group-item-action">
              <input
                class="form-check-input me-2"
                type="radio"
                name="quiz-option"
                value="${i}"
              >
              ${opt}
            </label>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  // (optional) trigger fade-in animation:
  const card = quizForm.querySelector('.quiz-card');
  card.classList.remove('active');
  setTimeout(() => card.classList.add('active'), 20);
}


submitQuizBtn.addEventListener('click', () => {
  const sel = quizForm.querySelector('input[name="quiz-option"]:checked');
  if (!sel) return alert('Please select an answer.');
  
  const selected     = +sel.value;
  const correctIndex = quizzes[currentSubject][currentGrade][currentLesson][currentQIndex].answerIndex;
  const isRight      = selected === correctIndex;

  // increment your score if they got it right
  if (isRight) {
    currentCorrectCount++;
    alert('✅ Correct!');
  } else {
    alert('❌ Incorrect.');
  }

  const qList = quizzes[currentSubject][currentGrade][currentLesson];
  if (currentQIndex < qList.length - 1) {
    // move on
    currentQIndex++;
    renderQuizQuestion();
  } else {
    // final question → save the *tally* and render performance
    savePerformance(
      currentSubject,
      currentGrade,
      currentLesson,
      currentCorrectCount,     // ← the learner’s score
      qList.length
    );
    renderPerformance();
    showCompletionCloud();
  }
});



function showCompletionCloud() {
  // hide the old Submit + Back buttons
  submitQuizBtn.style.display = 'none';
  backQuizBtn  .style.display = 'none';

  // render the cloud message with two buttons
  quizForm.innerHTML = `
    <div class="cloud-card">
      <p>☁️ Well done, Quiz Completed! ☁️</p>
      <div class="d-flex justify-content-center gap-3 mt-3">
        <button type="button" id="cloud-module-btn" class="btn btn-outline-primary">
          ← Back to Module
        </button>
        <button type="button" id="cloud-performance-btn" class="btn btn-outline-success">
          View Performance
        </button>
      </div>
    </div>
  `;

  // “Back to Module” handler
  document
    .getElementById('cloud-module-btn')
    .addEventListener('click', () => {
      // restore the quiz buttons
      submitQuizBtn.style.display = '';
      backQuizBtn  .style.display = '';
      showScreen('themeMenu');
    });

  // “View Performance” handler
  document
    .getElementById('cloud-performance-btn')
    .addEventListener('click', () => {
      renderPerformance();       // populate the performance list
      showScreen('performance');
    });
}


function savePerformance(subject, grade, lessonIdx, correct, total) {
  const key = 'performanceData';
  const list = JSON.parse(localStorage.getItem(key) || '[]');
  list.push({
    subject,
    grade,
    lesson: topics[subject][grade][lessonIdx].theme,
    correct,
    total
  });
  localStorage.setItem(key, JSON.stringify(list));
}


backQuizBtn.addEventListener('click', () => showScreen('themeMenu'));

// === Rain Effect ===
function renderRain(subject, container) {
  container.innerHTML = '';
  const icon = subject==='English' ? 'fa-book' : 'fa-calculator';
  for (let i=0; i<25; i++){
    const drop = document.createElement('i');
    drop.className = `fas ${icon} rain-icon`;
    drop.style.left              = `${Math.random()*100}%`;
    drop.style.fontSize          = `${Math.random()*24+16}px`;
    drop.style.animationDuration = `${Math.random()*3+3}s`;
    container.appendChild(drop);
  }
}

// === INIT & NAVIGATION ===

// Login → Home
loginBtn?.addEventListener('click', () => showScreen('home'));
// Logout → Login
loginBtn?.addEventListener('click', () => {
  showMotivation();
  showScreen('home');
});

// Subject → Grade
subjectBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    currentSubject = btn.dataset.subject;
    subjectTitle.textContent = currentSubject;
    showScreen('grade');
    renderRain(currentSubject, rainContainerGrade);
  });
});

// Grade → Theme-Menu
// — Grade → Module (instead of Grade → ThemeMenu) —
// Grade → Module
// when you click a grade, build the lesson menu instead of the accordion:
gradeBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    currentGrade = btn.dataset.grade;

    if (isLibraryFlow) {
      // build the module list exactly as before...
      moduleHeader.textContent      = `${currentSubject} — Grade ${currentGrade}`;
      moduleMenuContainer.innerHTML = '';

      (topics[currentSubject][currentGrade] || []).forEach((lesson, idx) => {
        const lessonBtn = document.createElement('button');
        lessonBtn.type            = 'button';
        lessonBtn.className       = 'btn btn-outline-secondary btn-rounded text-dark';
        lessonBtn.textContent     = lesson.theme;

        lessonBtn.addEventListener('click', () => {
          currentLesson = idx;
          // instead of startQuiz()…
          renderVideoScreen();
          // and the user lands on the video+text screen
        });

        moduleMenuContainer.appendChild(lessonBtn);
      });

      renderRain(currentSubject, rainContainerModule);
      showScreen('module');
      return;
    }

    // ...otherwise fall back to your normal Subject→Module flow
    // (which probably does the same as above but then calls startQuiz())
    //
  });
});




// “Back to subjects” lives on the module screen
backGradeBtn?.addEventListener('click', () => {
  showScreen('themeMenu');
});


// ————— Tab switching logic —————
const perfTabs = document.getElementById('perf-tabs');
perfTabs.querySelectorAll('.nav-link').forEach(tab => {
  tab.addEventListener('click', () => {
    // 1) visually activate
    perfTabs.querySelectorAll('.nav-link')
      .forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    // 2) update globals
    currentSubject = tab.dataset.subject;
    currentGrade   = tab.dataset.grade;

    // 3) re-render chart & list
    renderPerformance();
  });
});

performanceBtn?.addEventListener('click', () => {
  const defaultTab = perfTabs.querySelector('.nav-link.active');
  currentSubject = defaultTab.dataset.subject;
  currentGrade   = defaultTab.dataset.grade;
  renderPerformance();
  showScreen('performance');
});



function renderPerformanceBarChart() {
  // 1) pull & filter the data
  const raw = JSON.parse(localStorage.getItem('performanceData') || '[]');
  const data = raw.filter(e =>
    e.subject === currentSubject &&
    String(e.grade) === String(currentGrade)
  );

  // 2) get your themes in order
  const themes = topics[currentSubject][currentGrade].map(l => l.theme);

  // 3) compute average % correct per theme
  const averages = themes.map(theme => {
    const entries = data.filter(d => d.lesson === theme);
    if (!entries.length) return 0;
    const totalPct = entries.reduce((sum, e) =>
      sum + (e.correct / e.total) * 100
    , 0);
    return Math.round(totalPct / entries.length);
  });

  // 4) chart.js setup
  const ctx = document.getElementById('performance-bar-chart').getContext('2d');
  const config = {
    type: 'bar',
    data: {
      labels: themes,
      datasets: [{
        label: '% Correct',
        data: averages,
        backgroundColor: themes.map((_, i) =>
          // you can reuse your line‐chart palette
          ['rgba(44,123,229,0.8)',
           'rgba(247,185,36,0.8)',
           'rgba(0,200,80,0.8)',
           'rgba(200,0,200,0.8)',
           'rgba(0,150,150,0.8)'][i % 5]
        )
      }]
    },
    options: {
      indexAxis: 'y',           // horizontal bars (optional)
      scales: {
        x: {
          beginAtZero: true,
          max: 100
        }
      },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: `${currentSubject} • Grade ${currentGrade} — by Theme`
        }
      }
    }
  };

  if (perfBarChart) {
    perfBarChart.data.labels   = config.data.labels;
    perfBarChart.data.datasets = config.data.datasets;
    perfBarChart.options.plugins.title.text = config.options.plugins.title.text;
    perfBarChart.update();
  } else {
    perfBarChart = new Chart(ctx, config);
  }
}

function renderPerformance() {
  const perfList = document.getElementById('performance-list');
  perfList.innerHTML = '';   // clear old entries
  renderPerformanceChart();
  renderPerformanceBarChart();

  // get & filter stored data
  const allData = JSON.parse(localStorage.getItem('performanceData') || '[]');
  const data = allData
    .filter(e => e.subject === currentSubject && +e.grade === +currentGrade)
    .reverse();

  // build one .lesson per entry
  data.forEach(entry => {
    const item = document.createElement('div');
    item.className = 'lesson';
    item.innerHTML = `
      <span class="title">
        ${entry.subject} · Grade ${entry.grade}
      </span>
      <span class="score">
        ${entry.lesson}: ${entry.correct}/${entry.total} correct
      </span>
    `;
    perfList.appendChild(item);
  });
}


function renderPerformanceChart() {
  // 1) fetch & filter only this subject+grade
  const raw = JSON.parse(localStorage.getItem('performanceData') || '[]');
  const data = raw.filter(e =>
    e.subject === currentSubject &&
    String(e.grade) === String(currentGrade)
  );

  // 2) pull your themes in order
  const themes = topics[currentSubject][currentGrade].map(l => l.theme);

  // 3) figure out how many attempts we have total
  const counts = themes.map(theme =>
    data.filter(entry => entry.lesson === theme).length
  );
  const attemptCount = Math.max(...counts, 0);
  const labels = Array.from({ length: attemptCount }, (_, i) => `Attempt ${i + 1}`);

  // 4) build one dataset per theme, with bigger markers
  const palette = [
    'rgba( 44,123,229,0.8)',
    'rgba(247,185,36,0.8)',
    'rgba(  0,200, 80,0.8)',
    'rgba(200,  0,200,0.8)',
    'rgba(  0,150,150,0.8)'
  ];
  const datasets = themes.map((theme, idx) => {
    const themeData = Array.from({ length: attemptCount }, (_, ai) => {
      const e = data.filter(d => d.lesson === theme)[ai];
      if (!e) return null;
      const pct = Math.round((e.correct / e.total) * 100);
      return Math.min(100, Math.max(0, pct));
    });

    return {
      label: theme,
      data: themeData,
      borderColor: palette[idx % palette.length],
      backgroundColor: palette[idx % palette.length],
      fill: false,
      spanGaps: true,
      pointRadius: 6,       // larger dot
      pointHoverRadius: 8,  // hover highlight
      tension: 0.3          // slight curve
    };
  });

  // 5) Chart.js config with top padding (“grace”)
  const ctx = document.getElementById('performance-chart').getContext('2d');
  const config = {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' },
        title: {
          display: true,
          text: `${currentSubject} • Grade ${currentGrade}`
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: 100,  // keep 100 as target
          grace: '5%',        // add 5% padding above the top value
          title: { display: true, text: '% Correct' }
        }
      }
    }
  };

  // 6) create or update the chart
  if (perfChart) {
    perfChart.options = config.options;
    perfChart.data    = config.data;
    perfChart.update();
  } else {
    perfChart = new Chart(ctx, config);
  }
}





// Proceed to Quiz
proceedQuizBtn.addEventListener('click', () => {
  currentQIndex = 0;
  startQuiz();
});

// Back from Video → Theme-Menu
document.getElementById('back-to-theme-btn')
  .addEventListener('click', () => showScreen('themeMenu'));

// Back to Home
backHomeBtns.forEach(b => b?.addEventListener('click', () => showScreen('home')));
// Back to Grade
backGradeBtn?.addEventListener('click', () => showScreen('grade'));
// Back to Module
backModuleBtn?.addEventListener('click', () => showScreen('themeMenu'));
// Theme-Menu → Grade
backToGradeBtn?.addEventListener('click', () => showScreen('grade'));
// 1) Hide the spinner overlay
spinner.style.display = 'none';

// 2) Show the initial screen (hash or fallback to 'login')
const initial = window.location.hash.slice(1) || 'login';
showScreen(initial, true);

document
  .getElementById('export-pdf-btn')
  .addEventListener('click', () => {
    // 1) Clone the performance card so we can tear it down/modify for PDF
    console.log('✅ export-pdf-btn clicked!', { html2pdf });
    const perfCard = document.querySelector('#performance-screen .screen-card');
    const clone    = perfCard.cloneNode(true);

    // 2) Remove nav & back-button (we don’t want those in the PDF)
    clone.querySelector('.bottom-nav')?.remove();
    clone.querySelector('#back-home-btn2')?.remove();

    // 3) Give each chart canvas a bottom margin
    clone.querySelectorAll('canvas').forEach(c => {
      c.style.display      = 'block';
      c.style.marginBottom = '20px';
    });

    // 4) Build a plain HTML table of raw scores
    const data = JSON.parse(localStorage.getItem('performanceData') || '[]');
    const table = document.createElement('table');
    table.style.width           = '100%';
    table.style.borderCollapse  = 'collapse';
    table.style.marginTop       = '20px';

    // header row
    const thead  = table.createTHead();
    const hrow   = thead.insertRow();
    ['Subject','Grade','Lesson','Correct','Total'].forEach(txt => {
      const th = document.createElement('th');
      th.textContent   = txt;
      th.style.border  = '1px solid #ddd';
      th.style.padding = '8px';
      th.style.background = '#f2f2f2';
      th.style.textAlign  = 'left';
      hrow.appendChild(th);
    });

    // data rows
    const tbody = table.createTBody();
    data.forEach(({subject,grade,lesson,correct,total}) => {
      const row = tbody.insertRow();
      [subject, grade, lesson, correct, total].forEach(val => {
        const td = row.insertCell();
        td.textContent   = val;
        td.style.border  = '1px solid #ddd';
        td.style.padding = '8px';
      });
    });

    clone.appendChild(table);

    // 5) Wrap in a white background + padding so html2pdf can snapshot
    const wrapper = document.createElement('div');
    wrapper.style.background = '#fff';
    wrapper.style.padding    = '20px';
    wrapper.appendChild(clone);
    document.body.appendChild(wrapper);

    // 6) Fire html2pdf
    html2pdf()
      .set({
        margin:       [10,10,10,10],
        filename:     'performance-report.pdf',
        html2canvas:  { scale: 2, logging: false, useCORS: true },
        jsPDF:        { unit: 'pt', format: 'a4', orientation: 'portrait' }
      })
      .from(wrapper)
      .save()
      .then(() => {
        // clean up our temporary DOM
        document.body.removeChild(wrapper);
      });
  });





})
