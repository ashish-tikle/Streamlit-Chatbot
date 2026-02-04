"""Test Langfuse 3.x connectivity and API"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from langfuse import Langfuse

# Get credentials
public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

print(f"Testing Langfuse connectivity...")
print(f"Host: {host}")
print(f"Public Key: {public_key[:10]}..." if public_key else "Public Key: NOT SET")
print(f"Secret Key: {secret_key[:10]}..." if secret_key else "Secret Key: NOT SET")

try:
    # Initialize client
    print("\n1. Initializing Langfuse client...")
    client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    print("   ✓ Client initialized")

    # Test auth
    print("\n2. Testing authentication...")
    auth_result = client.auth_check()
    print(f"   ✓ Authentication successful: {auth_result}")

    # Create a trace using the correct API
    print("\n3. Creating generation...")

    # Use context manager approach
    generation = client.start_generation(
        name="test_generation",
        model="test-model",
        input=[{"role": "user", "content": "Test input"}],
        output="Test output",
        metadata={"test": "connectivity"},
        usage_details={"input": 10, "output": 5, "total": 15},
        cost_details={"input": 0.001, "output": 0.002, "total": 0.003},
    )
    print(f"   ✓ Generation created")

    # Flush
    print("\n4. Flushing data...")
    client.flush()
    print("   ✓ Data flushed")

    print(f"\n✅ SUCCESS! Check your Langfuse dashboard")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback

    traceback.print_exc()
