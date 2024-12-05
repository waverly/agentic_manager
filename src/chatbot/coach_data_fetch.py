from pathlib import Path
import json


# Data retrieval
def get_team_updates() -> dict:
    """Use this to get the user's competency matrix."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_updates.json"
    with open(json_path) as f:
        return json.load(f)


def get_user_context_data() -> dict:
    """Use this to get the user's employee data."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_user_context.json"
    with open(json_path) as f:
        return json.load(f)


def get_reviews_data() -> dict:
    """Use this to get the user's reviews data."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_reviews_data.json"
    with open(json_path) as f:
        return json.load(f)


def get_feedback_data() -> dict:
    """Use this to get the user's feedback data."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_feedback_data.json"
    with open(json_path) as f:
        return json.load(f)
