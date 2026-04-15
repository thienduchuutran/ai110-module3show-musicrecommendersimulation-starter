# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0** — a simple song picker that tries to match your mood.

---

## 2. Intended Use

VibeFinder suggests songs from a small catalog that fit a user's stated taste.

- It generates a short ranked list (top k) of songs with reasons for each pick.
- It assumes the user can describe their taste as a favorite genre, favorite mood, target energy level, and whether they like acoustic music.
- This is built for classroom exploration, not real users. It is a learning tool to see how scoring rules shape recommendations.

---

## 3. How the Model Works

For each song, VibeFinder checks how well it matches the user's taste and gives it points.

- If the song's genre matches the user's favorite genre, it gets a big boost.
- If the song's mood matches the user's favorite mood, it gets another boost.
- It compares the song's energy level to the energy the user wants. The closer they are, the more points the song earns.
- If the user likes acoustic music and the song is pretty acoustic, it gets a small bonus.

All the points are added up. Songs with the highest total scores are shown first, with a short list of reasons explaining why.

---

## 4. Data

The catalog lives in `data/songs.csv`.

- It holds **18 songs** with fields for title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness.
- Genres include pop, lofi, rock, and a few others. Moods include chill, happy, and intense.
- The dataset is tiny and hand-picked. Many real genres (jazz, classical, hip-hop, country, metal) and moods (sad, romantic, angry) are missing or barely represented.
- Because the catalog is so small, two or three songs can dominate results for a given taste.

---

## 5. Strengths

- Works well for users whose taste lines up with well-represented genres like lofi/chill or pop/happy.
- The scoring captures the simple idea that genre and mood matter more than small energy differences.
- The reasons shown next to each song make it easy to see why it was picked.

---

## 6. Limitations and Bias

- The model ignores tempo, valence, and danceability even though they are in the data. It only uses genre, mood, energy, and acousticness.
- A user who asks for a mood that doesn't exist in the catalog (like "sad") just loses those points silently — they get worse matches without any warning.
- Genre match gives the biggest boost (+2.0), so the system heavily favors one genre over balanced variety.
- Underrepresented genres get weak results no matter how the user tunes other knobs.
- Conflicting preferences (e.g., "chill mood" plus "max energy") can both add points to the same song, which is a bit nonsensical.

---

## 7. Evaluation

I tested VibeFinder with `src/evaluate.py`, which runs several adversarial user profiles:

- A late-night lofi listener (the main profile in `main.py`).
- Conflicting cases like "high energy + sad mood" and "chill mood + max energy."
- Unknown genres like "polka" that don't exist in the catalog.
- Out-of-range values like `target_energy = 2.0`.
- A fully neutral user with empty genre and mood.
- A user who wants rock but also loves acoustic songs.

I looked at whether the top picks felt reasonable and whether odd inputs broke the system. What surprised me: the scoring never crashes on bad input, but it silently gives low-quality recommendations. The "chill + max energy" profile also exposed that the model will reward both halves of a contradiction at once.

---

## 8. Future Work

- Use the ignored features (tempo, valence, danceability) in scoring.
- Warn the user when their favorite genre or mood doesn't exist in the catalog.
- Add diversity to the top k so results aren't all near-duplicates from one genre.
- Support multiple favorite genres/moods instead of just one.

---

## 9. Personal Reflection

Building this made me see how much of a recommender's personality lives in a handful of numbers (the point weights). Changing +2.0 to +1.0 for genre quietly changes everything. The most interesting part was watching the adversarial profiles — the system never errors out, but it can happily recommend nonsense with a confident-looking score. It made me more suspicious of real music apps that show a single "match %" without explaining what's actually behind it.
