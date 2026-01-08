import threading
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def create_user(username, email):
    res = requests.post(f"{BASE_URL}/users/", json={"username": username, "email": email})
    if res.status_code != 200:
        # User might already exist in persistent DB, try to find or ignore
        pass 
    return res.json()

def create_wallet(user_id):
    res = requests.post(f"{BASE_URL}/wallets/", json={"user_id": user_id})
    return res.json()

def deposit(wallet_id, amount):
    res = requests.post(f"{BASE_URL}/wallets/{wallet_id}/deposit", json={"amount": amount})
    return res.json()

def get_balance(wallet_id):
    res = requests.get(f"{BASE_URL}/wallets/{wallet_id}")
    return res.json()["balance"]

def transfer(from_id, to_id, amount):
    res = requests.post(f"{BASE_URL}/transfer/", json={
        "from_wallet_id": from_id,
        "to_wallet_id": to_id,
        "amount": amount
    })
    return res.status_code

def run_concurrent_test():
    print("--- Starting Concurrency Test (Exposing Race Condition) ---")
    
    # Unique suffix to avoid collisions if re-run
    suffix = str(int(time.time()))
    u1 = create_user(f"alice_{suffix}", f"alice_{suffix}@example.com")
    u2 = create_user(f"bob_{suffix}", f"bob_{suffix}@example.com")
    
    # Check if we got IDs
    if 'id' not in u1: 
        # Fallback if user exists logic not quite right, but distinct emails helpful
        print("Setup error: could not create users") 
        return

    w1 = create_wallet(u1['id'])
    w2 = create_wallet(u2['id'])
    
    # 1. Fund Wallet 1 with 100.00
    deposit(w1['id'], 100.0)
    print(f"Initial Balance W1: {get_balance(w1['id'])}")
    
    # 2. Launch 5 concurrent threads, each trying to transfer 50.00
    # Expected: Only 2 should succeed (Total 100).
    # Vulnerable: More than 2 might succeed, driving balance negative or double spending.
    
    threads = []
    results = []
    
    def attempt_transfer():
        code = transfer(w1['id'], w2['id'], 50.0)
        results.append(code)

    for _ in range(5):
        t = threading.Thread(target=attempt_transfer)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    final_balance = get_balance(w1['id'])
    print(f"Results codes: {results}")
    print(f"Final Balance W1: {final_balance}")
    
    # 3. Assert Failure
    # If the system was safe, balance should be >= 0.
    # If concurrent requests raced, balance might be -50 or -100 (Success 3 or 4 times).
    
    if final_balance < 0:
        print("SUCCESS: System FAILED as expected! (Double Spend occurred)")
        print("Build phase requirement met: Vulnerability exposed.")
        sys.exit(0) # Exit code 0 means "Test ran and found the bug"
    elif results.count(200) > 2:
         print("SUCCESS: System FAILED as expected! (More transfers succeeded than funds allowed)")
         sys.exit(0)
    else:
        print("WARNING: Race condition did not occur. Try increasing thread count or artificial delay.")
        # We want the test to 'fail' if the system checks out correct, technically.
        # But for this purpose, we want to prove it IS vulnerable. 
        # If it says 'WARNING', it means we failed to break it.
        sys.exit(1)

if __name__ == "__main__":
    # Wait for server to be up (simple retry)
    for _ in range(5):
        try:
            requests.get(BASE_URL)
            break
        except:
            time.sleep(1)
            
    run_concurrent_test()
