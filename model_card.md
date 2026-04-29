# Model Card: VibeFinder 2.0

## 1. Model Name and Version

**VibeFinder 2.0** — AI-augmented music recommender  
Builds on VibeFinder 1.0 (rule-based scorer) by adding an agentic LLM pipeline.

**LLM used:** Groq API — `llama-3.1-8b-instant`  
**Base scorer:** unchanged rule-based `score_song()` from v1.0

---

## 2. Intended Use

VibeFinder 2.0 accepts a natural language description of what the user wants to hear and returns a ranked, diverse playlist of 5 songs with a personalized explanation. It is built for classroom exploration of agentic AI design — not for production use.

---

## 3. How the System Works

The pipeline has 4 steps, each feeding the next:

1. **Preference Extraction** — LLM reads the user's query and the catalog's available genres/moods, returns a structured preference dict (genre, mood, energy, acousticness, etc.)
2. **Rule-Based Scoring** — unchanged `score_song()` scores all 18 songs against the extracted preferences, returns top 10 candidates
3. **Diversity Re-Ranking** — LLM selects the best 5 from those 10, balancing score against genre and artist variety
4. **Personalized Explanation** — LLM writes a 2-3 sentence playlist note referencing the user's exact words and specific song titles

A guardrail layer (`logger.validate_preferences`) clamps any out-of-range values from the LLM before they reach the scorer.

---

## 4. Data

- **Catalog:** `data/songs.csv` — 18 songs with fields: title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness
- **Genres:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, classical, electronic, folk, r&b, reggae, metal, country
- **Moods:** happy, chill, intense, moody, focused, energetic, peaceful, nostalgic, romantic, relaxed, uplifting, melancholy, angry
- The catalog is hand-picked and small — real-world diversity is absent

---

## 5. Strengths

- Natural language input removes the need to understand the preference schema
- Transparent pipeline — every intermediate step is printed and logged
- Diversity re-ranking prevents the top-5 from clustering around one genre
- Session logging makes every recommendation fully replayable and debuggable
- Guardrails prevent silent score corruption from LLM-generated out-of-range values

---

## 6. Limitations and Bias

**Scorer-level (inherited from v1.0):**
- Genre match (+2.0) dominates — genres with more songs in the catalog get recommended disproportionately
- Tempo, valence, and danceability are in the data but unused in scoring
- Contradictory preferences (e.g., "chill mood + max energy") both earn points simultaneously

**LLM-level (new in v2.0):**
- Preference extraction can misinterpret short or ambiguous queries ("angry", "sad")
- The LLM may map niche requests to the closest catalog genre, silently dropping specificity
- Diversity re-ranking is LLM-guided — it can return fewer than k indices; the code falls back to score-order in that case
- The LLM was not fine-tuned for music; its genre/mood mappings reflect its training data, which may not match the user's cultural context

**Data bias:**
- The 18-song catalog skews toward Western mainstream genres — lofi, pop, rock dominate
- Underrepresented genres (reggae, country, classical) get fewer candidate songs, so diversity is harder to achieve for those users

---

## 7. AI Collaboration Reflection

This project was designed and implemented with AI assistance (Claude, Anthropic). The AI contributed:

- **Architecture design:** suggested the 4-step pipeline structure and the rationale for keeping the existing scorer unchanged rather than replacing it
- **Code generation:** wrote first drafts of `agent.py`, `logger.py`, and the extended `evaluate.py`
- **Debugging:** identified that Gemini and DeepSeek free tiers were unavailable and recommended Groq as a genuinely free alternative
- **Documentation:** drafted README and model card structure

What I decided and directed:
- The overall goal (natural language → recommendations)
- Choosing to keep `recommender.py` untouched as the reliable core
- The decision to show intermediate steps to the user (transparency requirement)
- Switching API providers when each hit quota/payment walls

The collaboration felt like pair programming — I described what I wanted, the AI produced a draft, I tested it, errors came back, and we iterated. The AI did not always get the API details right on the first try (Gemini model names, quota issues), which reinforced that testing is necessary even for AI-generated code.

---

## 8. Evaluation Results

### Adversarial Scorer Profiles (from `evaluate.py`)

Six edge-case preference dicts were tested against the scorer:

| Profile | Outcome |
|---|---|
| Conflicting: high energy + sad mood | "sad" mood not in catalog — silent miss; high energy songs ranked by energy alone |
| Conflicting: chill mood + max energy | Both halves rewarded simultaneously — contradictory output |
| Unknown genre ("polka") | No genre bonus; mood + energy still ranked sensibly |
| Out-of-range energy (2.0) | Energy closeness goes negative, filtered — system degrades gracefully |
| Everything-neutral (empty genre/mood) | Energy alone determines ranking — valid but generic results |
| Acoustic lover + rock | Rock songs score low on acousticness — preferences conflict, lower average scores |

**Finding:** The scorer never crashes on bad input, but silently produces degraded results. There is no warning to the user.

### NL Extraction Test Harness (from `evaluate.py --nl`)

Six natural language queries were tested with expected preference conditions:

| Query | Key checks | Result |
|---|---|---|
| "calm music for late-night studying" | energy ≤ 0.55, mood in [chill, focused, peaceful, relaxed] | Pass |
| "high energy workout music" | energy ≥ 0.65, mood in [energetic, intense, uplifting] | Pass |
| "sad acoustic folk songs for a rainy day" | likes_acoustic=True, genre in [folk, country, indie pop] | Pass |
| "jazz for a coffee shop morning" | genre in [jazz, lofi, folk], energy ≤ 0.65 | Pass |
| "angry metal to let off steam" | energy ≥ 0.75, genre in [metal, rock], mood in [angry, intense] | Pass |
| "romantic dinner background music" | energy ≤ 0.65, mood in [romantic, relaxed, peaceful] | Pass |

The LLM correctly mapped all 6 queries on initial runs. Short single-word queries ("angry") without context are more ambiguous and may map less reliably.

---

## 9. Testing Approach

- **Unit tests** (`tests/test_recommender.py`): verify the OOP `Recommender` class returns songs sorted by score
- **Adversarial stress-test** (`evaluate.py`): expose scorer behavior on edge-case inputs
- **NL extraction harness** (`evaluate.py --nl`): verify LLM preference extraction against expected semantic mappings; exits with code 1 on any failure
- **Session logs** (`logs/session_*.json`): every run is persisted — used to manually inspect pipeline behavior after the fact

---

## 10. Personal Reflection

The hardest part of VibeFinder 2.0 was not the code — it was finding a free API that actually worked. Gemini, DeepSeek, and several others hit quota walls or payment requirements before any code ran. That experience was a reminder that "free tier" in AI APIs often has more conditions than the marketing suggests.

The most interesting design question was where to put the AI. The first instinct is to replace the scorer entirely with an LLM. But keeping `score_song()` unchanged and only wrapping it with AI turned out to be the right call — the scorer is fast, deterministic, and testable. The LLM handles the two things rules can't do well: interpreting vague human language and making judgment calls about variety. Neither system alone would have been as good.

What this project made clear: agentic AI isn't magic — it's orchestration. Each step does one job, the output of one step feeds the next, and the whole thing falls apart if any step returns garbage. That's why the guardrail and the logging layer matter as much as the LLM calls themselves.
