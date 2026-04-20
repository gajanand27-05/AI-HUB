import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import detect_intent

test_cases = [
    ("Test 1", "Write code for login system"),
    ("Test 2", "Summarize and translate this text to Hindi"),
    ("Test 3", "Explain this image in simple English"),
    ("Test 4", "Convert speech to text and summarize"),
    ("Test 5", "Do something smart")
]

print("Running Intent Detection Tests:\n")
for label, text in test_cases:
    print(f"--- {label} ---")
    print(f"Input: {text}")
    result = detect_intent(text)
    print(f"Output: {json.dumps(result, indent=2)}\n")
