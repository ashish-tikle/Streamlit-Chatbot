"""Test Langfuse API directly to understand input/output handling"""

import os
import json
from datetime import datetime
from langfuse import Langfuse
from langfuse.model import ModelUsage

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)

print("Testing different methods to send input/output to Langfuse...")

# Create a trace
trace = langfuse.trace(
    name="test_api_methods", user_id="test_user", metadata={"test": "api_methods"}
)

print(f"✓ Created trace: {trace.id}")

# Test 1: Create and then update
print("\n--- Test 1: Create generation, then update with input/output ---")
start = datetime.utcnow()
gen1 = trace.generation(
    name="test_update_method",
    model="test-model",
    start_time=start,
    end_time=datetime.utcnow(),
)
print(f"✓ Created generation: {gen1.id}")
print("  Updating with input/output...")
gen1.update(input="This is the input text", output="This is the output text")
print("  ✓ Updated")

# Test 2: Try using the internal API client directly
print("\n--- Test 2: Using low-level API ---")
try:
    start = datetime.utcnow()
    end = datetime.utcnow()

    # Access the internal client
    from langfuse.api.resources.ingestion.types import (
        CreateGenerationBody,
        CreateGenerationRequest,
    )

    gen_body = CreateGenerationBody(
        id=None,
        trace_id=trace.id,
        name="test_lowlevel",
        start_time=start,
        end_time=end,
        model="test-model",
        input="Low-level input",
        output="Low-level output",
        metadata={"test": "lowlevel"},
    )

    print(f"  Generation body: {gen_body}")
    print("  Note: This may not work directly, just testing...")
except Exception as e:
    print(f"  ✗ Low-level API error: {e}")

# Test 3: Try using span instead of generation
print("\n--- Test 3: Using span instead of generation ---")
try:
    start = datetime.utcnow()
    span1 = trace.span(
        name="test_span",
        start_time=start,
        end_time=datetime.utcnow(),
        input="Span input text",
        output="Span output text",
        metadata={"type": "span_test"},
    )
    print(f"✓ Created span: {span1.id}")
except Exception as e:
    print(f"  ✗ Span error: {e}")

# Test 4: Check if generation accepts **kwargs
print("\n--- Test 4: Generation with explicit kwargs ---")
start = datetime.utcnow()
gen4 = trace.generation(
    name="test_kwargs",
    model="test-model",
    start_time=start,
    end_time=datetime.utcnow(),
    **{
        "input": {"messages": [{"role": "user", "content": "test"}]},
        "output": {"content": "response"},
    },
)
print(f"✓ Created generation with kwargs: {gen4.id}")

# Test 5: Try JSON serialized strings
print("\n--- Test 5: JSON serialized input/output ---")
start = datetime.utcnow()
input_data = [{"role": "user", "content": "What is 2+2?"}]
output_data = {"role": "assistant", "content": "The answer is 4"}

gen5 = trace.generation(
    name="test_json_serialized",
    model="test-model",
    input=json.dumps(input_data),
    output=json.dumps(output_data),
    start_time=start,
    end_time=datetime.utcnow(),
)
print(f"✓ Created generation with JSON strings: {gen5.id}")

# Flush
print("\n--- Flushing data ---")
langfuse.flush()
print("✓ Flushed")

print(f"\n=== ALL TESTS COMPLETE ===")
print(f"Trace ID: {trace.id}")
print(f"Check in Langfuse UI: {os.getenv('LANGFUSE_HOST')}")
print(f"\nGeneration IDs:")
print(f"  1. Update method: {gen1.id}")
print(f"  3. Span: {span1.id if 'span1' in locals() else 'N/A'}")
print(f"  4. Kwargs: {gen4.id}")
print(f"  5. JSON serialized: {gen5.id}")
