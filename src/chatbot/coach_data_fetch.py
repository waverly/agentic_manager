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


def get_org_structure() -> dict:
    """Use this to get the user's org structure."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_org_structure.json"
    with open(json_path) as f:
        return json.load(f)


def get_github_data() -> dict:
    """Use this to get the user's github data."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_github_data.json"
    with open(json_path) as f:
        return json.load(f)


def get_jira_data() -> dict:
    """Use this to get the user's jira data."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_jira_data.json"
    with open(json_path) as f:
        return json.load(f)


def get_calendar_data() -> dict:
    """Use this to get the user's calendar data."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_calendar_data.json"
    with open(json_path) as f:
        return json.load(f)


def get_1_1s() -> dict:
    """Use this to get the user's 1:1s."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_1_1s.json"
    with open(json_path) as f:
        return json.load(f)


def get_competency_matrix() -> dict:
    """Use this to get the user's competency matrix."""
    json_path = Path(__file__).parent.parent / "mocks" / "competency_matrix.json"
    with open(json_path) as f:
        return json.load(f)
