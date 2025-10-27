"""
Simple API test script
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    """Test the API endpoints"""
    print("Testing Quatre-Vingt Backend API...")
    
    try:
        # Test root endpoint
        print("\n1. Testing root endpoint...")
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test health endpoint
        print("\n2. Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test game rooms endpoint
        print("\n3. Testing game rooms endpoint...")
        response = requests.get(f"{BASE_URL}/api/game/rooms")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test creating a room
        print("\n4. Testing create room...")
        response = requests.post(f"{BASE_URL}/api/game/rooms", params={"name": "Test Room"})
        print(f"Status: {response.status_code}")
        room_data = response.json()
        print(f"Response: {room_data}")
        
        if response.status_code == 200:
            room_id = room_data["id"]
            
            # Test joining the room
            print(f"\n5. Testing join room {room_id}...")
            response = requests.post(f"{BASE_URL}/api/game/rooms/{room_id}/join", params={"player_name": "Test Player"})
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Test getting the room
            print(f"\n6. Testing get room {room_id}...")
            response = requests.get(f"{BASE_URL}/api/game/rooms/{room_id}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        
        print("\nAll tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Connection failed. Make sure the server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
