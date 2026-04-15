# 🎵 Music Recommender Simulation

## Project Summary

This project builds **VibeFinder 1.0**, a small music recommender that picks songs from a tiny catalog based on a user's taste profile. It represents each song and each user as plain data, uses a simple scoring rule to rank songs, and prints the top picks with short reasons explaining why. The point is not to build a real music app — it is to see how scoring rules, weights, and data gaps shape what a user ends up seeing.

---

## How The System Works

**Song features used:** genre, mood, energy, tempo_bpm, valence, danceability, acousticness.

**UserProfile stores 4 pieces of information:**

- `favorite_genre` — the user's preferred music genre
- `favorite_mood` — the user's preferred mood (e.g., happy, sad, chill)
- `target_energy` — the desired energy level (0.0–1.0)
- `likes_acoustic` — whether the user prefers acoustic music

**How the Recommender computes a score:**

The recommender walks through every song and adds up points for each feature that matches the user's taste.

- **Genre match:** +2.0 if the song's genre equals `favorite_genre`
- **Mood match:** +1.5 if the song's mood equals `favorite_mood`
- **Energy closeness:** `(1 - |song.energy - target_energy|) * 1.0` — the closer the two numbers, the more points. Example: user wants 0.40, Song A at 0.42 scores 0.98; Song B at 0.91 scores only 0.49.
- **Acoustic bonus:** +0.5 if the user likes acoustic and the song's acousticness ≥ 0.5
- For `tempo_bpm`, values are normalized with `(tempo - 60) / (152 - 60)` so they sit on the same 0–1 scale as other features.

**How songs are chosen to recommend:**

1. Score every song against the user's preferences.
2. Filter out songs that fail basic rules (e.g., negative energy score).
3. Sort by total score, highest first.
4. Return the top `k` with a short list of reasons per pick.

Scoring tells you how good each song is; filtering, sorting, and presentation decide which ones the user actually sees.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python -m src.main
   ```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

- **Lowered genre weight from 2.0 to 0.5.** The top results became much more varied. Pop songs stopped dominating the lofi listener's list, and mood + energy drove more of the ranking. This showed how one weight choice basically sets the "personality" of the whole system.
- **Added tempo and valence to scoring.** Using normalized tempo closeness and valence closeness made results feel more fine-grained — two lofi songs that had looked identical now split apart based on how upbeat they felt. But the extra features also pulled rankings around in ways that were hard to explain.
- **Tried multiple user types.** A focused lofi/chill listener got clean, intuitive results. A user asking for "chill mood + max energy" (a contradiction) still got recommendations, because the system happily added points for both halves. A user asking for an unknown genre like "polka" still got songs — just low-scoring ones, with no warning.

---

## Limitations and Risks

- It only works on a tiny catalog of 18 songs.
- It does not understand lyrics, language, or cultural context.
- It over-favors one genre by default because genre match gives the biggest point boost.
- It silently ignores unknown moods and genres instead of warning the user.
- It rewards contradictory preferences (e.g., chill + high energy) at the same time.
- Tempo, valence, and danceability live in the data but are not used by the base scoring logic.

You will go deeper on this in the model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this recommender made it clear how much of a system's "opinion" is baked into a handful of numbers. The +2.0 weight on genre isn't a fact — it's a judgment that genre matters more than mood or energy. Change that number and the system behaves like a different product. Real recommenders do the same thing with far more features, but the core idea is identical: turn taste into data, compare it to items, and rank.

Bias shows up quietly. If the catalog is missing moods like "sad" or genres like "jazz," users who want those things just get worse matches — no error, no explanation, just silently lower-quality lists. A real product would amplify this: whoever builds the catalog and picks the weights decides whose taste counts as "normal." That's where unfairness enters, long before any fancy algorithm runs.

---

## 🎧 Model Card — Music Recommender Simulation

### 1. Model Name

**VibeFinder 1.0**

---

### 2. Intended Use

VibeFinder suggests 3–5 songs from a small catalog based on a user's preferred genre, mood, energy level, and acoustic preference. It is built for classroom exploration only — not for real users or production use.

---

### 3. How It Works (Short Explanation)

For each song, VibeFinder checks how well it matches the user's taste and adds up points:

- Big boost if the genre matches.
- Smaller boost if the mood matches.
- More points the closer the song's energy is to what the user wants.
- A small bonus if the user likes acoustic and the song is mostly acoustic.

The songs with the highest totals are shown first, with short reasons explaining each pick.

---

### 4. Data

- 18 songs in `data/songs.csv`.
- Fields: title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness.
- Genres represented: pop, lofi, rock, and a few others. Moods: chill, happy, intense.
- Many real genres (jazz, classical, hip-hop, country, metal) and moods (sad, romantic, angry) are missing.
- The taste reflected is narrow — it looks like the listening habits of a student who likes lofi and mainstream pop, not the world at large.

---

### 5. Strengths

- Works well for users whose taste matches well-represented genres (lofi/chill, pop/happy).
- Simple, transparent scoring — every recommendation comes with a clear list of reasons.
- Fast and easy to tweak: change one weight and you can see the whole system shift.

---

### 6. Limitations and Bias

- Ignores tempo, valence, and danceability in the base scoring, even though they're in the data.
- Treats every user as having the same 4-field taste shape.
- Biased toward the biggest genre in the catalog because genre match is worth the most points.
- Silently gives bad recommendations for unknown moods or genres instead of warning the user.
- In a real product, this kind of silent failure could push whole communities of users toward content that doesn't fit them, without them realizing why.

---

### 7. Evaluation

I ran `src/evaluate.py`, which tests six adversarial user profiles:

- Conflicting: high energy + sad mood
- Conflicting: chill mood + max energy
- Unknown genre ("polka")
- Out-of-range energy (`target_energy = 2.0`)
- Everything-neutral user (empty genre and mood)
- Acoustic lover who also wants rock

I looked at whether the system crashed, whether the top picks felt reasonable, and whether odd inputs got called out. The system never crashed — but it also never complained. It silently produced mediocre recommendations for bad inputs, which matched my expectation but still felt uncomfortable.

---

### 8. Future Work

- Use tempo, valence, and danceability in scoring.
- Support multiple favorite genres and moods per user.
- Add diversity to the top `k` so results aren't near-duplicates.
- Warn the user when their genre or mood doesn't exist in the catalog.
- Add a "group vibe" mode that blends multiple user profiles.

---

### 9. Personal Reflection

What surprised me most was how confident the system looks even when it's wrong. A score of 2.5 with two neat reasons feels authoritative, even if the underlying inputs were contradictory. Building this changed how I read real music apps — the "match %" numbers they show are the visible tip of a lot of invisible choices about weights and data. Human judgment still matters, especially in deciding what goes in the catalog, which features count, and how much. The model is only ever as thoughtful as the person who set its weights.
