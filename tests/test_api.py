"""
Test suite for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy

# Create a test client
client = TestClient(app)

# Store original activities for reset between tests
original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static_html(self):
        """Test that root endpoint redirects to static HTML page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_success(self):
        """Test getting all activities returns correct data"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_contains_expected_activities(self):
        """Test that response contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        # Check for some expected activities
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        email = "test@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        email = "test@mergington.edu"
        activity_name = "NonExistent Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_registration(self):
        """Test that duplicate registration is prevented"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_with_url_encoded_activity_name(self):
        """Test signup with URL-encoded activity name"""
        email = "test@mergington.edu"
        activity_name = "Programming Class"
        encoded_activity = "Programming%20Class"
        
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify the participant was added to the correct activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_with_special_characters_in_email(self):
        """Test signup with email containing special characters"""
        email = "test.user.name@mergington.edu"  # Use dots instead of + which gets URL decoded
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Verify the participant is initially registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
        
        # Unregister the participant
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity"""
        email = "test@mergington.edu"
        activity_name = "NonExistent Club"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_unregister_participant_not_registered(self):
        """Test unregister when participant is not registered"""
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_with_url_encoded_activity_name(self):
        """Test unregister with URL-encoded activity name"""
        email = "emma@mergington.edu"  # Already in Programming Class
        activity_name = "Programming Class"
        encoded_activity = "Programming%20Class"
        
        response = client.delete(f"/activities/{encoded_activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]


class TestEndToEndScenarios:
    """End-to-end test scenarios"""
    
    def test_complete_signup_and_unregister_flow(self):
        """Test complete flow: signup -> verify -> unregister -> verify"""
        email = "e2e@mergington.edu"
        activity_name = "Chess Club"
        
        # Initial state - participant should not be registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        initial_participants = activities_data[activity_name]["participants"].copy()
        assert email not in initial_participants
        
        # Step 1: Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Step 2: Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == len(initial_participants) + 1
        
        # Step 3: Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Step 4: Verify unregistration
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == len(initial_participants)
    
    def test_multiple_activities_signup(self):
        """Test signing up for multiple activities"""
        email = "multi@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Sign up for multiple activities
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify participant is in all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity in activities_to_join:
            assert email in activities_data[activity]["participants"]
    
    def test_activity_capacity_tracking(self):
        """Test that participant counts are tracked correctly"""
        activity_name = "Chess Club"
        
        # Get initial state
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        initial_count = len(activities_data[activity_name]["participants"])
        max_participants = activities_data[activity_name]["max_participants"]
        
        # Add a new participant
        new_email = "capacity@mergington.edu"
        signup_response = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        assert signup_response.status_code == 200
        
        # Verify count increased
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        new_count = len(activities_data[activity_name]["participants"])
        assert new_count == initial_count + 1
        
        # Verify max_participants remains unchanged
        assert activities_data[activity_name]["max_participants"] == max_participants


class TestErrorHandling:
    """Tests for error handling and edge cases"""
    
    def test_missing_email_parameter(self):
        """Test signup without email parameter"""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup")
        assert response.status_code == 422  # Unprocessable Entity for missing required parameter
    
    def test_empty_email_parameter(self):
        """Test signup with empty email"""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email=")
        # Current API accepts empty emails, but this could be improved in the future
        assert response.status_code == 200