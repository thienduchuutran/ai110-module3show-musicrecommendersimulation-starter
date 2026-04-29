"""
VibeFinder 2.0 — AI-powered music recommender.

Pipeline (each step's output feeds the next):
  1. Claude extracts structured preferences from the user's natural language query
  2. Existing scorer (recommend_songs) scores all songs against those preferences
  3. Claude re-ranks top candidates for genre/artist diversity
  4. Claude writes a personalized explanation referencing the user's own words
  5. Full session is saved to logs/ as a JSON file for replay and debugging
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()


sys.path.insert(0, os.path.dirname(__file__))

from agent import extract_preferences, diversify_results, generate_explanation
from logger import log_session, logger, validate_preferences
from recommender import load_songs, recommend_songs


def run_pipeline(user_query: str, songs: list, k: int = 5) -> tuple:
    """
    Execute the 4-step agentic pipeline for one user query.
    Returns (session_dict, final_recommendations, explanation_text).
    """
    session = {"query": user_query, "steps": {}}

    # ── Step 1: Understand the query ────────────────────────────────────────
    print("\n[Step 1] Understanding your request...")
    logger.info("Step 1 — extracting preferences for: '%s'", user_query)

    raw_prefs, reasoning = extract_preferences(user_query)
    prefs = validate_preferences(raw_prefs)

    session["steps"]["extraction"] = {"prefs": prefs, "reasoning": reasoning}
    print(f"         Heard as: {prefs['favorite_genre']} / {prefs['favorite_mood']}, "
          f"energy={prefs['target_energy']:.2f}, acoustic={prefs['likes_acoustic']}")
    print(f"         Why: {reasoning}")

    # ── Step 2: Score all songs (existing scorer, wider net) ─────────────────
    print("\n[Step 2] Scoring all songs...")
    logger.info("Step 2 — scoring %d songs", len(songs))

    # Fetch k*2 candidates so Step 3 has room to pick for diversity
    candidates = recommend_songs(prefs, songs, k=k * 2)

    session["steps"]["scoring"] = {
        "candidates": [
            {"title": s["title"], "artist": s["artist"], "score": round(sc, 2)}
            for s, sc, _ in candidates
        ]
    }
    score_range = f"{candidates[0][1]:.2f} → {candidates[-1][1]:.2f}"
    print(f"         {len(candidates)} candidates scored ({score_range})")

    # ── Step 3: Diversity re-rank ────────────────────────────────────────────
    print("\n[Step 3] Selecting a diverse top-5...")
    logger.info("Step 3 — diversity re-ranking")

    final_recs, diversity_reasoning = diversify_results(candidates, user_query, k=k)

    session["steps"]["diversity"] = {"reasoning": diversity_reasoning}
    print(f"         {diversity_reasoning}")

    # ── Step 4: Personalized explanation ─────────────────────────────────────
    print("\n[Step 4] Writing your playlist note...")
    logger.info("Step 4 — generating explanation")

    explanation = generate_explanation(user_query, final_recs)
    session["steps"]["explanation"] = explanation

    session["final_recommendations"] = [
        {
            "title": s["title"],
            "artist": s["artist"],
            "genre": s["genre"],
            "mood": s["mood"],
            "score": round(sc, 2),
        }
        for s, sc, _ in final_recs
    ]

    return session, final_recs, explanation


def display_results(recommendations: list, explanation: str) -> None:
    print("\n" + "=" * 60)
    print(f"{'YOUR PERSONALIZED PLAYLIST':^60}")
    print("=" * 60)
    print(f"\n{explanation}\n")
    print("-" * 60)

    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        title = f"{song['title']} - {song['artist']}"
        print(f"\n#{rank}  {title}")
        print(f"    [{song['genre']} / {song['mood']}]  Score: {score:.2f}")
        for reason in reasons.split("; "):
            print(f"      - {reason}")

    print("\n" + "=" * 60)


def main() -> None:
    songs = load_songs("../data/songs.csv")
    logger.info("VibeFinder 2.0 started — %d songs loaded", len(songs))

    print("=" * 60)
    print(f"{'VIBEFINDER 2.0 — AI Music Recommender':^60}")
    print("=" * 60)
    print("\nDescribe the music you want in plain English.")
    print('Examples: "calm music for late-night coding"')
    print('          "upbeat songs to work out to"')
    print('          "sad acoustic songs for a rainy day"')
    print("\nType 'quit' to exit.\n")

    while True:
        try:
            user_query = input("What are you in the mood for? > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not user_query:
            print("Please describe what you're looking for.")
            continue

        try:
            session, recommendations, explanation = run_pipeline(user_query, songs)
            display_results(recommendations, explanation)

            log_path = log_session(session)
            logger.info("Session saved → %s", log_path)

        except Exception as exc:
            logger.error("Pipeline error: %s", exc, exc_info=True)
            print(f"\nSomething went wrong: {exc}")
            print("Try rephrasing your request.\n")
            continue

        print()


if __name__ == "__main__":
    main()
