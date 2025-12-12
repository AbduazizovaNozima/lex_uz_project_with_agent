import re
import json

def test_regex():
    content = "si.\n78-modda.\n\n\nҲужжатга..."
    pattern = re.compile(r'(?:^|\n|\s)(\d+)-modda', re.IGNORECASE)
    parts = pattern.split(content)
    print(f"Parts length: {len(parts)}")
    for i, p in enumerate(parts):
        print(f"{i}: {p!r}")

if __name__ == "__main__":
    test_regex()
