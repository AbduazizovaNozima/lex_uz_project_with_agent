import sys
import os

# Mock autogen to avoid import error if it's not needed for this function
# But search_article_direct is in agents.py which imports autogen at top level.
# So we must use the venv python.

try:
    from agents import search_article_direct
except ImportError:
    # If running with system python and autogen is missing
    print("Could not import agents. Make sure to run with venv python.")
    sys.exit(1)

queries = [
    "konstitusiyada nechta modda bor",  # Misspelled (missing 't')
    "konstitutsiyada nechta modda bor", # Correct spelling
    "Konstitutsiya",
    "Konstitusiya"
]

print("Testing search_article_direct:")
for q in queries:
    try:
        result = search_article_direct(q)
        status = "✅ Found" if result else "❌ Not Found"
        print(f"Query: '{q}' -> {status}")
    except Exception as e:
        print(f"Query: '{q}' -> ❌ Error: {e}")
