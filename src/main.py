"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("../data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Taste profile: a focused late-night lofi listener who studies to music.
    # Values mirror song attribute ranges in data/songs.csv so the recommender
    # can compare categorical fields (genre, mood) and numeric fields (0.0–1.0).
    user_prefs = {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.4,
        "target_valence": 0.6,
        "target_danceability": 0.55,
        "target_acousticness": 0.8,
        "target_tempo_bpm": 80,
        "likes_acoustic": True,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print()
    print("=" * 60)
    print(f"{'TOP ' + str(len(recommendations)) + ' RECOMMENDATIONS':^60}")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        title = f"{song['title']} - {song['artist']}"
        print(f"\n#{rank}  {title}")
        print(f"    Score: {score:.2f}")
        print(f"    Reasons:")
        for reason in explanation.split("; "):
            print(f"      - {reason}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
