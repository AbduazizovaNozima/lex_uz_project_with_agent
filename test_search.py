import sys
import os

# Add the project directory to sys.path
sys.path.append('/home/nozima/langchain_first_project')

from agents import search_article_tool

def test_search():
    print("Testing search_article_tool with 'Konstitutsiya 80-modda'...")
    result = search_article_tool("Konstitutsiya 80-modda")
    print("\nResult:")
    print(result)
    
    if result and "80-modda" in result and "Konstitutsiya" in result:
        print("\nSUCCESS: Found article 80 of Constitution.")
    else:
        print("\nFAILURE: Did not find article 80.")

    print("\nTesting search_article_tool with 'Konstitutsiya' (general info)...")
    result_general = search_article_tool("Konstitutsiya")
    print("\nResult General:")
    print(result_general[:200] + "...") # Print first 200 chars

    if result_general and "moddalar mavjud" in result_general:
        print("\nSUCCESS: Found general info.")
    else:
        print("\nFAILURE: Did not find general info.")

if __name__ == "__main__":
    test_search()
