# QuizForge — Gamified AI-Based Syllabus-to-Quiz Learning System
**Mini Project BIS586 | Department of ISE | Bangalore Institute of Technology**

---

## 1. Project Overview

QuizForge transforms a syllabus PDF or DOCX into an adaptive, gamified quiz experience. The pipeline: **Upload → Parse → Topic Extraction → AI Question Generation → Gamified Quiz → BKT Mastery Tracking → Adaptive Personalization**.

---

## 2. Tech Stack (Fixed)

### Backend
- Python 3.11, FastAPI, SQLAlchemy 2.x, Pydantic v2
- SQLite default (PostgreSQL via `DATABASE_URL`)
- JWT auth (bcrypt + python-jose)
- pytest

### Frontend
- React 18 + Vite + TypeScript
- Tailwind CSS, Framer Motion, Recharts
- Zustand, React Router, lucide-react, canvas-confetti
- Vitest

### Parsing
- PyMuPDF (PDF), python-docx (DOCX)
- Detect scanned PDFs → clear error, optional pytesseract
- Fallback chain: heading-based → TF-IDF+KMeans → LDA

### NLP
- spaCy en_core_web_sm
- sentence-transformers all-MiniLM-L6-v2
- BERTopic
- Auto-selects by document size; never crashes if model fails

### LLM
- `LLMProvider` abstraction
- Providers: Gemini (default), Anthropic, OpenAI, Ollama, MockProvider
- Selected by `LLM_PROVIDER` env var
- MockProvider: template-based questions, no API key needed
- Force JSON, Pydantic validation, retry once, backoff, fallback to Mock

---

## 3. Features

1. Upload PDF/DOCX (drag-drop, 20MB limit, validation)
2. Syllabus structure extraction (units → topics → subtopics), editable tree
3. AI topic identification: embedding clustering + heading seeding
4. LLM question generation: MCQ, T/F, short answer; difficulty, Bloom tags
5. Syllabus-topic-question mapping; coverage view; "Generate more"
6. Gamified quiz: timer, streak, combo, lifelines, keyboard shortcuts
7. XP, levels, streaks, 12+ badges
8. Weak-topic detection from BKT
9. Adaptive next-question selection with "Why this question?"
Plus: analytics, faculty question bank, CSV/JSON/DOCX export, role toggle

---

## 4. Algorithms

### BKT (Bayesian Knowledge Tracing)
- `p_init`: from topic difficulty prior (0.25–0.4, cold-start)
- `p_transit = 0.15`
- `p_slip = 0.10`
- `p_guess = 0.25` (MCQ-4), `0.5` (T/F)

**Update rules:**
- Correct: `pL' = pL(1−slip) / [pL(1−slip) + (1−pL)·guess]`
- Wrong: `pL' = pL·slip / [pL·slip + (1−pL)(1−guess)]`
- Transition: `pL_next = pL' + (1−pL')·p_transit`

- Weak: mastery < 0.6 after ≥3 attempts
- Mastered: mastery ≥ 0.9

### Adaptive Selector
- Weight = `(1−mastery)² + 0.15·recency_bonus`
- 20% exploration over non-weak topics
- Difficulty staircase: correct→harder, wrong→easier, two wrong→remedial easy on neighboring topic
- No repeats within 10 turns
- "Why this question?" tooltip

### XP Formula
- Base: easy=10, medium=20, hard=35
- Multiplier: `× (1 + min(streak,10) × 0.1)`
- Speed bonus: up to +25% if answered in <40% of allotted time
- Level n: `100 × n^1.5` XP required

---

## 5. Data Model

| Table | Key Fields |
|-------|-----------|
| users | id, email, password_hash, role(student/faculty), created_at |
| documents | id, user_id, filename, status, raw_text, structure_json |
| topics | id, document_id, parent_id, name, keywords, summary, difficulty_prior |
| questions | id, topic_id, type, difficulty, bloom, stem, options, answer, explanation, source_snippet, status, embedding |
| quiz_sessions | id, user_id, mode, started_at, completed_at, score |
| attempts | id, session_id, user_id, question_id, correct, response_ms, ts |
| mastery | id, user_id, topic_id, p_L, attempts_count, history_json |
| user_stats | id, user_id, xp, level, streak, last_active, streak_freeze |
| badges | id, code, name, description, icon |
| user_badges | id, user_id, badge_id, earned_at |

---

## 6. API Contract

Full OpenAPI 3.0 spec in `/contracts/openapi.json`.

Key endpoints:
- `POST /auth/register`, `POST /auth/login`
- `POST /documents` (multipart), `GET /documents`, `GET /documents/{id}/topics`
- `PATCH /topics/{id}`, `POST /topics/{id}/generate`
- `GET /questions`
- `POST /quiz/start`, `POST /quiz/{id}/answer`
- `GET /analytics/mastery`, `/analytics/progress`, `/analytics/coverage`
- `GET /leaderboard`
- `GET /export/questions`
- `GET /documents/{id}/progress` (SSE)

---

## 7. Screens

1. **Landing/Login**: hero, animated pipeline, "Try demo"
2. **Upload**: drag-drop, live pipeline stepper, topic tree preview
3. **Dashboard**: level ring, XP bar, streak, weak topics, radar chart, heatmap, badges
4. **Syllabus Map**: interactive tree, mastery-colored nodes
5. **Quiz**: one question, timer, combo, XP popups, confetti, keyboard shortcuts
6. **Results**: score, XP, mastery deltas, badges, recommendations
7. **Analytics**: mastery over time, Bloom heatmap, accuracy scatter
8. **Question Bank** (faculty): filterable table, coverage matrix, export
9. **Badges & Leaderboard**: badge wall, weekly leaderboard

---

## 8. Design System

- Dark default, light toggle (persisted)
- Colors: bg `#0B0F1A`, surface `#121829`, elevated `#1A2238`
- Primary gradient: violet `#7C5CFF` → cyan `#22D3EE`
- Success `#34D399`, Warning `#FBBF24`, Danger `#F87171`, XP Gold `#FFC53D`
- Light mode: warm off-white `#F7F8FC`
- Fonts: Space Grotesk (headings), Inter (body), JetBrains Mono (numbers)
- Duolingo energy × Linear polish

---

## 9. Quality Bar

- Strict TypeScript (no `any` in app code)
- Robust error handling (corrupt PDFs, LLM timeouts, rate limits)
- Tests: pytest (BKT math, XP calc, adaptive selector, parser, API); Vitest (key components)
- Security: bcrypt, JWT expiry, upload validation, CORS
- Performance: embedding cache, batch LLM, background jobs, pagination

---

## 10. Build Order

| Phase | Scope | Agent |
|-------|-------|-------|
| 0 | Scaffold, contracts, DB models, seed | Main |
| 1 | Parsing → topics → Mock generation E2E | BACKEND |
| 2 | Quiz engine, BKT, adaptive, XP/badges + tests | BACKEND |
| 3 | All 9 frontend screens + mock API | FRONTEND |
| 4 | Real LLM providers, exports, polish | BACKEND+FRONTEND |
| 5 | QA/integration, screenshots, verification report | QA |

---

## 11. Seed Data

- Demo user: `demo@quizforge.app` / `demo1234` (student role)
- Faculty user: `faculty@quizforge.app` / `faculty1234`
- Pre-parsed "Computer Networks" syllabus (6 units, 24 topics, 120+ questions)
- Try Demo login on landing page

---

## 12. Run Instructions

```bash
cp .env.example .env
make dev      # starts backend + frontend
# OR
docker-compose up
```

Backend: http://localhost:8000
Frontend: http://localhost:5173
API Docs: http://localhost:8000/docs
