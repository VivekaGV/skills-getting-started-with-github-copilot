import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the global activities dict after each test to avoid state bleed."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


def test_get_activities():
    """Test that GET /activities returns the activity data."""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success():
    """Test successful signup for an activity."""
    response = client.post("/activities/Chess Club/signup?email=test@example.com")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "test@example.com" in result["message"]
    assert "Chess Club" in result["message"]

    # Verify the participant was added
    response = client.get("/activities")
    data = response.json()
    assert "test@example.com" in data["Chess Club"]["participants"]


def test_signup_duplicate():
    """Test that signing up a duplicate participant returns 400."""
    # First signup
    client.post("/activities/Chess Club/signup?email=duplicate@example.com")
    # Second signup should fail
    response = client.post("/activities/Chess Club/signup?email=duplicate@example.com")
    assert response.status_code == 400
    result = response.json()
    assert "detail" in result
    assert "already signed up" in result["detail"]


def test_signup_nonexistent_activity():
    """Test signup for a non-existent activity returns 404."""
    response = client.post("/activities/NonExistent Activity/signup?email=test@example.com")
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "Activity not found" in result["detail"]


def test_unregister_success():
    """Test successful unregister from an activity."""
    # First signup
    client.post("/activities/Chess Club/signup?email=unregister@example.com")
    # Then unregister
    response = client.delete("/activities/Chess Club/participants?email=unregister@example.com")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "unregister@example.com" in result["message"]
    assert "Chess Club" in result["message"]

    # Verify the participant was removed
    response = client.get("/activities")
    data = response.json()
    assert "unregister@example.com" not in data["Chess Club"]["participants"]


def test_unregister_missing_participant():
    """Test unregistering a non-existent participant returns 404."""
    response = client.delete("/activities/Chess Club/participants?email=missing@example.com")
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "Participant not found" in result["detail"]


def test_unregister_nonexistent_activity():
    """Test unregister from a non-existent activity returns 404."""
    response = client.delete("/activities/NonExistent Activity/participants?email=test@example.com")
    assert response.status_code == 404
    result = response.json()
    assert "detail" in result
    assert "Activity not found" in result["detail"]