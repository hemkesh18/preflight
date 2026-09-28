"""
Verification script for Hindsight and Groq credentials.
Tests basic connectivity, bank creation, retain, and recall operations.
"""
import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in project root and parent directories
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path.cwd() / ".env"

load_dotenv(dotenv_path=env_path)

HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def check_credentials():
    missing = []
    if not HINDSIGHT_API_KEY or HINDSIGHT_API_KEY == "your_hindsight_api_key_here":
        missing.append("HINDSIGHT_API_KEY")
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        missing.append("GROQ_API_KEY")
    
    if missing:
        print(f"[ERROR] Missing required credentials in .env: {', '.join(missing)}")
        print(f"Looked at .env file path: {env_path.resolve()}")
        print("\nPlease ensure your .env file exists and contains:")
        print("  HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io")
        print("  HINDSIGHT_API_KEY=hsk_...")
        print("  GROQ_API_KEY=gsk_...")
        return False
    return True


def test_groq():
    print("[*] Testing Groq LLM connectivity...")
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Respond with the word 'OK' only."}],
            max_tokens=10,
        )
        msg = response.choices[0].message.content.strip()
        print(f"[+] Groq response: {msg}")
        return True
    except Exception as e:
        print(f"[-] Groq test failed: {e}")
        # Try fallback model
        try:
            print("[*] Testing Groq fallback model qwen/qwen3-32b...")
            response = client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[{"role": "user", "content": "Respond with the word 'OK' only."}],
                max_tokens=10,
            )
            msg = response.choices[0].message.content.strip()
            print(f"[+] Groq fallback response: {msg}")
            return True
        except Exception as e2:
            print(f"[-] Groq fallback failed: {e2}")
            return False


def test_hindsight():
    print(f"[*] Testing Hindsight connectivity to {HINDSIGHT_BASE_URL}...")
    try:
        from hindsight_client import Hindsight
        client = Hindsight(base_url=HINDSIGHT_BASE_URL, api_key=HINDSIGHT_API_KEY)
        
        # Test bank ID with timestamp to prevent collisions
        test_bank = f"test-preflight-{int(datetime.datetime.now().timestamp())}"
        
        print(f"[*] Ensuring test memory bank '{test_bank}'...")
        try:
            client.create_bank(
                bank_id=test_bank,
                name="Preflight Verification Bank",
                mission="Verification bank for Preflight automated testing"
            )
        except Exception as be:
            # Bank might already exist or create_bank returned handled status
            print(f"    (create_bank notice: {be})")
            
        print("[*] Retaining sample memory...")
        retain_resp = client.retain(
            bank_id=test_bank,
            content="Deploy #101 on payments-api updated config.yaml on Friday 18:00 and caused connection pool exhaustion.",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            tags=["service:payments-api", "type:config", "env:production"],
            document_id="deploy-verify-101"
        )
        print(f"[+] Retain successful! Items count: {getattr(retain_resp, 'items_count', 1)}")

        print("[*] Recalling memory...")
        recall_resp = client.recall(
            bank_id=test_bank,
            query="Did payments-api config change cause any connection pool issue?",
            tags=["service:payments-api"]
        )
        results = recall_resp.results
        print(f"[+] Recall returned {len(results)} memory units:")
        for r in results:
            print(f"    - [{r.id}] {r.text[:80]}... (tags: {r.tags})")

        # Cleanup
        try:
            client.delete_bank(bank_id=test_bank)
            print("[+] Cleaned up test memory bank.")
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"[-] Hindsight test failed: {e}")
        return False


if __name__ == "__main__":
    if not check_credentials():
        sys.exit(1)
    
    h_ok = test_hindsight()
    g_ok = test_groq()
    
    if h_ok and g_ok:
        print("\n[SUCCESS] Both Hindsight and Groq credentials verified successfully!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Verification failed.")
        sys.exit(1)
