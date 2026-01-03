#!/usr/bin/env python3
"""
Sample data population script for Creator Support AI.
This script uploads sample course content and FAQ to test the system.
"""

import requests
import os
from pathlib import Path

API_URL = os.getenv('API_URL', 'http://localhost:8000')
CREATOR_ID = "demo-creator-123"

def upload_file(file_path, content_type, title):
    """Upload a file to the API."""

    print(f"\nUploading: {title}")
    print(f"File: {file_path}")
    print(f"Type: {content_type}")

    url = f"{API_URL}/upload/content"

    with open(file_path, 'rb') as f:
        files = {
            'file': (Path(file_path).name, f, 'text/plain')
        }
        data = {
            'creator_id': CREATOR_ID,
            'content_type': content_type,
            'title': title
        }

        try:
            response = requests.post(url, files=files, data=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            print(f"✓ Success!")
            print(f"  Chunks created: {result.get('chunks_created', 'N/A')}")
            print(f"  Status: {result.get('status', 'unknown')}")
            return True

        except requests.exceptions.ConnectionError:
            print("✗ Error: Could not connect to API")
            print(f"  Make sure the backend is running at {API_URL}")
            return False

        except requests.exceptions.Timeout:
            print("✗ Error: Request timed out")
            print("  Large files may take longer to process")
            return False

        except requests.exceptions.HTTPError as e:
            print(f"✗ Error: HTTP {e.response.status_code}")
            print(f"  {e.response.text}")
            return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


def test_chat(question):
    """Test the chat endpoint with a question."""

    print(f"\nTesting chat: '{question}'")

    url = f"{API_URL}/chat"
    payload = {
        'message': question,
        'creator_id': CREATOR_ID
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        print(f"✓ Response received")
        print(f"  Answer: {result['response'][:150]}...")
        print(f"  Sources: {len(result.get('sources', []))} sources cited")
        print(f"  Should escalate: {result.get('should_escalate', False)}")
        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def check_api_health():
    """Check if the API is running."""

    print("Checking API health...")

    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        print(f"✓ API is running at {API_URL}")
        return True
    except Exception as e:
        print(f"✗ API is not responding at {API_URL}")
        print(f"  Error: {str(e)}")
        print("\n  Make sure the backend is running:")
        print("  cd backend")
        print("  python main.py")
        return False


def main():
    """Main function to populate sample data."""

    print("=" * 60)
    print("Creator Support AI - Sample Data Population")
    print("=" * 60)

    # Check if API is running
    if not check_api_health():
        return

    print(f"\nCreator ID: {CREATOR_ID}")
    print(f"API URL: {API_URL}")

    # Define sample files
    sample_dir = Path(__file__).parent / 'sample_data'

    files_to_upload = [
        {
            'path': sample_dir / 'sample_course_content.txt',
            'type': 'text',
            'title': 'Module 1: Introduction to Python'
        },
        {
            'path': sample_dir / 'sample_faq.txt',
            'type': 'text',
            'title': 'Course FAQ'
        }
    ]

    # Check if sample files exist
    for file_info in files_to_upload:
        if not file_info['path'].exists():
            print(f"\n✗ Sample file not found: {file_info['path']}")
            print("  Please ensure sample_data directory exists with sample files.")
            return

    print("\n" + "-" * 60)
    print("Uploading Sample Content")
    print("-" * 60)

    # Upload each file
    success_count = 0
    for file_info in files_to_upload:
        if upload_file(file_info['path'], file_info['type'], file_info['title']):
            success_count += 1

    print("\n" + "-" * 60)
    print(f"Upload Summary: {success_count}/{len(files_to_upload)} files uploaded")
    print("-" * 60)

    if success_count == 0:
        print("\n✗ No files were uploaded successfully.")
        return

    # Wait a moment for indexing
    print("\nWaiting for content to be indexed...")
    import time
    time.sleep(3)

    # Test with sample questions
    print("\n" + "-" * 60)
    print("Testing Chat Functionality")
    print("-" * 60)

    test_questions = [
        "What is Python?",
        "How do I access the course?",
        "What's covered in Module 1?",
        "Can I get a refund?",
        "Do I need prior experience?"
    ]

    for question in test_questions:
        test_chat(question)

    print("\n" + "=" * 60)
    print("Sample Data Population Complete!")
    print("=" * 60)

    print("\nNext steps:")
    print("1. Visit http://localhost:3000/demo to test the chat interface")
    print("2. Visit http://localhost:3000/dashboard to view conversations")
    print(f"3. Use creator ID: {CREATOR_ID} when testing")

    print("\nSample questions to try:")
    for q in test_questions:
        print(f"  • {q}")

    print("\nEnjoy testing Creator Support AI! 🚀")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
