"""Test Langfuse input/output directly"""

import os
from datetime import datetime
from langfuse import Langfuse
from langfuse.model import ModelUsage

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)

print("Testing Langfuse input/output...")
print(f"Langfuse version: {langfuse.__class__.__module__}")

# Create a trace
trace = langfuse.trace(
    name="test_io_trace", user_id="test_user", metadata={"test": "input_output"}
)

print(f"✓ Created trace: {trace.id}")

# Test 1: Simple strings
print("\n--- Test 1: Simple string input/output ---")
start = datetime.utcnow()
gen1 = trace.generation(
    name="test_gen_strings",
    model="test-model",
    input="What is 2+2?",
    output="The answer is 4",
    start_time=start,
    end_time=datetime.utcnow(),
)
print(f"✓ Created generation with strings: {gen1.id}")

# Test 2: Dict input/output
print("\n--- Test 2: Dict input/output ---")
start = datetime.utcnow()
gen2 = trace.generation(
    name="test_gen_dict",
    model="test-model",
    input={"prompt": "What is 2+2?"},
    output={"response": "The answer is 4"},
    start_time=start,
    end_time=datetime.utcnow(),
)
print(f"✓ Created generation with dicts: {gen2.id}")

# Test 3: List input/output (like messages)
print("\n--- Test 3: List input/output ---")
start = datetime.utcnow()
gen3 = trace.generation(
    name="test_gen_list",
    model="test-model",
    input=[{"role": "user", "content": "What is 2+2?"}],
    output=[{"role": "assistant", "content": "The answer is 4"}],
    start_time=start,
    end_time=datetime.utcnow(),
)
print(f"✓ Created generation with lists: {gen3.id}")

# Test 4: With usage
print("\n--- Test 4: With ModelUsage ---")
start = datetime.utcnow()
usage = ModelUsage(
    input=10,
    output=5,
    total=15,
    unit="TOKENS",
    input_cost=0.001,
    output_cost=0.002,
    total_cost=0.003,
)
gen4 = trace.generation(
    name="test_gen_usage",
    model="test-model",
    input="What is 2+2?",
    output="The answer is 4",
    start_time=start,
    end_time=datetime.utcnow(),
    usage=usage,
)
print(f"✓ Created generation with usage: {gen4.id}")

# Flush
print("\n--- Flushing data ---")
langfuse.flush()
print("✓ Flushed")

print(f"\n=== ALL TESTS COMPLETE ===")
print(f"Trace ID: {trace.id}")
print(f"Check in Langfuse UI: {os.getenv('LANGFUSE_HOST')}")
print(f"\nGeneration IDs:")
print(f"  1. Strings: {gen1.id}")
print(f"  2. Dicts: {gen2.id}")
print(f"  3. Lists: {gen3.id}")
print(f"  4. With usage: {gen4.id}")
