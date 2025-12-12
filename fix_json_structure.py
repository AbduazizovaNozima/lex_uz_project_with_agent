import json
import re
import os
import glob

STRUCTURED_FOLDER = '/home/nozima/langchain_first_project/lex_structured'

def fix_file(file_path):
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return

    # Check if it's already in the correct format (multiple keys that are digits)
    # keys = list(data.keys())
    # if len(keys) > 5 and all(k.isdigit() for k in keys[:5]):
    #     print(f"  Skipping {file_path}, seems already correct.")
    #     return

    # Assuming the content is in data['1']['content'] or just data['content']
    content = ""
    # If the file was already processed, it has many keys. We need to reconstruct the full content.
    # But the order might be lost if we just iterate keys.
    # However, since we are fixing a bad split, we might need to reload the ORIGINAL content if possible.
    # But we overwrote it.
    # Fortunately, the keys are likely distinct segments of the original text.
    # We can try to concatenate them back?
    # Or better, just treat the file as a collection of texts and search within each?
    # No, that's messy.
    
    # If the file is already split, we can't easily "unsplit" it perfectly without order.
    # But wait, I can just check if '1' exists and has a huge content.
    # If I already split it, '1' will have small content.
    
    # If I already split it badly, I might have lost the original structure.
    # BUT, I can try to find the "preamble" or the first chunk which might contain the rest if the split failed?
    # No, the split succeeded in producing 327 parts.
    
    # If I want to re-split, I need the full text.
    # I can concatenate all values['content']? 
    # But in what order?
    # The keys are "1", "2", "106", etc.
    # If I sort by key numerically? 
    # The Constitution articles are 1..155.
    # If I have 327 keys, I have duplicates or garbage.
    
    # Let's try to concatenate based on the original file order if possible?
    # JSON keys are unordered in older Python, but ordered in 3.7+.
    # So `data.values()` should give content in insertion order (which is split order).
    
    full_content = ""
    if len(data) > 20: # Already split
        print("  Re-assembling content from existing keys...")
        for key, val in data.items():
            if isinstance(val, dict) and 'content' in val:
                # We need to put back the delimiter!
                # The key is the article number.
                # So we prepend "X-modda." to the content?
                # Wait, my previous script removed the delimiter from the content?
                # pattern.split returns [preamble, delim1, content1, delim2, content2...]
                # I stored content1.
                # So "X-modda" is missing from content1.
                # I should add it back to reconstruct.
                # Also replace literal \n with real \n to fix the mess
                content_val = val['content'].replace('\\n', '\n')
                full_content += f"\n{key}-modda. " + content_val
            elif isinstance(val, str): # Just in case
                 content_val = val.replace('\\n', '\n')
                 full_content += f"\n{key}-modda. " + content_val
    else:
        # Not split yet (or failed to split much)
        if '1' in data and 'content' in data['1']:
            content = data['1']['content']
        elif 'content' in data:
            content = data['content']
        else:
            first_key = list(data.keys())[0]
            if isinstance(data[first_key], dict) and 'content' in data[first_key]:
                content = data[first_key]['content']
            else:
                print(f"  Could not find content in {file_path}")
                return
        full_content = content.replace('\\n', '\n')

    # Regex to find articles
    # Pattern: Look for "X-modda." (with dot)
    # We capture the number.
    # Now that we replaced \\n with \n, we can use \n
    
    pattern = re.compile(r'(?:^|\n)(\d+)-modda\.', re.IGNORECASE)
    
    parts = pattern.split(full_content)
    
    if "Konstitutsiya" in file_path:
        print(f"DEBUG: Full content length: {len(full_content)}")
        
        # Debug with finditer
        matches = list(pattern.finditer(full_content))
        print(f"DEBUG: finditer found {len(matches)} matches.")
        # Check specific missing articles
        found_80 = False
        for m in matches:
            if m.group(1) == "80":
                found_80 = True
                print(f"DEBUG: finditer FOUND 80 at {m.start()}")
        if not found_80:
             print("DEBUG: finditer did NOT find 80")

    parts = pattern.split(full_content)
    
    # parts[0] is everything before the first article (preamble)
    # parts[1] is the first article number
    # parts[2] is the content of the first article
    # parts[3] is the second article number
    # parts[4] is the content of the second article
    # ...
    
    new_data = {}
    
    # Save preamble if needed, but for now we focus on articles
    # new_data['preamble'] = parts[0].strip()
    
    if len(parts) < 3:
        print(f"  No articles found in {file_path} with regex.")
        return

    for i in range(1, len(parts), 2):
        article_num = parts[i]
        article_text = parts[i+1].strip()
        
        # Clean up the text
        # Remove garbage like "Ҳужжатга таклиф юбориш..."
        garbage_pattern = re.compile(r'Ҳужжатга таклиф юборишАудиони тинглашҲужжат элементидан ҳавола олиш', re.IGNORECASE)
        article_text = garbage_pattern.sub('', article_text)
        
        # Extract title if possible (usually the first line or sentence)
        # For Konstitutsiya: "1-modda.[OKOZ:...] Oʻzbekiston — boshqaruvning..."
        # The title might be embedded or just the text.
        # Let's just use the first few words as title or generic "X-modda"
        
        title = f"{article_num}-modda"
        
        # Try to find a real title if it exists before the [OKOZ] tag or newline
        # In Mehnat Kodeksi: "1-modda. Ushbu Kodeks bilan tartibga solinadigan munosabatlar[OKOZ:..."
        
        # Let's take the first line as title candidate
        first_line = article_text.split('\n')[0]
        # Remove [OKOZ...] tags for title
        clean_first_line = re.sub(r'\[.*?\]', '', first_line).strip()
        if clean_first_line:
             # Limit title length
             if len(clean_first_line) < 100:
                 title = f"{article_num}-modda. {clean_first_line}"
             else:
                 title = f"{article_num}-modda"

        new_data[article_num] = {
            "title": title,
            "content": article_text
        }

    print(f"  Found {len(new_data)} articles.")
    
    # Save back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved {file_path}")
    except Exception as e:
        print(f"  Error saving {file_path}: {e}")

def main():
    files = glob.glob(os.path.join(STRUCTURED_FOLDER, "*.json"))
    for file_path in files:
        fix_file(file_path)

if __name__ == "__main__":
    main()
