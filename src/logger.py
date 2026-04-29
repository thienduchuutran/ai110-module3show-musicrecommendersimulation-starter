"""
Session logging and preference guardrails for VibeFinder.

Every pipeline run writes a JSON session file under logs/ so that any
recommendation can be fully replayed and debugged after the fact.
The validate_preferences() guardrail prevents out-of-range AI-generated
values from silently corrupting the scorer's arithmetic.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(_LOG_DIR, "vibefinder.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("vibefinder")


def log_session(session_data: Dict[str, Any]) -> str:
    """Write a full pipeline session to a JSON file. Returns the file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(_LOG_DIR, f"session_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    return path


_FLOAT_FIELDS = ["target_energy", "target_valence", "target_danceability", "target_acousticness"]
_REQUIRED_FIELDS = ["favorite_genre", "favorite_mood", "target_energy", "likes_acoustic"]


def validate_preferences(prefs: Dict) -> Dict:
    """
    Clamp numeric preferences to valid ranges and fill missing required fields.
    Logs a warning for every correction so problems are visible in the log.
    """
    corrections: List[str] = []

    for field in _FLOAT_FIELDS:
        if field in prefs:
            clamped = max(0.0, min(1.0, float(prefs[field])))
            if clamped != prefs[field]:
                corrections.append(f"{field}: {prefs[field]} → {clamped}")
            prefs[field] = clamped

    if "target_tempo_bpm" in prefs:
        clamped = max(40, min(220, int(prefs["target_tempo_bpm"])))
        if clamped != prefs.get("target_tempo_bpm"):
            corrections.append(f"target_tempo_bpm: {prefs['target_tempo_bpm']} → {clamped}")
        prefs["target_tempo_bpm"] = clamped

    if "likes_acoustic" in prefs and not isinstance(prefs["likes_acoustic"], bool):
        prefs["likes_acoustic"] = bool(prefs["likes_acoustic"])

    for field in _REQUIRED_FIELDS:
        if field not in prefs:
            corrections.append(f"{field} missing — using default")
            defaults = {
                "favorite_genre": "",
                "favorite_mood": "",
                "target_energy": 0.5,
                "likes_acoustic": False,
            }
            prefs[field] = defaults[field]

    if corrections:
        logger.warning("Preference guardrails applied: %s", "; ".join(corrections))

    return prefs
