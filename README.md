# QuizForge — Gamified AI-Based Syllabus-to-Quiz Learning System
**Mini Project BIS586 • Department of Information Science & Engineering • Bangalore Institute of Technology**

---

## 🌟 Executive Overview
**QuizForge** is an end-to-end, adaptive educational platform that transforms static academic syllabus documents (PDF/DOCX) into personalized, gamified micro-learning quizzes. It couples real-time syllabus parsing and topic taxonomy extraction with **Bayesian Knowledge Tracing (BKT)** to track per-topic student mastery, detect weak concepts, and adaptively route the optimal question next.

---

## 🚀 Key Highlights & Architecture

### 1. Document Ingestion & Topic Decomposition
- **File Ingestion:** Drag-and-drop PDF & DOCX syllabus uploader with scanned PDF detection.
- **Parsing Engine:** PyMuPDF (`fitz`) and `python-docx` preserve hierarchical heading levels (`Unit` → `Topic` → `Subtopic`).
- **Topic Extraction:** Multi-tier fallback hierarchy (Heading analysis → TF-IDF & KMeans → paragraph chunking).

### 2. AI Question Generation & Deduplication
- **Multi-Provider LLM Abstraction (`LLMProvider`):** Support for Google Gemini Flash, OpenAI, Anthropic, Ollama, and a zero-dependency template-driven **MockProvider**.
- **Pedagogical Tagging:** Every question tags Bloom's Taxonomy (`Remember`, `Understand`, `Apply`, `Analyze`), difficulty (`easy`, `medium`, `hard`), comprehensive explanations, and specific syllabus source citations.
- **Deduplication:** Questions validated with Pydantic v2 schemas and cosine similarity checks to prevent duplicates.

### 3. Bayesian Knowledge Tracing (BKT)
Each student-topic pair maintains an evolving knowledge state:
$$\begin{aligned}
p(L' \mid \text{correct}) &= \frac{p(L)(1 - p_s)}{p(L)(1 - p_s) + (1 - p(L)) p_g} \\
p(L' \mid \text{wrong}) &= \frac{p(L) p_s}{p(L) p_s + (1 - p(L))(1 - p_g)} \\
p(L_{next}) &= p(L') + (1 - p(L')) p_t
\end{aligned}$$
- **Priors:** $p_{\text{init}} \in [0.25, 0.40]$ derived from topic difficulty.
- **Parameters:** $p_t = 0.15$, $p_s = 0.10$, $p_g = 0.25$ (MCQ) or $0.50$ (True/False).
- **Classification:** **Weak Topic** ($p(L) < 0.60$ after $\ge 3$ attempts); **Mastered** ($p(L) \ge 0.90$).

### 4. Adaptive Question Selector
- **Sampling Weight:** $\text{weight} = (1 - \text{mastery})^2 + 0.15 \times \text{recency\_bonus}$
- **Exploration:** 20% random exploration over non-weak topics to ensure syllabus coverage.
- **Difficulty Staircase:** Correct answer steps up difficulty; wrong answer steps down; two consecutive wrong answers trigger remedial mode.
- **Transparency:** Every question includes a `"Why this question?"` explanation (e.g., *"Focusing on weak topic: IPv4 Subnetting (38% mastery)"*).

### 5. Gamification & Engagement Mechanics
- **XP Calculation:**
  $$\text{XP} = \text{base} \times (1 + \min(\text{streak}, 10) \times 0.1) \times \text{speed\_bonus}$$
  where base is 10 (easy), 20 (medium), or 35 (hard), with $+25\%$ speed bonus if answered in $<40\%$ of allotted time.
- **Progression:** Level $n$ requires $100 \times n^{1.5}$ XP.
- **Badges:** 12+ achievements (*On Fire*, *Speed Demon*, *Sharp Mind*, *Topic Master*, *Comeback Kid*, etc.).
- **Lifelines:** 50:50, Skip, and +15s Time extension.

### 6. Faculty Question Bank & Export
- Faculty role toggle.
- Question bank filtering by difficulty and Bloom level.
- Multi-format export in **CSV**, **JSON**, and **DOCX** with ABET/NBA course outcome mapping columns.

---

## 🛠️ Technology Stack
- **Backend:** Python 3.11/3.13, FastAPI, SQLAlchemy 2.x, Pydantic v2, PyMuPDF, python-docx, bcrypt, python-jose, SQLite.
- **Frontend:** Responsive SPA with Tailwind CSS, Space Grotesk + Inter + JetBrains Mono typography, Lucide icons, Canvas Confetti.
- **Testing:** `pytest` unit test suite covering BKT math, XP formulas, and adaptive selection.

---

## 🏃 Quick Start & Running Instructions

### 1. Start the Unified Server
Run from the project root:
```powershell
cd "backend"
python -m uvicorn app.main:app --reload --port 8000
```
Then open your browser at **http://localhost:8000**.

### 2. Demo Credentials (Pre-seeded)
- **Student User:** `demo@quizforge.app` / `demo1234`
- **Faculty User:** `faculty@quizforge.app` / `faculty1234`

### 3. Running Automated Tests
```powershell
$env:PYTHONPATH="C:\Users\VIBHA C\.gemini\antigravity\scratch\quizforge\backend"
python -m pytest backend/tests/ -v
```

---

## 📂 Project Structure
```
quizforge/
├── SPEC.md
├── README.md
├── contracts/
│   └── openapi.json
├── samples/
│   └── computer_networks.pdf
├── frontend/
│   ├── index.html
│   └── static/
│       └── app.js
└── backend/
    ├── quizforge.db
    ├── pyproject.toml
    ├── seed.py
    ├── scripts/
    │   ├── create_sample_pdf.py
    │   └── seed_db.py
    ├── tests/
    │   ├── conftest.py
    │   ├── test_bkt.py
    │   ├── test_xp.py
    │   ├── test_adaptive.py
    │   ├── test_auth.py
    │   └── test_quiz.py
    └── app/
        ├── main.py
        ├── config.py
        ├── database.py
        ├── models/
        ├── schemas/
        ├── core/
        ├── services/
        │   ├── bkt/
        │   ├── adaptive/
        │   ├── gamification/
        │   ├── parsing/
        │   ├── topics/
        │   └── generation/
        └── api/
```
