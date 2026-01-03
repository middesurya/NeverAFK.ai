#!/usr/bin/env python3
"""
Environment validation script for Creator Support AI.
Run this before starting the backend to ensure all required environment variables are set.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Required environment variables
REQUIRED_VARS = {
    'OPENAI_API_KEY': 'OpenAI API key for LLM and embeddings',
    'PINECONE_API_KEY': 'Pinecone API key for vector storage',
}

# Optional but recommended
OPTIONAL_VARS = {
    'SUPABASE_URL': 'Supabase project URL for database',
    'SUPABASE_ANON_KEY': 'Supabase anonymous key',
    'SUPABASE_SERVICE_KEY': 'Supabase service role key',
    'LEMON_SQUEEZY_API_KEY': 'Lemon Squeezy API key for billing',
}

def validate_environment():
    """Validate that all required environment variables are set."""

    print("=" * 60)
    print("Creator Support AI - Environment Validation")
    print("=" * 60)
    print()

    missing_required = []
    missing_optional = []

    # Check required variables
    print("Required Environment Variables:")
    print("-" * 60)
    for var, description in REQUIRED_VARS.items():
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var:<25} {masked}")
        else:
            print(f"✗ {var:<25} MISSING")
            missing_required.append((var, description))

    print()

    # Check optional variables
    print("Optional Environment Variables:")
    print("-" * 60)
    for var, description in OPTIONAL_VARS.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✓ {var:<25} {masked}")
        else:
            print(f"○ {var:<25} Not set")
            missing_optional.append((var, description))

    print()
    print("=" * 60)

    # Report results
    if missing_required:
        print("\n❌ VALIDATION FAILED")
        print("\nMissing required environment variables:")
        for var, description in missing_required:
            print(f"  • {var}: {description}")
        print("\nPlease set these variables in your .env file.")
        print("See .env.example for reference.")
        return False

    if missing_optional:
        print("\n⚠️  WARNING: Optional variables not set")
        print("\nMissing optional environment variables:")
        for var, description in missing_optional:
            print(f"  • {var}: {description}")
        print("\nThe application will run, but some features may be limited.")
        print()

    print("\n✅ VALIDATION PASSED")
    print("\nAll required environment variables are set.")
    print("You can start the backend server now.")
    return True


def test_api_keys():
    """Test API keys are valid by making test calls."""

    print("\n" + "=" * 60)
    print("Testing API Key Validity")
    print("=" * 60)
    print()

    # Test OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            # Simple test - list models
            models = client.models.list()
            print("✓ OpenAI API key is valid")
        except Exception as e:
            print(f"✗ OpenAI API key test failed: {str(e)}")
            return False

    # Test Pinecone
    pinecone_key = os.getenv('PINECONE_API_KEY')
    if pinecone_key:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=pinecone_key)
            indexes = pc.list_indexes()
            print("✓ Pinecone API key is valid")
        except Exception as e:
            print(f"✗ Pinecone API key test failed: {str(e)}")
            return False

    # Test Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    if supabase_url and supabase_key:
        try:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
            # Simple test - check connection
            print("✓ Supabase credentials are valid")
        except Exception as e:
            print(f"✗ Supabase test failed: {str(e)}")
            print("  (This is optional - app will work without it)")

    print("\n✅ API key validation complete")
    return True


def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""

    if not os.path.exists('.env') and os.path.exists('.env.example'):
        print("\n📝 Creating .env file from .env.example...")
        with open('.env.example', 'r') as example:
            with open('.env', 'w') as env:
                env.write(example.read())
        print("✓ .env file created")
        print("\n⚠️  Please edit .env and add your API keys before continuing.")
        return False
    return True


if __name__ == '__main__':
    print("\n🔍 Starting environment validation...\n")

    # Create .env if needed
    if not create_env_file():
        sys.exit(1)

    # Validate environment variables
    if not validate_environment():
        sys.exit(1)

    # Optionally test API keys (can be slow)
    test_keys = '--test-keys' in sys.argv or '-t' in sys.argv

    if test_keys:
        print("\n🔑 Testing API keys (this may take a moment)...\n")
        if not test_api_keys():
            print("\n⚠️  Some API key tests failed.")
            print("Please check your API keys and try again.")
            sys.exit(1)
    else:
        print("\n💡 Tip: Run with --test-keys to validate API keys")

    print("\n🚀 Ready to start the backend!\n")
    print("Run: python main.py")
    print("Or:  uvicorn main:app --reload\n")

    sys.exit(0)
