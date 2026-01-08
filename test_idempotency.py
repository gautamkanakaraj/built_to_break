
import requests
import sys
import random
import time
import uuid

BASE_URL = "http://localhost:4000"

def get_token(username):
    # Register/Get token is a bit tricky since we don't have separate auth flow for test users.
    # For now, we will simulate login by calling the logic directly or assume we can get token.
    # Wait! Our `login_for_access_token` checks if user exists.
    # So we Create User -> Login -> Get Token.
    r = requests.post(f"{BASE_URL}/users/token", 
                      data={"username": username, "password": "any"},
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code == 200:
        return r.json()["access_token"]
    print(f"Failed to login: {r.text}")
    sys.exit(1)

def create_user_and_wallet(email_prefix):
    username = f"{email_prefix}_{random.randint(10000,99999)}"
    user_payload = {
        "username": username,
        "email": f"{email_prefix}_{random.randint(10000,99999)}@example.com"
    }
    r = requests.post(f"{BASE_URL}/users/", json=user_payload)
    if r.status_code != 200:
        sys.exit(1)
    
    # Get Token
    token = get_token(username)
    headers = {"Authorization": f"Bearer {token}"}

    # Create Wallet (Authenticated? No, wallet creation not authenticated in task description but good practice. 
    # Checking api/wallets.py... it uses Depends(get_db) but NOT security. Let's assume public for now or check.)
    # The prompt said "JWT authentication is ALLOWED only to identify the caller." 
    # My plan only updated api/transfer.py. So likely wallet creation is still open.
    
    r = requests.post(f"{BASE_URL}/wallets/", json={"user_id": r.json()["id"]})
    wallet_id = r.json()["id"]
    return wallet_id, token

def get_balance(wallet_id):
    r = requests.get(f"{BASE_URL}/wallets/{wallet_id}")
    return r.json()["balance"]

def run_test():
    print("--- Setting up environment ---")
    wallet_a, token_a = create_user_and_wallet("alice_replay")
    wallet_b, token_b = create_user_and_wallet("bob_replay")
    
    # Initial Deposit (Still public endpoint?)
    requests.post(f"{BASE_URL}/wallets/{wallet_a}/deposit", json={"amount": 100.0})
    
    print(f"Wallet A: {wallet_a} (Balance: {get_balance(wallet_a)})")
    print(f"Wallet B: {wallet_b} (Balance: {get_balance(wallet_b)})")
    print("------------------------------")
    
    # Attack Payload
    idempotency_key = str(uuid.uuid4())
    transfer_payload = {
        "from_wallet_id": wallet_a,
        "to_wallet_id": wallet_b,
        "amount": 10.0,
        "idempotency_key": idempotency_key
    }
    headers = {"Authorization": f"Bearer {token_a}"}
    
    print("Executing 'Single' Transfer Request... (Replayed 5 times)")
    print(f"Using Idempotency Key: {idempotency_key}")
    
    success_count = 0
    
    for i in range(1, 6):
        r = requests.post(f"{BASE_URL}/transfer/", json=transfer_payload, headers=headers)
        status = r.status_code
        new_bal_a = get_balance(wallet_a)
        print(f"Attempt #{i}: Status {status} | Wallet A Balance: {new_bal_a}")
        
        # In a real idempotent system, repeated calls usually return 200 (Success) with SAME result 
        # OR 409 (Conflict). My implementation returns the existing txn (so 200 OK).
        if status == 200:
            success_count += 1
            
        time.sleep(0.1)
        
    final_a = get_balance(wallet_a)
    final_b = get_balance(wallet_b)
    
    print("------------------------------")
    print(f"Final Balance A: {final_a}")
    print(f"Final Balance B: {final_b}")
    
    expected_safe = 90.0 # 100 - 10 (once)
    
    if final_a == expected_safe:
        print("\n[PASS] IDEMPOTENCY VERIFIED")
        print(f"System processed the transfer exactly once despite {success_count} attempts.")
        sys.exit(0)
    else:
        print("\n[FAIL] SYSTEM STILL VULNERABLE")
        print(f"Expected: {expected_safe}, Got: {final_a}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
