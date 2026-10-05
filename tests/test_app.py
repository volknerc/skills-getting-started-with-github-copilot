from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_NAME = "Chess Club"
ACTIVITY_URL = f"/activities/{quote(ACTIVITY_NAME, safe='')}"
EXISTING_EMAIL = "existing@mergington.edu"


@pytest.fixture
def activity_data(monkeypatch):
    test_activities = {
        ACTIVITY_NAME: {
            "description": "Practice chess",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": [EXISTING_EMAIL],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return test_activities


@pytest.fixture
def client(activity_data):
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client, activity_data):
    # Arrange
    expected_activities = activity_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post(f"{ACTIVITY_URL}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}."}
    assert email in activity_data[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_without_changing_participants(client, activity_data):
    # Arrange
    participants_before = activity_data[ACTIVITY_NAME]["participants"].copy()

    # Act
    response = client.post(
        f"{ACTIVITY_URL}/signup", params={"email": EXISTING_EMAIL}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity."
    }
    assert activity_data[ACTIVITY_NAME]["participants"] == participants_before


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post(
        "/activities/Unknown/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    email = EXISTING_EMAIL
    participant_url = f"{ACTIVITY_URL}/participants/{quote(email, safe='')}"

    # Act
    response = client.delete(participant_url)

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {ACTIVITY_NAME}."
    }
    assert email not in activity_data[ACTIVITY_NAME]["participants"]


def test_unregister_returns_not_found_for_absent_participant(client):
    # Arrange
    email = "absent@mergington.edu"
    participant_url = f"{ACTIVITY_URL}/participants/{quote(email, safe='')}"

    # Act
    response = client.delete(participant_url)

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity."
    }


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    email = "student@mergington.edu"
    participant_url = f"/activities/Unknown/participants/{quote(email, safe='')}"

    # Act
    response = client.delete(participant_url)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}