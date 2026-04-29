"""
System evaluation: two modes in one script.

Mode 1 — Adversarial scorer profiles (original):
  Stress-tests score_song() / recommend_songs() with edge-case preference dicts
  to verify the scorer never crashes and produces sensible output on bad input.

Mode 2 — NL extraction test harness (new):
  Verifies that extract_preferences() maps natural language queries to structured
  preferences that are semantically correct. Each test case specifies expected
  conditions; the harness prints a pass/fail table and exit-code 1 on failure.

Run scorer stress-test:   python evaluate.py
Run NL extraction tests:  python evaluate.py --nl
Run both:                 python evaluate.py --all
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from recommender import load_songs, recommend_songs

# ── Mode 1: Adversarial scorer profiles (unchanged) ─────────────────────────

ADVERSARIAL_PROFILES = [
    {
        "name": "Conflicting: high energy + sad mood",
        "note": "Mood 'sad' doesn't exist in data; energy pushes toward intense tracks.",
        "prefs": {
            "favorite_genre": "pop",
            "favorite_mood": "sad",
            "target_energy": 0.9,
            "likes_acoustic": False,
        },
    },
    {
        "name": "Conflicting: chill mood + max energy",
        "note": "Mood wants calm, energy wants peak — scoring may reward both at once.",
        "prefs": {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 1.0,
            "likes_acoustic": True,
        },
    },
    {
        "name": "Unknown genre",
        "note": "Genre 'polka' is not in the dataset — should not break scoring.",
        "prefs": {
            "favorite_genre": "polka",
            "favorite_mood": "happy",
            "target_energy": 0.5,
            "likes_acoustic": False,
        },
    },
    {
        "name": "Out-of-range energy",
        "note": "target_energy=2.0 is outside [0,1]; (1 - diff) goes negative and is filtered.",
        "prefs": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 2.0,
            "likes_acoustic": False,
        },
    },
    {
        "name": "Everything-neutral user",
        "note": "Generic midpoint energy with unknown genre/mood — tests tie-breaking.",
        "prefs": {
            "favorite_genre": "",
            "favorite_mood": "",
            "target_energy": 0.5,
            "likes_acoustic": False,
        },
    },
    {
        "name": "Acoustic lover but wants rock",
        "note": "Rock songs tend to have low acousticness; preferences pull in opposite directions.",
        "prefs": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.9,
            "likes_acoustic": True,
        },
    },
]


def run_scorer_profile(profile: dict, songs: list) -> None:
    print("\n" + "=" * 60)
    print(f"PROFILE: {profile['name']}")
    print(f"NOTE:    {profile['note']}")
    print(f"PREFS:   {profile['prefs']}")
    print("-" * 60)

    recs = recommend_songs(profile["prefs"], songs, k=5)
    for rank, (song, score, explanation) in enumerate(recs, start=1):
        print(
            f"#{rank}  {song['title']} - {song['artist']}  "
            f"[{song['genre']}/{song['mood']}  "
            f"energy={song['energy']}  acoustic={song['acousticness']}]"
        )
        print(f"    Score: {score:.2f}  |  {explanation}")


def run_scorer_evaluation(songs: list) -> None:
    print("\n" + "=" * 60)
    print("MODE 1: ADVERSARIAL SCORER PROFILES")
    print("=" * 60)
    for profile in ADVERSARIAL_PROFILES:
        run_scorer_profile(profile, songs)
    print("\n" + "=" * 60)


# ── Mode 2: NL extraction test harness ──────────────────────────────────────

# Each test case: a natural language query + a dict of conditions to verify.
# Condition keys:
#   energy_max / energy_min      — target_energy must be ≤ / ≥ threshold
#   acousticness_min             — target_acousticness must be ≥ threshold
#   likes_acoustic               — must equal True or False
#   mood_in                      — favorite_mood must be one of the listed values
#   genre_in                     — favorite_genre must be one of the listed values

NL_TEST_CASES = [
    {
        "query": "calm music for late-night studying",
        "checks": {
            "energy_max": 0.55,
            "mood_in": ["chill", "focused", "peaceful", "relaxed"],
        },
    },
    {
        "query": "high energy workout music",
        "checks": {
            "energy_min": 0.65,
            "mood_in": ["energetic", "intense", "uplifting", "happy"],
        },
    },
    {
        "query": "sad acoustic folk songs for a rainy day",
        "checks": {
            "likes_acoustic": True,
            "acousticness_min": 0.5,
            "genre_in": ["folk", "country", "indie pop", "classical"],
        },
    },
    {
        "query": "jazz for a coffee shop morning",
        "checks": {
            "genre_in": ["jazz", "lofi", "folk", "classical"],
            "energy_max": 0.65,
        },
    },
    {
        "query": "angry metal to let off steam",
        "checks": {
            "energy_min": 0.75,
            "genre_in": ["metal", "rock", "electronic"],
            "mood_in": ["angry", "intense", "energetic"],
        },
    },
    {
        "query": "romantic dinner background music",
        "checks": {
            "energy_max": 0.65,
            "mood_in": ["romantic", "relaxed", "peaceful", "chill", "nostalgic"],
        },
    },
]


def _check_extraction(prefs: dict, checks: dict) -> list[str]:
    """Return list of failure messages. Empty list means all checks passed."""
    failures = []

    if "energy_max" in checks and prefs.get("target_energy", 1.0) > checks["energy_max"]:
        failures.append(
            f"energy {prefs['target_energy']:.2f} > expected max {checks['energy_max']}"
        )

    if "energy_min" in checks and prefs.get("target_energy", 0.0) < checks["energy_min"]:
        failures.append(
            f"energy {prefs['target_energy']:.2f} < expected min {checks['energy_min']}"
        )

    if "acousticness_min" in checks and prefs.get("target_acousticness", 0.0) < checks["acousticness_min"]:
        failures.append(
            f"acousticness {prefs['target_acousticness']:.2f} < expected min {checks['acousticness_min']}"
        )

    if "likes_acoustic" in checks and prefs.get("likes_acoustic") != checks["likes_acoustic"]:
        failures.append(
            f"likes_acoustic={prefs.get('likes_acoustic')} != expected {checks['likes_acoustic']}"
        )

    if "mood_in" in checks and prefs.get("favorite_mood") not in checks["mood_in"]:
        failures.append(
            f"mood '{prefs.get('favorite_mood')}' not in {checks['mood_in']}"
        )

    if "genre_in" in checks and prefs.get("favorite_genre") not in checks["genre_in"]:
        failures.append(
            f"genre '{prefs.get('favorite_genre')}' not in {checks['genre_in']}"
        )

    return failures


def run_nl_evaluation() -> bool:
    """
    Run NL extraction tests. Returns True if all pass, False if any fail.
    Calls Claude for each test case — expect ~10-15 seconds total.
    """
    from agent import extract_preferences, CATALOG_GENRES, CATALOG_MOODS
    from logger import validate_preferences

    print("\n" + "=" * 60)
    print("MODE 2: NL PREFERENCE EXTRACTION TEST HARNESS")
    print(f"        {len(NL_TEST_CASES)} test cases — calling Claude for each")
    print("=" * 60)

    passed = 0
    failed = 0
    results = []

    for i, case in enumerate(NL_TEST_CASES, start=1):
        query = case["query"]
        checks = case["checks"]

        print(f"\n[{i}/{len(NL_TEST_CASES)}] \"{query}\"")

        try:
            raw_prefs, reasoning = extract_preferences(query)
            prefs = validate_preferences(raw_prefs)

            print(f"         → genre={prefs['favorite_genre']}, "
                  f"mood={prefs['favorite_mood']}, "
                  f"energy={prefs['target_energy']:.2f}, "
                  f"acoustic={prefs['likes_acoustic']}")
            print(f"         → reasoning: {reasoning}")

            failures = _check_extraction(prefs, checks)

            if failures:
                failed += 1
                status = "FAIL"
                for f in failures:
                    print(f"         ✗ {f}")
            else:
                passed += 1
                status = "PASS"
                print("         ✓ all checks passed")

            results.append({"query": query, "status": status, "prefs": prefs, "failures": failures})

        except Exception as exc:
            failed += 1
            print(f"         ✗ ERROR: {exc}")
            results.append({"query": query, "status": "ERROR", "error": str(exc)})

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(NL_TEST_CASES)} tests")
    print("=" * 60)

    return failed == 0


def main() -> None:
    songs = load_songs("../data/songs.csv")
    print(f"Loaded {len(songs)} songs")

    args = sys.argv[1:]
    run_scorer = "--nl" not in args or "--all" in args
    run_nl = "--nl" in args or "--all" in args

    if not args:
        run_scorer = True
        run_nl = False

    all_passed = True

    if run_scorer:
        run_scorer_evaluation(songs)

    if run_nl:
        all_passed = run_nl_evaluation()

    if run_nl and not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
