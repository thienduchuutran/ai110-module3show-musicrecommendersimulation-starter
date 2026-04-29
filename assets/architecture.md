# VibeFinder 2.0 — System Architecture

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                  │
│           "calm music for late-night coding"                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1 — Preference Extraction            [src/agent.py]           │
│                                                                     │
│  Groq LLM (llama-3.1-8b-instant) reads the query and the           │
│  catalog's available genres/moods, then returns a structured        │
│  preference dict:                                                   │
│    { favorite_genre, favorite_mood, target_energy,                  │
│      target_acousticness, likes_acoustic, ... }                     │
│                                                                     │
│  ┌─────────────────────────────────────┐                            │
│  │  GUARDRAILS     [src/logger.py]     │                            │
│  │  Clamp floats to [0.0, 1.0]         │                            │
│  │  Fill missing required fields       │                            │
│  │  Log warnings for corrections       │                            │
│  └─────────────────────────────────────┘                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │  structured prefs dict
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2 — Rule-Based Scoring               [src/recommender.py]     │
│                                                                     │
│  score_song() evaluates every song (18 songs in data/songs.csv):   │
│    +2.0  genre match                                                │
│    +1.5  mood match                                                 │
│    +1.0  energy closeness  (1 - |song.energy - target_energy|)      │
│    +0.5  acoustic bonus                                             │
│                                                                     │
│  recommend_songs() sorts by score, returns top 10 candidates        │
└────────────────────────────┬────────────────────────────────────────┘
                             │  top 10 (song, score, reasons)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3 — Diversity Re-Rank                [src/agent.py]           │
│                                                                     │
│  Groq LLM reviews all 10 candidates and selects the best 5,        │
│  balancing high scores against genre/artist variety.                │
│  (prevents top-5 from being all the same genre)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │  top 5 diverse picks
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4 — Personalized Explanation         [src/agent.py]           │
│                                                                     │
│  Groq LLM writes a 2-3 sentence playlist note that:                 │
│    - References the user's exact words                              │
│    - Names specific song titles                                     │
│    - Explains why each fits the vibe                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OUTPUT + LOGGING                          [src/logger.py]          │
│                                                                     │
│  • Display: ranked playlist with scores and reasons                 │
│  • logs/session_<timestamp>.json — full pipeline record             │
│    (query → extracted prefs → candidates → final picks → note)      │
│  • logs/vibefinder.log — INFO/WARNING/ERROR stream                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Map

```
ai110-module3show-musicrecommendersimulation-starter/
│
├── src/
│   ├── main.py          Entry point — interactive loop, pipeline wiring
│   ├── agent.py         AI layer — 3 Groq LLM calls
│   ├── recommender.py   Rule-based scorer (untouched from v1.0)
│   ├── logger.py        Session logging + preference guardrails
│   └── evaluate.py      Test harness (adversarial profiles + NL tests)
│
├── data/
│   └── songs.csv        18-song catalog with audio attributes
│
├── tests/
│   └── test_recommender.py  Unit tests for OOP Recommender class
│
├── assets/
│   └── architecture.md  This file — system diagram
│
└── logs/                Auto-created at runtime
    ├── vibefinder.log
    └── session_<timestamp>.json
```

## Data Flow Summary

```
Natural Language  →  [LLM]  →  Structured Prefs  →  [Scorer]  →  Candidates
                                                                       │
                                                              [LLM Diversity]
                                                                       │
                                                               Final Top 5
                                                                       │
                                                           [LLM Explanation]
                                                                       │
                                                            User-facing output
                                                            + JSON session log
```
