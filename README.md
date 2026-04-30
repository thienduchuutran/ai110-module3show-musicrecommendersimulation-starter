# VibeFinder 2.0 — AI Music Recommender

**Base project:** AI110 Module 3 — Music Recommender Simulation

VibeFinder started as a rule-based song scorer (VibeFinder 1.0) that matched hardcoded preference dicts against a 18-song catalog. VibeFinder 2.0 wraps that same scorer with an agentic AI pipeline: you describe what you want in plain English, and an LLM extracts your preferences, runs the scorer, re-ranks for diversity, and writes you a personalized playlist note.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                  │
│           "calm music for late-night coding"                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1 — Preference Extraction            [src/agent.py]           │
│  Groq LLM maps the query to a structured preference dict            │
│  { favorite_genre, target_energy, likes_acoustic, ... }             │
│  + Guardrails: clamp out-of-range values    [src/logger.py]         │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2 — Rule-Based Scoring               [src/recommender.py]     │
│  score_song() scores all 18 songs; returns top 10 candidates        │
│    +2.0 genre  +1.5 mood  +1.0 energy closeness  +0.5 acoustic      │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3 — Diversity Re-Rank                [src/agent.py]           │
│  Groq LLM picks best 5 from top 10 — balancing score + variety      │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4 — Personalized Explanation         [src/agent.py]           │
│  Groq LLM writes a playlist note referencing the user's own words   │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
            Display results + save full session to logs/
```

Full component diagram: [assets/architecture.md](assets/architecture.md)

---

## AI Features

| Feature | How it's implemented |
|---|---|
| Agentic Workflow | 4 sequential steps where each step's output feeds the next |
| LLM Preference Extraction | Groq (llama-3.1-8b-instant) translates natural language to structured prefs |
| Diversity Re-Ranking | LLM selects top-5 from top-10 candidates for genre/artist variety |
| Guardrails | `validate_preferences()` clamps AI-generated values to valid ranges |
| Session Logging | Every pipeline run is saved as a timestamped JSON in `logs/` |
| NL Test Harness | `evaluate.py --nl` verifies extraction quality against expected mappings |

---

## Project Structure

```
├── src/
│   ├── main.py          Interactive loop + pipeline wiring
│   ├── agent.py         3 Groq LLM calls (extract, diversify, explain)
│   ├── recommender.py   Rule-based scorer (unchanged from v1.0)
│   ├── logger.py        JSON session logs + preference guardrails
│   └── evaluate.py      Adversarial profiles + NL extraction test harness
├── data/
│   └── songs.csv        18-song catalog with audio attributes
├── tests/
│   └── test_recommender.py
├── assets/
│   └── architecture.md  System architecture diagram
└── logs/                Auto-created at runtime (gitignored)
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get a free Groq API key

Sign up at [console.groq.com](https://console.groq.com) — no credit card required.

### 3. Set your API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your-key-here
```

### 4. Run the app

```bash
cd src
python main.py
```

Example session:

```
What are you in the mood for? > calm music for late-night coding

[Step 1] Understanding your request...
         Heard as: lofi / chill, energy=0.35, acoustic=True
         Why: Late-night coding implies low energy and focused calm

[Step 2] Scoring all songs...
         10 candidates scored (4.98 → 2.22)

[Step 3] Selecting a diverse top-5...
         Prioritised high scores while mixing genres for variety

[Step 4] Writing your playlist note...

════════════════ YOUR PERSONALIZED PLAYLIST ════════════════
Given your need for late-night focus, "Midnight Coding" and
"Library Rain" capture exactly that low-energy headspace...
```

---

## Running Tests

```bash
# Unit tests for the rule-based scorer
pytest

# Adversarial scorer stress-test (no API key needed)
cd src && python evaluate.py

# NL extraction test harness (calls Groq, ~15 seconds)
cd src && python evaluate.py --nl

# Both
cd src && python evaluate.py --all
```

---

## How the Scorer Works (VibeFinder 1.0 core)

`score_song()` in `recommender.py` gives each song points for matching the user's preferences:

| Feature | Points |
|---|---|
| Genre match | +2.0 |
| Mood match | +1.5 |
| Energy closeness | `(1 - \|song.energy - target\|) × 1.0` |
| Acoustic bonus | +0.5 if user likes acoustic and song acousticness ≥ 0.5 |

In VibeFinder 2.0, the user's preference dict is no longer hardcoded — it is extracted from natural language by the LLM in Step 1.

---

## Limitations

- 18-song catalog — results are limited by what's available
- LLM extraction can misinterpret ambiguous queries
- Scorer uses only 4 of 8 available audio attributes (tempo, valence, danceability unused)
- Diversity re-ranking is LLM-guided, not guaranteed — fallback pads from remaining candidates if needed

---

## Reflection

See [model_card.md](model_card.md) for full reflection on AI collaboration, bias analysis, and evaluation results.


https://www.loom.com/share/d63024c0c0944f198c08abb52efd339b