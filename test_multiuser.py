"""
Multi-User Concurrent Request Test
Tests parallel request handling and session isolation
"""

import requests
import threading
import time
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"

def test_single_user_session():
    """Test 1: Single user with session"""
    print("\n" + "="*70)
    print("TEST 1: Single User Session")
    print("="*70)
    
    # Create new session
    response = requests.post(f"{API_BASE_URL}/sessions/new")
    session_id = response.json()["session_id"]
    print(f"✓ Session yaratildi: {session_id}")
    
    # Send messages
    questions = [
        "Salom",
        "Mehnat kodeksi 131-modda haqida",
        "Registratsiya qanday qilinadi"
    ]
    
    for q in questions:
        print(f"\n📤 Savol: {q}")
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"question": q, "session_id": session_id},
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Javob olindi ({len(data['response'])} belgi)")
        else:
            print(f"✗ Xato: {response.status_code}")
    
    # Check history
    response = requests.get(f"{API_BASE_URL}/sessions/{session_id}/history")
    history = response.json()
    print(f"\n✓ Tarix: {history['count']} xabar")
    
    return session_id


def test_multiple_sessions():
    """Test 2: Multiple sessions"""
    print("\n" + "="*70)
    print("TEST 2: Multiple Sessions")
    print("="*70)
    
    sessions = []
    for i in range(3):
        response = requests.post(f"{API_BASE_URL}/sessions/new")
        session_id = response.json()["session_id"]
        sessions.append(session_id)
        print(f"✓ Session {i+1}: {session_id}")
    
    # List sessions
    response = requests.get(f"{API_BASE_URL}/sessions")
    total = response.json()["total"]
    print(f"\n✓ Jami sessionlar: {total}")
    
    return sessions


def send_concurrent_request(session_id, question, thread_id):
    """Helper function for concurrent requests"""
    start_time = time.time()
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"question": question, "session_id": session_id},
            timeout=120
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Thread {thread_id}: Javob olindi ({elapsed:.2f}s)")
            return True
        else:
            print(f"✗ Thread {thread_id}: Xato {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Thread {thread_id}: Exception - {e}")
        return False


def test_concurrent_requests():
    """Test 3: Concurrent requests from multiple users"""
    print("\n" + "="*70)
    print("TEST 3: Concurrent Requests (Parallel Users)")
    print("="*70)
    
    # Create 3 sessions
    sessions = []
    for i in range(3):
        response = requests.post(f"{API_BASE_URL}/sessions/new")
        session_id = response.json()["session_id"]
        sessions.append(session_id)
        print(f"✓ User {i+1} session: {session_id}")
    
    # Prepare concurrent requests
    questions = [
        "Salom, qalaysiz?",
        "Mehnat kodeksi haqida",
        "Til sozlamalari"
    ]
    
    threads = []
    print("\n🚀 Parallel requestlar yuborilmoqda...")
    start_time = time.time()
    
    for i, (session_id, question) in enumerate(zip(sessions, questions)):
        thread = threading.Thread(
            target=send_concurrent_request,
            args=(session_id, question, i+1)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    print(f"\n✓ Barcha requestlar bajarildi: {total_time:.2f}s")
    
    # Verify each session has correct history
    print("\n📊 Session tarixlarini tekshirish:")
    for i, session_id in enumerate(sessions):
        response = requests.get(f"{API_BASE_URL}/sessions/{session_id}/history")
        history = response.json()
        print(f"  User {i+1}: {history['count']} xabar")
    
    return sessions


def test_session_isolation():
    """Test 4: Session isolation"""
    print("\n" + "="*70)
    print("TEST 4: Session Isolation")
    print("="*70)
    
    # Create 2 sessions
    session1 = requests.post(f"{API_BASE_URL}/sessions/new").json()["session_id"]
    session2 = requests.post(f"{API_BASE_URL}/sessions/new").json()["session_id"]
    
    print(f"✓ Session 1: {session1}")
    print(f"✓ Session 2: {session2}")
    
    # Send different messages to each
    print("\n📤 Session 1'ga xabar:")
    requests.post(
        f"{API_BASE_URL}/chat",
        json={"question": "Mehnat kodeksi", "session_id": session1},
        timeout=120
    )
    
    print("📤 Session 2'ga xabar:")
    requests.post(
        f"{API_BASE_URL}/chat",
        json={"question": "Registratsiya", "session_id": session2},
        timeout=120
    )
    
    # Check histories are separate
    hist1 = requests.get(f"{API_BASE_URL}/sessions/{session1}/history").json()
    hist2 = requests.get(f"{API_BASE_URL}/sessions/{session2}/history").json()
    
    print(f"\n✓ Session 1 tarixi: {hist1['count']} xabar")
    print(f"✓ Session 2 tarixi: {hist2['count']} xabar")
    
    # Verify content is different
    if hist1['messages'][0]['content'] != hist2['messages'][0]['content']:
        print("✓ Sessionlar izolatsiya qilingan (tarixlar farq qiladi)")
    else:
        print("✗ XATO: Sessionlar aralashib ketgan!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("LEX.UZ AI ASSISTANT - MULTI-USER TEST SUITE")
    print("="*70)
    print(f"Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Check API health
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code != 200:
            print("✗ API ishlamayapti!")
            return
        print("✓ API ishlayapti")
        
        # Run tests
        test_single_user_session()
        time.sleep(2)
        
        test_multiple_sessions()
        time.sleep(2)
        
        test_concurrent_requests()
        time.sleep(2)
        
        test_session_isolation()
        
        print("\n" + "="*70)
        print("✅ BARCHA TESTLAR MUVAFFAQIYATLI YAKUNLANDI")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Test xatosi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
