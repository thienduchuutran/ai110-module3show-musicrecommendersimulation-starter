"""
Agentic pipeline for VibeFinder: three Gemini calls that wrap the existing scorer.

Step 1 — extract_preferences(): natural language → structured preference dict
Step 2 — (caller runs recommend_songs() with those prefs — existing scorer, unchanged)
Step 3 — diversify_results(): re-rank top candidates for genre/artist variety
Step 4 — generate_explanation(): personalized narrative referencing the user's words

Using Groq (llama-3.1-8b-instant) for all calls: genuinely free tier, no credit card required,
OpenAI-compatible API. Get a key at console.groq.com.
"""

import json
import os
from typing import Dict, List, Tuple

from openai import OpenAI

_client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
_MODEL = "llama-3.1-8b-instant"

# Injected into prompts so Gemini maps to values that actually exist in songs.csv —
# prevents silent mismatches like "hip hop" vs "hip-hop".
CATALOG_GENRES = [
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave",
    "indie pop", "hip-hop", "classical", "electronic", "folk",
    "r&b", "reggae", "metal", "country",
]
CATALOG_MOODS = [
    "happy", "chill", "intense", "moody", "focused", "energetic",
    "peaceful", "nostalgic", "romantic", "relaxed", "uplifting",
    "melancholy", "angry",
]


def _call(prompt: str) -> str:
    """Send a prompt to DeepSeek and return the text response."""
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def extract_preferences(user_query: str) -> Tuple[Dict, str]:
    """
    Step 1: Translate a natural language query into a structured preference dict.

    Returns (prefs_dict, reasoning_string). The reasoning is logged and shown
    to the user so the interpretation step is fully transparent.
    """
    prompt = f"""You are a music taste analyzer for a recommendation system.

Available genres in our catalog: {", ".join(CATALOG_GENRES)}
Available moods in our catalog: {", ".join(CATALOG_MOODS)}

Numeric fields use these scales:
- energy: 0.0 = barely audible ambient, 1.0 = full blast metal
- valence: 0.0 = dark/sad, 1.0 = bright/happy
- danceability: 0.0 = still/ambient, 1.0 = made to dance
- acousticness: 0.0 = fully electronic, 1.0 = fully acoustic
- tempo_bpm: 40 (very slow) to 200 (very fast)

User query: "{user_query}"

Pick the single best matching genre and mood from the catalog lists above.
Respond with a JSON object only — no markdown, no extra text:
{{
  "favorite_genre": "<genre from catalog>",
  "favorite_mood": "<mood from catalog>",
  "target_energy": <float 0.0-1.0>,
  "target_valence": <float 0.0-1.0>,
  "target_danceability": <float 0.0-1.0>,
  "target_acousticness": <float 0.0-1.0>,
  "target_tempo_bpm": <integer>,
  "likes_acoustic": <true or false>,
  "reasoning": "<one sentence: how you interpreted the query>"
}}"""

    raw = _call(prompt)
    # Strip markdown code fences if Gemini wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    reasoning = data.pop("reasoning", "No reasoning provided.")
    return data, reasoning


def diversify_results(
    candidates: List[Tuple[Dict, float, str]],
    user_query: str,
    k: int = 5,
) -> Tuple[List[Tuple[Dict, float, str]], str]:
    """
    Step 3: Re-rank top candidates for variety.

    The scorer ranks purely by numeric score — this step prevents the top-k
    from being dominated by one genre or artist. Gemini selects k indices
    from the candidates list, optimising for both score and diversity.

    Returns (selected_candidates, reasoning_string).
    """
    candidate_info = [
        {
            "index": i,
            "title": song["title"],
            "artist": song["artist"],
            "genre": song["genre"],
            "mood": song["mood"],
            "score": round(score, 2),
        }
        for i, (song, score, _) in enumerate(candidates)
    ]

    prompt = f"""You are a music curator selecting a diverse playlist.

User request: "{user_query}"

Scored candidates (higher score = better match to stated preferences):
{json.dumps(candidate_info, indent=2)}

Select exactly {k} songs that best serve this user. Prioritise high scores,
but avoid selecting 3 or more songs of the same genre, and avoid 2 or more
songs by the same artist. Variety makes the playlist more useful.

Respond with JSON only — no markdown, no extra text:
{{"selected_indices": [<exactly {k} integers from the index field above>], "reasoning": "<one sentence>"}}"""

    raw = _call(prompt)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())

    indices = result["selected_indices"][:k]
    selected = [candidates[i] for i in indices if i < len(candidates)]

    # Fallback: if Gemini returned too few valid indices, pad from remaining candidates
    if len(selected) < k:
        used = set(indices)
        for i, c in enumerate(candidates):
            if len(selected) >= k:
                break
            if i not in used:
                selected.append(c)

    return selected, result.get("reasoning", "Diversity selection applied.")


def generate_explanation(
    user_query: str,
    recommendations: List[Tuple[Dict, float, str]],
) -> str:
    """
    Step 4: Write a personalized explanation that references the user's words
    and the actual song titles — not a generic template.
    """
    rec_lines = [
        f"#{i + 1}: \"{song['title']}\" by {song['artist']} "
        f"({song['genre']}, {song['mood']}, energy={song['energy']:.2f})"
        for i, (song, _, _) in enumerate(recommendations)
    ]

    prompt = f"""You are VibeFinder's AI assistant writing a playlist note.

The user asked for: "{user_query}"

You selected these songs:
{chr(10).join(rec_lines)}

Write 2-3 friendly sentences explaining why this playlist fits their request.
Reference specific song titles and connect them to the user's exact words.
Do not use lists or headers — just flowing sentences."""

    return _call(prompt)
