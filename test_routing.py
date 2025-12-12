#!/usr/bin/env python3
"""
Test script for verifying 3-way agent routing
"""
import sys
sys.path.insert(0, '/home/nozima/langchain_first_project')

from agents import user_proxy, manager

# Test cases for 3 routing paths
test_cases = [
    {
        "type": "SOCIAL",
        "query": "Salom, qalaysiz?",
        "expected": "SocialBot should respond"
    },
    {
        "type": "KNOWLEDGE",
        "query": "Qanday qilib registratsiyadan o'taman?",
        "expected": "KnowledgeBot should respond with registration guide"
    },
    {
        "type": "LEGAL",
        "query": "Ma'muriy javobgarlik to'g'risidagi kodeks 131-modda nimani tartibga soladi?",
        "expected": "LegalSearcher should search and LegalAnalyzer should respond"
    }
]

print("=" * 70)
print("3-WAY ROUTING TEST")
print("=" * 70)

for i, test in enumerate(test_cases, 1):
    print(f"\n\n{'=' * 70}")
    print(f"TEST {i}: {test['type']}")
    print(f"{'=' * 70}")
    print(f"Query: {test['query']}")
    print(f"Expected: {test['expected']}")
    print(f"{'=' * 70}\n")
    
    try:
        user_proxy.initiate_chat(
            manager,
            message=test['query']
        )
        print(f"\n✅ Test {i} completed")
    except Exception as e:
        print(f"\n❌ Test {i} failed: {str(e)}")
    
    print("\n" + "=" * 70)

print("\n\n🎉 All tests completed!")
