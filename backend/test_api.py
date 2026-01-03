import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_check():
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_root_endpoint():
    print("\nTesting root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    print("✅ Root endpoint passed")

def test_chat_endpoint():
    print("\nTesting chat endpoint...")
    payload = {
        "message": "What is this about?",
        "creator_id": "test-creator-123"
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "sources" in data
    print(f"✅ Chat endpoint passed")
    print(f"   Response: {data['response'][:100]}...")

def test_upload_content():
    print("\nTesting content upload...")

    test_content = """
    Module 1: Introduction to Python

    Python is a high-level programming language. Key features include:
    - Easy to learn syntax
    - Dynamic typing
    - Large standard library
    - Cross-platform compatibility

    In this module, we cover variables, data types, and basic operations.
    """

    files = {
        'file': ('test_module.txt', test_content, 'text/plain')
    }
    data = {
        'creator_id': 'test-creator-123',
        'content_type': 'text',
        'title': 'Module 1: Introduction'
    }

    try:
        response = requests.post(f"{BASE_URL}/upload/content", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Content upload passed")
            print(f"   Chunks created: {result.get('chunks_created', 'N/A')}")
        else:
            print(f"❌ Content upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Content upload error: {str(e)}")

def test_chat_with_context():
    print("\nTesting chat with uploaded content...")
    time.sleep(2)

    payload = {
        "message": "What did you cover in Module 1?",
        "creator_id": "test-creator-123"
    }

    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat with context passed")
            print(f"   Response: {data['response'][:200]}...")
            print(f"   Sources: {data['sources']}")
        else:
            print(f"❌ Chat failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")

def test_conversations_endpoint():
    print("\nTesting conversations endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/conversations/test-creator-123")
        if response.status_code == 200:
            data = response.json()
            conversations = data.get("conversations", [])
            print(f"✅ Conversations endpoint passed")
            print(f"   Total conversations: {len(conversations)}")
        else:
            print(f"❌ Conversations failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Conversations error: {str(e)}")

def run_all_tests():
    print("=" * 60)
    print("Creator Support AI - API Tests")
    print("=" * 60)

    try:
        test_health_check()
        test_root_endpoint()
        test_chat_endpoint()
        test_upload_content()
        test_chat_with_context()
        test_conversations_endpoint()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to the API.")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    run_all_tests()
