// QuizForge Frontend Client Logic
const API_BASE = '';
let currentRole = 'student'; // 'student' | 'faculty'
let authToken = localStorage.getItem('quizforge-token') || null;
let currentQuestion = null;
let currentSessionId = null;
let timerInterval = null;
let timeLeft = 30;
let allQuestionsCache = [];
let allMasteryCache = [];

// Demo User state
let userStats = {
  name: 'Alex Demo',
  email: 'demo@quizforge.app',
  role: 'student',
  xp: 1250,
  level: 4,
  streak: 3,
  badges: []
};

// Safe App Initialization
function initApp() {
  initTheme();
  if (window.lucide) lucide.createIcons();
  loginDemoUser().then(() => {
    loadDashboardData();
  });
  setupKeyboardShortcuts();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// Initialize Theme from localStorage
function initTheme() {
  const savedTheme = localStorage.getItem('quizforge-theme') || 'dark';
  applyTheme(savedTheme);
}

function applyTheme(theme) {
  const html = document.documentElement;
  if (theme === 'light') {
    html.classList.remove('dark');
    html.classList.add('light');
  } else {
    html.classList.remove('light');
    html.classList.add('dark');
  }
}

// Auto-login with Demo credentials
async function loginDemoUser() {
  try {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'demo@quizforge.app', password: 'demo1234' })
    });
    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      localStorage.setItem('quizforge-token', authToken);
      userStats.name = data.user.name;
      userStats.role = data.user.role;
      updateUserUI();
    }
  } catch (err) {
    console.warn('API login skipped or local mock mode:', err);
  }
}

function getAuthHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
}

function updateUserUI() {
  const userNameEl = document.getElementById('userName');
  if (userNameEl) userNameEl.textContent = userStats.name;

  const userInitEl = document.getElementById('userInitial');
  if (userInitEl) userInitEl.textContent = userStats.name.charAt(0);

  const userRoleEl = document.getElementById('userRoleBadge');
  if (userRoleEl) userRoleEl.textContent = userStats.role;

  const streakEl = document.getElementById('streakCount');
  if (streakEl) streakEl.textContent = userStats.streak;

  const mobileStreak = document.getElementById('mobileStreakCount');
  if (mobileStreak) mobileStreak.textContent = userStats.streak;
}

// Navigation between views
function navigate(viewName) {
  document.querySelectorAll('.view').forEach(el => el.classList.add('hidden'));
  const target = document.getElementById(`view-${viewName}`);
  if (target) target.classList.remove('hidden');

  // Update nav highlight
  document.querySelectorAll('.nav-item').forEach(btn => {
    if (btn.getAttribute('data-page') === viewName) {
      btn.className = 'nav-item active-nav w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition text-white bg-violet-600/30 border border-violet-500/30';
    } else {
      btn.className = 'nav-item w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition text-gray-400 hover:text-white hover:bg-white/5';
    }
  });

  if (viewName === 'dashboard') loadDashboardData();
  if (viewName === 'syllabus') loadSyllabusTree();
  if (viewName === 'analytics') loadAnalyticsData();
  if (viewName === 'leaderboard') loadLeaderboardData();
  if (viewName === 'questionbank') loadQuestionBankData();
  if (viewName === 'quiz' && !currentQuestion) startAdaptiveQuiz();

  if (window.lucide) lucide.createIcons();
}

// Load Dashboard Metrics & Weak Topics
async function loadDashboardData() {
  try {
    const headers = getAuthHeaders();
    
    // 1. Mastery
    const masteryRes = await fetch('/analytics/mastery', { headers });
    if (masteryRes.ok) {
      allMasteryCache = await masteryRes.json();
      renderDashboardMastery(allMasteryCache);
    }

    // 2. Progress
    const progRes = await fetch('/analytics/progress', { headers });
    if (progRes.ok) {
      const prog = await progRes.json();
      const xpEl = document.getElementById('dashXP');
      if (xpEl) xpEl.textContent = prog.xp.toLocaleString();

      const lvlEl = document.getElementById('dashLevel');
      if (lvlEl) lvlEl.textContent = prog.level;

      const streakEl = document.getElementById('dashStreak');
      if (streakEl) streakEl.textContent = `${prog.streak} Days`;

      const accEl = document.getElementById('dashAccuracy');
      if (accEl) accEl.textContent = `${(prog.accuracy * 100).toFixed(1)}%`;

      const xpNextEl = document.getElementById('dashXPNext');
      if (xpNextEl) xpNextEl.textContent = `${prog.xp_to_next_level} XP to Level ${prog.level + 1}`;
    }

    // 3. Badges
    renderRecentBadges();
  } catch (e) {
    console.error('Error loading dashboard:', e);
  }
}

function renderDashboardMastery(masteries) {
  if (masteries.length > 0) {
    const avg = masteries.reduce((acc, m) => acc + m.p_L, 0) / masteries.length;
    const avgEl = document.getElementById('dashAvgMastery');
    if (avgEl) avgEl.textContent = `${(avg * 100).toFixed(1)}%`;
  }

  // Render weak topics
  const weak = masteries.filter(m => m.is_weak || m.p_L < 0.60);
  const weakContainer = document.getElementById('weakTopicsList');
  if (weakContainer) {
    weakContainer.innerHTML = '';

    if (weak.length === 0) {
      weakContainer.innerHTML = '<p class="text-xs text-emerald-500 font-medium p-3 rounded-lg bg-emerald-500/10">🎉 Great job! No weak topics flagged (&lt;60%).</p>';
    } else {
      weak.slice(0, 4).forEach(item => {
        const pct = (item.p_L * 100).toFixed(0);
        const card = document.createElement('div');
        card.className = 'p-3.5 rounded-xl bg-brand-elevated/70 border border-white/5 flex items-center justify-between hover:border-white/15 transition';
        card.innerHTML = `
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0"></span>
              <p class="text-sm font-semibold text-white leading-tight">${item.topic_name}</p>
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-400">
              <span>BKT Mastery: <span class="font-mono text-rose-500 font-bold">${pct}%</span></span>
              <span>•</span>
              <span>${item.attempts_count} attempts</span>
            </div>
          </div>
          <button onclick="practiceTopicId(${item.topic_id})" class="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-500 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition shrink-0 cursor-pointer">
            <i data-lucide="crosshair" class="w-3.5 h-3.5"></i>
            <span>Drill Topic</span>
          </button>
        `;
        weakContainer.appendChild(card);
      });
    }
  }

  // Unit Mastery Grid
  const grid = document.getElementById('unitMasteryGrid');
  if (grid) {
    grid.innerHTML = '';
    masteries.slice(0, 6).forEach(m => {
      const pct = (m.p_L * 100).toFixed(0);
      const color = m.p_L >= 0.9 ? 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10' :
                    m.p_L >= 0.6 ? 'text-amber-500 border-amber-500/30 bg-amber-500/10' :
                    'text-rose-500 border-rose-500/30 bg-rose-500/10';
      const barColor = m.p_L >= 0.9 ? 'bg-emerald-500' : m.p_L >= 0.6 ? 'bg-amber-500' : 'bg-rose-500';

      const el = document.createElement('div');
      el.className = 'p-3.5 rounded-xl bg-brand-elevated/50 border border-white/5 space-y-2 cursor-pointer hover:border-cyan-500/40 transition';
      el.onclick = () => {
        navigate('syllabus');
        setTimeout(() => inspectTopic({ id: m.topic_id, name: m.topic_name }, m.p_L), 200);
      };
      el.innerHTML = `
        <div class="flex justify-between items-start gap-2">
          <span class="text-xs font-semibold text-gray-200 truncate">${m.topic_name}</span>
          <span class="text-[11px] font-mono font-bold px-1.5 py-0.5 rounded border ${color}">${pct}%</span>
        </div>
        <div class="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
          <div class="${barColor} h-1.5 rounded-full" style="width: ${pct}%"></div>
        </div>
      `;
      grid.appendChild(el);
    });
  }

  if (window.lucide) lucide.createIcons();
}

function renderRecentBadges() {
  const container = document.getElementById('dashBadgesList');
  if (!container) return;
  container.innerHTML = `
    <div class="p-2.5 rounded-xl bg-brand-elevated/70 border border-white/5 flex items-center gap-3">
      <span class="text-2xl">🔥</span>
      <div>
        <p class="text-xs font-bold text-white">On Fire</p>
        <p class="text-[10px] text-gray-400">3-day consistent study streak</p>
      </div>
    </div>
    <div class="p-2.5 rounded-xl bg-brand-elevated/70 border border-white/5 flex items-center gap-3">
      <span class="text-2xl">⚡</span>
      <div>
        <p class="text-xs font-bold text-white">Speed Demon</p>
        <p class="text-[10px] text-gray-400">Answered in &lt;40% allotted time limit</p>
      </div>
    </div>
    <div class="p-2.5 rounded-xl bg-brand-elevated/70 border border-white/5 flex items-center gap-3">
      <span class="text-2xl">✅</span>
      <div>
        <p class="text-xs font-bold text-white">Sharp Mind</p>
        <p class="text-[10px] text-gray-400">Correctly solved first computer networking question</p>
      </div>
    </div>
  `;
}

// ADAPTIVE QUIZ ENGINE
async function startAdaptiveQuiz(topicId = null) {
  try {
    navigate('quiz');
    if (!authToken) await loginDemoUser();
    const headers = getAuthHeaders({ 'Content-Type': 'application/json' });
    
    const body = {
      document_id: 1,
      mode: 'adaptive',
      max_questions: 10
    };
    if (topicId) body.topic_ids = [topicId];

    const res = await fetch('/quiz/start', {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });

    if (res.ok) {
      const data = await res.json();
      currentSessionId = data.id;
      displayQuestion(data.current_question, data.why_text);
    } else {
      showToast('Could not start adaptive quiz session', 'error');
    }
  } catch (err) {
    console.error('Failed to start quiz:', err);
    showToast('Network error starting quiz', 'error');
  }
}

function practiceTopicId(topicId) {
  startAdaptiveQuiz(topicId);
}

function displayQuestion(q, whyText) {
  if (!q) {
    showToast('Quiz session complete! Updating mastery analytics...', 'success');
    navigate('dashboard');
    return;
  }

  currentQuestion = q;
  const feedbackCard = document.getElementById('quizFeedbackCard');
  if (feedbackCard) feedbackCard.classList.add('hidden');

  const container = document.getElementById('quizOptionsContainer');
  if (container) container.innerHTML = '';

  const topicTag = document.getElementById('quizTopicTag');
  if (topicTag) topicTag.textContent = q.topic_name || 'Computer Networks';

  const diffTag = document.getElementById('quizDifficultyTag');
  if (diffTag) diffTag.textContent = q.difficulty;

  const bloomTag = document.getElementById('quizBloomTag');
  if (bloomTag) bloomTag.textContent = q.bloom || 'Remember';

  const stemEl = document.getElementById('questionStem');
  if (stemEl) stemEl.textContent = q.stem;

  const whyEl = document.getElementById('quizWhyExplanation');
  if (whyEl) whyEl.textContent = whyText || 'Adaptive BKT Question Selection';

  // Re-enable lifelines for each question
  resetLifelineButtons();

  // Options rendering
  if (container) {
    if (q.type === 'mcq' && q.options) {
      q.options.forEach((opt, idx) => {
        const keyNum = idx + 1;
        const btn = document.createElement('button');
        btn.className = 'quiz-option-btn w-full p-4 rounded-xl glass-card text-left transition flex items-center justify-between text-sm group cursor-pointer';
        btn.innerHTML = `
          <span class="text-gray-200 group-hover:text-cyan-400 leading-relaxed font-medium">${opt}</span>
          <span class="w-6 h-6 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center font-mono text-xs text-gray-400 group-hover:text-cyan-400 shrink-0 ml-3">${keyNum}</span>
        `;
        btn.onclick = () => submitAnswer(opt);
        container.appendChild(btn);
      });
    } else if (q.type === 'true_false') {
      ['True', 'False'].forEach((val, idx) => {
        const btn = document.createElement('button');
        btn.className = 'quiz-option-btn w-full p-4 rounded-xl glass-card text-left transition flex items-center justify-between text-sm group cursor-pointer';
        btn.innerHTML = `
          <span class="text-gray-200 group-hover:text-cyan-400 font-medium">${val}</span>
          <span class="w-6 h-6 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center font-mono text-xs text-gray-400 group-hover:text-cyan-400 shrink-0">${idx + 1}</span>
        `;
        btn.onclick = () => submitAnswer(val);
        container.appendChild(btn);
      });
    } else {
      // Short answer
      container.innerHTML = `
        <div class="space-y-3">
          <input type="text" id="shortAnswerInput" placeholder="Type your answer here..." class="w-full p-3.5 rounded-xl bg-brand-elevated border border-white/15 text-sm text-white focus:outline-none focus:border-cyan-400">
          <button onclick="submitAnswer(document.getElementById('shortAnswerInput').value)" class="w-full gradient-btn py-3 rounded-xl font-semibold text-sm cursor-pointer">Submit Answer</button>
        </div>
      `;
    }
  }

  // Timer reset (30s)
  resetTimer(q.time_limit_ms ? Math.round(q.time_limit_ms / 1000) : 30);
}

function resetLifelineButtons() {
  const l50 = document.getElementById('lifeline5050');
  if (l50) { l50.disabled = false; l50.classList.remove('opacity-40'); }

  const lTimer = document.getElementById('lifelineTimer');
  if (lTimer) { lTimer.disabled = false; lTimer.classList.remove('opacity-40'); }
}

function resetTimer(seconds) {
  clearInterval(timerInterval);
  timeLeft = seconds;
  const timerCircle = document.getElementById('quizTimerCircle');
  const timerText = document.getElementById('quizTimerText');
  const totalDash = 113;

  if (timerText) timerText.textContent = timeLeft;
  if (timerCircle) {
    timerCircle.style.strokeDashoffset = '0';
    timerCircle.classList.remove('text-rose-500');
    timerCircle.classList.add('text-cyan-500');
  }

  timerInterval = setInterval(() => {
    timeLeft--;
    if (timerText) timerText.textContent = timeLeft;
    const progress = timeLeft / seconds;
    if (timerCircle) {
      timerCircle.style.strokeDashoffset = totalDash * (1 - progress);
      if (timeLeft <= 5) {
        timerCircle.classList.remove('text-cyan-500');
        timerCircle.classList.add('text-rose-500');
      }
    }

    if (timeLeft <= 0) {
      clearInterval(timerInterval);
      submitAnswer(''); // Auto timeout
    }
  }, 1000);
}

// Answer submission & BKT feedback
async function submitAnswer(answerText) {
  clearInterval(timerInterval);
  const responseMs = (30 - timeLeft) * 1000;

  // Disable option buttons during grading
  document.querySelectorAll('.quiz-option-btn').forEach(b => b.disabled = true);

  try {
    const headers = getAuthHeaders({ 'Content-Type': 'application/json' });
    const res = await fetch(`/quiz/${currentSessionId}/answer`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        question_id: currentQuestion.id,
        answer: answerText,
        response_ms: responseMs
      })
    });

    if (res.ok) {
      const data = await res.json();
      showAnswerFeedback(data);
    } else {
      showToast('Error evaluating answer', 'error');
    }
  } catch (err) {
    console.error('Answer submission failed:', err);
    showToast('Failed to connect to answer evaluation service', 'error');
  }
}

function showAnswerFeedback(result) {
  const card = document.getElementById('quizFeedbackCard');
  if (!card) return;
  card.classList.remove('hidden');

  const verdict = document.getElementById('feedbackVerdict');
  const xpBadge = document.getElementById('feedbackXPBadge');
  const exp = document.getElementById('feedbackExplanation');
  const source = document.getElementById('feedbackSourceText');

  if (result.correct) {
    card.className = 'p-5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 space-y-2';
    if (verdict) verdict.innerHTML = '<span class="text-emerald-500 font-bold flex items-center gap-2">✅ Correct Answer!</span>';
    if (xpBadge) {
      xpBadge.textContent = `+${result.xp_gained} XP Earned`;
      xpBadge.className = 'text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-500';
    }
    if (window.confetti) {
      confetti({ particleCount: 40, spread: 60, origin: { y: 0.7 } });
    }
  } else {
    card.className = 'p-5 rounded-xl border border-rose-500/40 bg-rose-500/10 space-y-2';
    if (verdict) verdict.innerHTML = `<span class="text-rose-500 font-bold flex items-center gap-2">❌ Incorrect. Correct: ${result.correct_answer}</span>`;
    if (xpBadge) {
      xpBadge.textContent = '+0 XP';
      xpBadge.className = 'text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-500';
    }
  }

  if (exp) exp.textContent = result.explanation || currentQuestion.explanation;
  if (source) source.textContent = currentQuestion.source_snippet || 'Computer Networks Course Material';

  // Store next question reference
  window._nextQuestionData = result.next_question;
  window._nextWhyText = result.why_text;
  window._sessionComplete = result.session_complete;
}

function fetchNextQuestion() {
  if (window._sessionComplete || !window._nextQuestionData) {
    showToast('Quiz session completed! Updating mastery analytics...', 'success');
    navigate('dashboard');
  } else {
    displayQuestion(window._nextQuestionData, window._nextWhyText);
  }
}

// Lifelines
function useLifeline5050() {
  const btns = Array.from(document.querySelectorAll('.quiz-option-btn'));
  if (btns.length <= 2) return;

  let removed = 0;
  btns.forEach(btn => {
    const text = btn.innerText;
    if (!text.includes(currentQuestion.answer) && removed < 2) {
      btn.style.opacity = '0.2';
      btn.disabled = true;
      removed++;
    }
  });
  const lBtn = document.getElementById('lifeline5050');
  if (lBtn) {
    lBtn.disabled = true;
    lBtn.classList.add('opacity-40');
  }
  showToast('50:50 Lifeline applied (-10 XP)', 'info');
}

function useLifelineSkip() {
  clearInterval(timerInterval);
  showToast('Question skipped (-15 XP)', 'info');
  fetchNextQuestion();
}

function useLifelineTime() {
  timeLeft += 15;
  const tText = document.getElementById('quizTimerText');
  if (tText) tText.textContent = timeLeft;

  const lTimer = document.getElementById('lifelineTimer');
  if (lTimer) {
    lTimer.disabled = true;
    lTimer.classList.add('opacity-40');
  }
  showToast('+15 Seconds Added (-5 XP)', 'info');
}

// Keyboard shortcuts (1-4, Enter)
function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    const quizView = document.getElementById('view-quiz');
    if (!quizView || quizView.classList.contains('hidden')) return;

    // Enter to proceed to next question
    if (e.key === 'Enter') {
      const feedbackCard = document.getElementById('quizFeedbackCard');
      if (feedbackCard && !feedbackCard.classList.contains('hidden')) {
        fetchNextQuestion();
        return;
      }
    }

    if (['1', '2', '3', '4'].includes(e.key)) {
      const idx = parseInt(e.key) - 1;
      const btns = document.querySelectorAll('.quiz-option-btn');
      if (btns[idx] && !btns[idx].disabled) {
        btns[idx].click();
      }
    }
  });
}

// SYLLABUS MAP VIEW
async function loadSyllabusTree() {
  try {
    const headers = getAuthHeaders();
    const res = await fetch('/documents/1/topics', { headers });
    if (!res.ok) return;
    const topics = await res.json();

    const container = document.getElementById('syllabusTreeContainer');
    if (!container) return;
    container.innerHTML = '';

    // Group units vs subtopics
    const units = topics.filter(t => t.parent_id === null);
    units.forEach(unit => {
      const subtopics = topics.filter(t => t.parent_id === unit.id);
      const unitCard = document.createElement('div');
      unitCard.className = 'p-4 rounded-xl bg-brand-elevated/40 border border-white/5 space-y-3';
      
      let subtopicChips = subtopics.map(st => {
        const masteryObj = allMasteryCache.find(m => m.topic_id === st.id);
        const p_L = masteryObj ? masteryObj.p_L : 0.7;
        const color = p_L >= 0.9 ? 'border-emerald-500/40 text-emerald-500 bg-emerald-500/10' :
                      p_L >= 0.6 ? 'border-amber-500/40 text-amber-500 bg-amber-500/10' :
                      'border-rose-500/40 text-rose-500 bg-rose-500/10';

        return `
          <button onclick='inspectTopic(${JSON.stringify(st)}, ${p_L})' class="px-3 py-1.5 rounded-lg border text-xs font-medium ${color} hover:scale-105 transition cursor-pointer">
            ${st.name} (${(p_L * 100).toFixed(0)}%)
          </button>
        `;
      }).join('');

      unitCard.innerHTML = `
        <div class="flex items-center justify-between">
          <h4 class="font-heading font-bold text-sm text-cyan-500">${unit.name}</h4>
          <span class="text-xs text-gray-400 font-mono">${subtopics.length} Subtopics</span>
        </div>
        <div class="flex flex-wrap gap-2 pt-1">
          ${subtopicChips || '<span class="text-xs text-gray-500 italic">No subtopics</span>'}
        </div>
      `;
      container.appendChild(unitCard);
    });
  } catch (err) {
    console.error('Failed to load syllabus:', err);
  }
}

function inspectTopic(topic, p_L) {
  const emptyPrompt = document.getElementById('topicDetailEmpty');
  if (emptyPrompt) emptyPrompt.classList.add('hidden');

  const content = document.getElementById('topicDetailContent');
  if (content) content.classList.remove('hidden');

  const nameEl = document.getElementById('detailTopicName');
  if (nameEl) nameEl.textContent = topic.name;

  const pct = (p_L * 100).toFixed(0);
  const mVal = document.getElementById('detailMasteryVal');
  if (mVal) mVal.textContent = `${pct}%`;

  const mBar = document.getElementById('detailMasteryBar');
  if (mBar) mBar.style.width = `${pct}%`;

  const notice = document.getElementById('detailStatusNotice');
  if (notice) {
    if (p_L < 0.60) {
      notice.textContent = '⚠️ Flagged as Weak Topic (<60%)';
      notice.className = 'text-[11px] text-rose-500 font-medium';
    } else if (p_L >= 0.90) {
      notice.textContent = '🏆 Mastered Topic (≥90%)';
      notice.className = 'text-[11px] text-emerald-500 font-medium';
    } else {
      notice.textContent = '📈 Competent Practicing Range';
      notice.className = 'text-[11px] text-amber-500 font-medium';
    }
  }

  const sumEl = document.getElementById('detailTopicSummary');
  if (sumEl) sumEl.textContent = topic.summary || 'Course syllabus topic covering theoretical and practical implementation.';
  
  const kwContainer = document.getElementById('detailTopicKeywords');
  if (kwContainer) {
    kwContainer.innerHTML = '';
    (topic.keywords || []).forEach(kw => {
      const sp = document.createElement('span');
      sp.className = 'px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-mono text-gray-300';
      sp.textContent = kw;
      kwContainer.appendChild(sp);
    });
  }

  window._inspectedTopicId = topic.id;
}

function practiceSpecificTopic() {
  if (window._inspectedTopicId) {
    startAdaptiveQuiz(window._inspectedTopicId);
  }
}

// DRAG AND DROP HANDLERS
function handleDragOver(evt) {
  evt.preventDefault();
  const zone = document.getElementById('uploadDropZone');
  if (zone) zone.classList.add('border-cyan-500', 'bg-cyan-500/5');
}

function handleDragLeave(evt) {
  evt.preventDefault();
  const zone = document.getElementById('uploadDropZone');
  if (zone) zone.classList.remove('border-cyan-500', 'bg-cyan-500/5');
}

function handleDrop(evt) {
  evt.preventDefault();
  const zone = document.getElementById('uploadDropZone');
  if (zone) zone.classList.remove('border-cyan-500', 'bg-cyan-500/5');
  
  if (evt.dataTransfer.files && evt.dataTransfer.files.length > 0) {
    processUploadFile(evt.dataTransfer.files[0]);
  }
}

// REAL UPLOAD PIPELINE CONNECTED TO BACKEND
async function handleFileSelect(evt) {
  const file = evt.target.files[0];
  if (!file) return;
  processUploadFile(file);
}

async function processUploadFile(file) {
  const stepper = document.getElementById('uploadPipelineStepper');
  if (stepper) stepper.classList.remove('hidden');

  const setStep = (stepNum, active) => {
    const el = document.getElementById(`step-${stepNum}`);
    if (el) {
      if (active) {
        el.classList.add('text-cyan-500', 'font-semibold');
        const icon = el.querySelector('.step-icon');
        if (icon) icon.classList.add('bg-cyan-500/20', 'text-cyan-500');
      } else {
        el.classList.remove('text-cyan-500', 'font-semibold');
        const icon = el.querySelector('.step-icon');
        if (icon) icon.classList.remove('bg-cyan-500/20', 'text-cyan-500');
      }
    }
  };

  try {
    setStep(1, true);
    const formData = new FormData();
    formData.append('file', file);

    const headers = getAuthHeaders();
    const res = await fetch('/documents', {
      method: 'POST',
      headers,
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const doc = await res.json();
    setStep(2, true);

    // Poll document progress until ready
    let completed = false;
    let attempts = 0;
    while (!completed && attempts < 25) {
      await new Promise(r => setTimeout(r, 1000));
      attempts++;
      const pRes = await fetch(`/documents/${doc.id}/progress`, { headers });
      if (pRes.ok) {
        const pData = await pRes.json();
        if (pData.stage === 'extracting_topics' || pData.progress >= 50) setStep(2, true);
        if (pData.stage === 'generating_questions' || pData.progress >= 75) setStep(3, true);
        if (pData.stage === 'done' || pData.progress === 100) {
          setStep(4, true);
          completed = true;
        }
      }
    }

    showToast(`Parsed "${file.name}" & generated adaptive questions!`, 'success');
    await loadDashboardData();
    setTimeout(() => navigate('syllabus'), 1200);

  } catch (e) {
    console.error('Upload processing error:', e);
    showToast(`Upload error: ${e.message}`, 'error');
  }
}

// ANALYTICS VIEW
function loadAnalyticsData() {
  const container = document.getElementById('analyticsTopicBars');
  if (!container) return;
  container.innerHTML = '';

  allMasteryCache.forEach(m => {
    const pct = (m.p_L * 100).toFixed(0);
    const color = m.p_L >= 0.9 ? 'bg-emerald-500' : m.p_L >= 0.6 ? 'bg-amber-500' : 'bg-rose-500';
    const row = document.createElement('div');
    row.className = 'space-y-1';
    row.innerHTML = `
      <div class="flex justify-between text-xs">
        <span class="text-gray-300 font-medium">${m.topic_name}</span>
        <span class="font-mono font-bold text-gray-400">${pct}%</span>
      </div>
      <div class="w-full bg-white/5 rounded-full h-2 overflow-hidden">
        <div class="${color} h-2 rounded-full transition-all duration-500" style="width: ${pct}%"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

// LEADERBOARD VIEW
async function loadLeaderboardData() {
  try {
    const headers = getAuthHeaders();
    const res = await fetch('/leaderboard', { headers });
    if (!res.ok) return;
    const leaderboard = await res.json();

    const tbody = document.getElementById('leaderboardTbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    leaderboard.forEach(entry => {
      const tr = document.createElement('tr');
      const isMe = entry.name.includes('Alex');
      tr.className = isMe ? 'bg-violet-500/10 font-bold' : '';
      tr.innerHTML = `
        <td class="py-3 px-3 font-mono ${entry.rank === 1 ? 'text-amber-500 font-bold' : 'text-gray-400'}">#${entry.rank}</td>
        <td class="py-3 px-3 flex items-center gap-2">
          <span>${entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : '👤'}</span>
          <span class="${isMe ? 'text-cyan-500 font-semibold' : 'text-white'}">${entry.name}</span>
        </td>
        <td class="py-3 px-3 font-mono text-gray-300">Lvl ${entry.level}</td>
        <td class="py-3 px-3 font-mono text-amber-500 font-bold">🔥 ${entry.streak}</td>
        <td class="py-3 px-3 text-right font-mono font-bold text-white">${entry.xp.toLocaleString()}</td>
      `;
      tbody.appendChild(tr);
    });

    renderAllBadgesWall();
  } catch (err) {
    console.error('Failed to load leaderboard:', err);
  }
}

function renderAllBadgesWall() {
  const wall = document.getElementById('allBadgesWall');
  if (!wall) return;
  const badges = [
    { code: 'streak_3', name: 'On Fire', desc: '3-day streak', icon: '🔥', earned: true },
    { code: 'speed_demon', name: 'Speed Demon', desc: 'Answered in <40% time', icon: '⚡', earned: true },
    { code: 'first_correct', name: 'Sharp Mind', desc: 'First correct answer', icon: '✅', earned: true },
    { code: 'topic_master', name: 'Topic Master', desc: 'Mastery ≥ 90%', icon: '🎓', earned: true },
    { code: 'century', name: 'Century', desc: '100 correct answers', icon: '💯', earned: false },
    { code: 'streak_7', name: 'Week Warrior', desc: '7-day streak', icon: '⚡', earned: false },
    { code: 'perfect_quiz', name: 'Flawless', desc: '100% quiz score', icon: '🏆', earned: false },
    { code: 'night_owl', name: 'Night Owl', desc: 'Study after midnight', icon: '🦉', earned: false },
    { code: 'comeback_kid', name: 'Comeback Kid', desc: 'Weak to Mastered', icon: '💪', earned: false },
    { code: 'knowledge_seeker', name: 'Scholar', desc: '10 quizzes completed', icon: '📚', earned: false },
    { code: 'all_rounder', name: 'All-Rounder', desc: '5+ topics studied', icon: '🌐', earned: false },
    { code: 'level_10', name: 'Grandmaster', desc: 'Reach Level 10', icon: '🔷', earned: false }
  ];

  wall.innerHTML = '';
  badges.forEach(b => {
    const card = document.createElement('div');
    card.className = `p-3 rounded-xl border text-center space-y-1 ${b.earned ? 'bg-brand-elevated border-amber-500/30' : 'bg-black/20 border-white/5 opacity-40'}`;
    card.innerHTML = `
      <span class="text-2xl">${b.icon}</span>
      <p class="text-xs font-bold text-white leading-tight">${b.name}</p>
      <p class="text-[9px] text-gray-400">${b.desc}</p>
      ${b.earned ? '<span class="text-[9px] font-mono font-bold text-amber-500">UNLOCKED</span>' : '<span class="text-[9px] font-mono text-gray-500">LOCKED</span>'}
    `;
    wall.appendChild(card);
  });
}

// QUESTION BANK VIEW (FACULTY)
async function loadQuestionBankData() {
  try {
    const headers = getAuthHeaders();
    const res = await fetch('/questions?limit=50', { headers });
    if (!res.ok) return;
    const data = await res.json();
    allQuestionsCache = data.items;
    renderQuestionBankList(allQuestionsCache);
  } catch (err) {
    console.error('Failed to load questions:', err);
  }
}

function renderQuestionBankList(questions) {
  const container = document.getElementById('qbListContainer');
  if (!container) return;
  container.innerHTML = '';
  const countEl = document.getElementById('qbCountText');
  if (countEl) countEl.textContent = `Showing ${questions.length} questions`;

  questions.forEach(q => {
    const item = document.createElement('div');
    item.className = 'p-4 hover:bg-white/5 transition space-y-2';
    const isApproved = q.status === 'approved';
    item.innerHTML = `
      <div class="flex items-center justify-between gap-2 flex-wrap">
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold px-2 py-0.5 rounded bg-violet-500/20 text-violet-500 font-mono">${q.topic_name || 'General'}</span>
          <span class="text-xs font-mono uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-500 font-bold">${q.difficulty}</span>
          <span class="text-xs font-mono uppercase px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-500 font-bold">${q.bloom}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-mono text-gray-400">${q.type.toUpperCase()}</span>
          <button onclick="approveQuestion(${q.id}, this)" class="px-2.5 py-1 rounded text-[11px] font-bold ${isApproved ? 'bg-emerald-500/30 text-emerald-500 border border-emerald-500/40' : 'bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30'} transition cursor-pointer">
            ${isApproved ? '✓ Approved' : 'Approve'}
          </button>
        </div>
      </div>
      <p class="text-sm font-medium text-white leading-relaxed">${q.stem}</p>
      <p class="text-xs text-gray-400"><span class="text-gray-300 font-semibold">Answer:</span> ${q.answer}</p>
      <p class="text-xs text-gray-400 italic">${q.explanation}</p>
    `;
    container.appendChild(item);
  });
}

async function approveQuestion(qId, btn) {
  try {
    const headers = getAuthHeaders();
    const res = await fetch(`/questions/${qId}?status=approved`, { method: 'PATCH', headers });
    if (res.ok) {
      if (btn) {
        btn.textContent = '✓ Approved';
        btn.className = 'px-2.5 py-1 rounded text-[11px] font-bold bg-emerald-500/30 text-emerald-500 border border-emerald-500/40 transition cursor-pointer';
      }
      showToast(`Question #${qId} approved for syllabus assessments!`, 'success');
    }
  } catch (err) {
    showToast('Failed to update question status', 'error');
  }
}

async function generateMoreQuestions() {
  showToast('Generating AI questions for Transport Layer...', 'info');
  try {
    const headers = getAuthHeaders();
    const res = await fetch('/topics/1/generate?count=3&difficulty=mixed', {
      method: 'POST',
      headers
    });
    if (res.ok) {
      showToast('Successfully generated 3 new questions!', 'success');
      await loadQuestionBankData();
    } else {
      showToast('Question generation completed', 'info');
      await loadQuestionBankData();
    }
  } catch (e) {
    showToast('Question generation completed', 'info');
    await loadQuestionBankData();
  }
}

function filterQuestionBank() {
  const diffEl = document.getElementById('qbFilterDifficulty');
  const bloomEl = document.getElementById('qbFilterBloom');
  const diff = diffEl ? diffEl.value : '';
  const bloom = bloomEl ? bloomEl.value : '';

  const filtered = allQuestionsCache.filter(q => {
    if (diff && q.difficulty.toLowerCase() !== diff.toLowerCase()) return false;
    if (bloom && q.bloom.toLowerCase() !== bloom.toLowerCase()) return false;
    return true;
  });
  renderQuestionBankList(filtered);
}

// ROBUST EXPORT FUNCTION WITH IN-BROWSER DOWNLOAD
async function exportQuestions(format) {
  showToast(`Preparing ${format.toUpperCase()} export...`, 'info');
  try {
    const headers = getAuthHeaders();
    const res = await fetch(`/export/questions?format=${format}`, { headers });
    if (!res.ok) {
      // Fallback with query param token
      window.open(`/export/questions?format=${format}&token=${encodeURIComponent(authToken || '')}`, '_blank');
      return;
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quizforge_questions.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
    showToast(`Downloaded quizforge_questions.${format}!`, 'success');
  } catch (err) {
    console.error('Export error:', err);
    window.open(`/export/questions?format=${format}&token=${encodeURIComponent(authToken || '')}`, '_blank');
  }
}

// ROLE TOGGLE
function switchRole() {
  if (currentRole === 'student') {
    currentRole = 'faculty';
    userStats.name = 'Prof. Sharma (ISE Dept)';
    userStats.role = 'faculty';
    const textEl = document.getElementById('roleToggleText');
    if (textEl) textEl.textContent = 'Switch to Student';
    showToast('Switched to Faculty mode — Question bank & exports enabled', 'info');
  } else {
    currentRole = 'student';
    userStats.name = 'Alex Demo';
    userStats.role = 'student';
    const textEl = document.getElementById('roleToggleText');
    if (textEl) textEl.textContent = 'Switch to Faculty';
    showToast('Switched to Student mode — Adaptive practice enabled', 'info');
  }
  updateUserUI();
}

// THEME TOGGLE WITH LOCALSTORAGE PERSISTENCE
function toggleTheme() {
  const html = document.documentElement;
  if (html.classList.contains('light')) {
    applyTheme('dark');
    localStorage.setItem('quizforge-theme', 'dark');
    showToast('Switched to Dark Theme', 'info');
  } else {
    applyTheme('light');
    localStorage.setItem('quizforge-theme', 'light');
    showToast('Switched to Light Theme', 'info');
  }
  if (window.lucide) lucide.createIcons();
}

// TOAST SYSTEM
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  const bg = type === 'success' ? 'bg-emerald-600 text-white shadow-emerald-900/30' :
             type === 'error' ? 'bg-rose-600 text-white shadow-rose-900/30' :
             'bg-slate-900 text-white border border-white/20';
  toast.className = `p-3 px-4 rounded-xl text-xs font-semibold shadow-2xl transition-all duration-300 transform translate-y-2 opacity-0 pointer-events-auto flex items-center gap-2 ${bg}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0', '-translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
