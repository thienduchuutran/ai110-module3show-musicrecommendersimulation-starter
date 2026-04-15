"""
System Evaluation: adversarial / edge-case user profiles.

Each profile is designed to stress the scoring logic in recommender.py
and expose weaknesses (conflicting preferences, missing fields, extreme
values, unknown categories, etc.).
"""

from recommender import load_songs, recommend_songs


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


def run_profile(profile, songs):
    print("\n" + "=" * 60)
    print(f"PROFILE: {profile['name']}")
    print(f"NOTE:    {profile['note']}")
    print(f"PREFS:   {profile['prefs']}")
    print("-" * 60)

    recs = recommend_songs(profile["prefs"], songs, k=5)
    for rank, (song, score, explanation) in enumerate(recs, start=1):
        print(f"#{rank}  {song['title']} - {song['artist']}  "
              f"[{song['genre']}/{song['mood']}  "
              f"energy={song['energy']}  acoustic={song['acousticness']}]")
        print(f"    Score: {score:.2f}  |  {explanation}")


def main():
    songs = load_songs("../data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    for profile in ADVERSARIAL_PROFILES:
        run_profile(profile, songs)
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
