"""
Comprehensive test suite for AI Therapist Memory System.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def test_setup():
    """Test that setup is correct."""
    print("\n" + "=" * 70)
    print("TEST 1: Setup Verification")
    print("=" * 70)
    
    required_files = ["main.py", "therapist.py", "memory_manager.py", "storage.py", "prompts.py"]
    for file in required_files:
        if Path(file).exists():
            print(f"   [OK] {file}")
        else:
            print(f"   [FAIL] {file} missing")
            return False
    
    try:
        import openai
        import dotenv
        print("   [OK] Dependencies installed")
    except ImportError as e:
        print(f"   [FAIL] Missing dependency: {e}")
        return False
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("   [WARN] API key not configured (tests will be limited)")
        return False
    
    print(f"   [OK] API key configured")
    return True


def test_storage():
    """Test storage module."""
    print("\n" + "=" * 70)
    print("TEST 2: Storage Module")
    print("=" * 70)
    
    import storage
    
    test_client = "test_storage_client"
    
    profile = storage.load_profile(test_client)
    profile["key_facts"] = ["Test fact 1", "Test fact 2"]
    storage.save_profile(test_client, profile)
    
    loaded = storage.load_profile(test_client)
    assert len(loaded["key_facts"]) == 2
    print("   [OK] Profile save/load")
    
    themes = storage.load_themes(test_client)
    themes["recurring_themes"] = [{"name": "test_theme", "intensity": "high"}]
    storage.save_themes(test_client, themes)
    
    loaded_themes = storage.load_themes(test_client)
    assert len(loaded_themes["recurring_themes"]) == 1
    print("   [OK] Themes save/load")
    
    session_data = {"transcript": [{"role": "user", "content": "test"}]}
    session_id = storage.save_session(test_client, session_data)
    
    sessions = storage.list_sessions(test_client)
    assert len(sessions) >= 1
    print("   [OK] Session save/load")
    
    return True


def test_prompts():
    """Test prompts module."""
    print("\n" + "=" * 70)
    print("TEST 3: Prompts Module")
    print("=" * 70)
    
    import prompts
    
    profile = {
        "basic_info": {"name": "Test", "age": 30},
        "key_facts": ["Fact 1", "Fact 2"]
    }
    themes = {"recurring_themes": [{"name": "anxiety", "intensity": "high"}]}
    sessions = [{"session_id": "session_001", "summary": "Test summary"}]
    
    context = prompts.format_context_for_therapist(profile, themes, sessions)
    assert "Test" in context
    assert "anxiety" in context.lower()
    print("   [OK] Context formatting")
    
    transcript = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
    formatted = prompts.format_transcript_for_extraction(transcript)
    assert "Client:" in formatted
    assert "Therapist:" in formatted
    print("   [OK] Transcript formatting")
    
    return True


def test_memory_manager():
    """Test memory manager."""
    print("\n" + "=" * 70)
    print("TEST 4: Memory Manager")
    print("=" * 70)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("   [SKIP] No API key")
        return True
    
    from memory_manager import MemoryManager
    
    client = OpenAI(api_key=api_key)
    mm = MemoryManager("test_mm", client)
    
    print(f"   Model: {mm.model}")
    
    transcript = [
        {"role": "assistant", "content": "Hello, how are you?"},
        {"role": "user", "content": "Hi, I'm Alex. I'm anxious about work."}
    ]
    
    try:
        extracted = mm.extract_memories(transcript)
        assert "new_facts" in extracted
        assert "themes" in extracted
        print(f"   [OK] Memory extraction (facts: {len(extracted['new_facts'])})")
        return True
    except Exception as e:
        print(f"   [FAIL] Extraction failed: {e}")
        return False


def test_therapist():
    """Test therapist."""
    print("\n" + "=" * 70)
    print("TEST 5: Therapist")
    print("=" * 70)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("   [SKIP] No API key")
        return True
    
    from therapist import Therapist
    import uuid
    
    client = OpenAI(api_key=api_key)
    # Use unique client ID for each test
    test_id = f"test_therapist_{uuid.uuid4().hex[:8]}"
    therapist = Therapist(test_id, client)
    
    print(f"   Model: {therapist.model}")
    
    try:
        greeting = therapist.start_session()
        print(f"   Greeting: '{greeting[:50]}...'")
        assert len(greeting) > 0
        print("   [OK] Session start")
        
        response = therapist.send_message("Hi, I'm feeling stressed.")
        print(f"   Response: '{response[:50]}...'")
        assert len(response) > 0
        print("   [OK] Message exchange")
        
        summary = therapist.end_session()
        assert "session_id" in summary
        print(f"   [OK] Session end (ID: {summary['session_id']})")
        
        return True
    except Exception as e:
        print(f"   [FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli():
    """Test CLI module."""
    print("\n" + "=" * 70)
    print("TEST 6: CLI Module")
    print("=" * 70)
    
    try:
        import main
        print("   [OK] main.py imports successfully")
        
        import subprocess
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("   [OK] --help command works")
        else:
            print("   [FAIL] --help command failed")
            return False
        
        return True
    except Exception as e:
        print(f"   [FAIL] CLI test failed: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print("AI THERAPIST - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Setup", test_setup),
        ("Storage", test_storage),
        ("Prompts", test_prompts),
        ("Memory Manager", test_memory_manager),
        ("Therapist", test_therapist),
        ("CLI", test_cli),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n   [FAIL] {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"   {status} - {test_name}")
    
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    print("\n" + "=" * 70)
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if all(results.values()):
        print("\n[SUCCESS] ALL TESTS PASSED")
        print("\nThe system is fully functional!")
        print("\nRun the therapist:")
        print("  python main.py")
    else:
        print("\n[WARNING] SOME TESTS FAILED")
        print("\nCheck the failures above.")
    
    print("=" * 70 + "\n")
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
