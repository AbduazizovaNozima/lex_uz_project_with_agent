from knowledge_base import search_guide_by_tags

queries = [
    "search",
    "qidirish",
    "qidiruv",
    "izlash",
    "topish",
    "saytda qanday qidiriladi",
    "hujjatni qanday topsam bo'ladi",
    "registratsiya",
    "tilni o'zgartirish"
]

print("Testing search_guide_by_tags:")
for q in queries:
    result = search_guide_by_tags(q)
    status = "✅ Found" if result else "❌ Not Found"
    print(f"Query: '{q}' -> {status}")
