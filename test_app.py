import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the frontend HTML loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data # Ensures HTML is actually returned

def test_chat_empty_prompt(client):
    """Test that the backend correctly rejects empty messages"""
    response = client.post('/chat', json={"message": "   "})
    assert response.status_code == 400
    assert b"Prompt cannot be empty" in response.data

@patch('app.client.models.generate_content')
def test_chat_success_and_experiment_cycling(mock_generate, client):
    """Test the chat endpoint mocks the AI and cycles parameters correctly"""
    
    # 1. Setup our "Fake" Google API Response
    mock_response = MagicMock()
    mock_response.text = "This is a fake AI response for testing."
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.candidates_token_count = 20
    mock_response.usage_metadata.total_token_count = 30
    mock_generate.return_value = mock_response

    # 2. Send a fake user message to our Flask app
    response = client.post('/chat', json={"message": "My engine is making a noise."})
    
    # 3. Verify our code processed it correctly
    assert response.status_code == 200
    data = response.get_json()
    
    # Check that our experiment logic worked (it should return 3 results per round)
    assert len(data['results']) == 3
    assert data['query'] == "My engine is making a noise."
    
    # Verify the fake AI text was returned successfully
    assert "This is a fake AI response" in data['results'][0]['text']
    assert "Tokens: Prompt: 10" in data['results'][0]['text']
