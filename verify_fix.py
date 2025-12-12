import re

def test_logic(final_answer):
    image_path = None
    
    # a) Markdown formatini tekshirish: ![alt](url)
    md_match = re.search(r'!\[.*?\]\((.*?)\)', final_answer)
    if md_match:
        image_path = md_match.group(1)
    
    # b) Agar markdown bo'lmasa, matn ichidan "http...static..." ni qidirish
    if not image_path:
        url_match = re.search(r'(http[s]?://[^\s\)]+/static/[^\s\)]+)', final_answer)
        if url_match:
            image_path = url_match.group(1)

    # c) Sandbox prefiksini olib tashlash
    if image_path and "sandbox:" in image_path:
        image_path = image_path.replace("sandbox:", "")
        
    return image_path

# Test cases
test1 = "Here is the image: ![test](sandbox:/home/nozima/static/test.png)"
result1 = test_logic(test1)
print(f"Test 1 (Markdown): {result1}")
assert result1 == "/home/nozima/static/test.png"

test2 = "Check this url: http://localhost:8000/static/test.png"
result2 = test_logic(test2)
print(f"Test 2 (URL): {result2}")
assert result2 == "http://localhost:8000/static/test.png"

test3 = "Mixed: sandbox:/home/nozima/static/test.png"
# Note: My logic in api.py only extracts from Markdown or URL. 
# If it's just text, it might not be caught by a/b steps unless I added logic for that too?
# Wait, let's check api.py again.
# It only checks Markdown and URL. 
# But the user's issue showed: "📷 Rasm: sandbox:/home/..."
# This format comes from the agent response text.
# `api.py` lines 626-639 only check Markdown and URL.
# BUT, `frontend.py` checks `📷 Rasm: (.+)`.
# So `api.py` might NOT be extracting it if it's in `📷 Rasm:` format and NOT markdown/url.
# Let's check the logs in the user request.
# "🖼️ RASM: sandbox:/home/nozima/langchain_first_project/static/registration.png"
# This means `api.py` DID extract it.
# How?
# Ah, I might have missed something in `api.py`.
# Let's re-read `api.py` carefully.

# Line 299 in the commented out code had `re.search(r'📷 Rasm: (static/[^\s\n]+)', content)`.
# But the ACTIVE code (lines 626+) only has Markdown and URL.
# Wait, the log says:
# 📤 JAVOB: Registratsiya qilish uchun Lex.uz saytida quyidagi amallarni bajaring:
# ...
# 🖼️ RASM: sandbox:/home/nozima/langchain_first_project/static/registration.png

# If `api.py` extracted it, then it must have matched one of the regexes.
# The user text had: `![Ro'yxatdan o'tish jarayoni](sandbox:/home/nozima/langchain_first_project/static/registration.png)`
# So it matched the Markdown regex!
# So my test1 covers it.

print("All tests passed!")
