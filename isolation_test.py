
import requests
import time
import threading
import sys
import random

BASE_URL = "http://localhost:8000"

def create_user_and_wallet(email_prefix):
    # 1. Create User
    user_payload = {
        "username": f"{email_prefix}_{random.randint(1000,9999)}",
        "email": f"{email_prefix}_{random.randint(1000,9999)}@example.com"
    }
    r = requests.post(f"{BASE_URL}/users/", json=user_payload)
    if r.status_code != 200:
        print(f"Failed to create user: {r.text}")
        sys.exit(1)
    user_id = r.json()["id"]

    # 2. Create Wallet
    wallet_payload = {"user_id": user_id}
    r = requests.post(f"{BASE_URL}/wallets/", json=wallet_payload)
    if r.status_code != 200:
         print(f"Failed to create wallet: {r.text}")
         sys.exit(1)
    wallet_id = r.json()["id"]
    
    # 3. Deposit Initial Funds (100.0)
    requests.post(f"{BASE_URL}/wallets/{wallet_id}/deposit", json={"amount": 100.0})
    
    return wallet_id

def get_balance(wallet_id):
    r = requests.get(f"{BASE_URL}/wallets/{wallet_id}")
    if r.status_code != 200:
        return 0.0
    return r.json()["balance"]

def run_test():
    print("--- Setting up environment ---")
    wallet_a = create_user_and_wallet("alice")
    wallet_b = create_user_and_wallet("bob")
    
    initial_a = get_balance(wallet_a)
    initial_b = get_balance(wallet_b)
    total_invariant = initial_a + initial_b
    
    print(f"Wallet A ID: {wallet_a} (Balance: {initial_a})")
    print(f"Wallet B ID: {wallet_b} (Balance: {initial_b})")
    print(f"Invariant Total: {total_invariant}")
    print("------------------------------")

    stop_event = threading.Event()
    
    # Background thread to constantly move money
    def mover_logic():
        while not stop_event.is_set():
            amount = 10.0
            # A -> B
            requests.post(f"{BASE_URL}/transfer/", json={
                "from_wallet_id": wallet_a,
                "to_wallet_id": wallet_b,
                "amount": amount
            })
            time.sleep(0.01) # fast enough to cause race, slow enough to not DOS
            
            # B -> A
            requests.post(f"{BASE_URL}/transfer/", json={
                "from_wallet_id": wallet_b,
                "to_wallet_id": wallet_a,
                "amount": amount
            })
            time.sleep(0.01)

    mover_thread = threading.Thread(target=mover_logic)
    mover_thread.daemon = True
    mover_thread.start()

    print("Starting READ SKEW verification loop...")
    print("Reading Balance A... then Balance B... and checking sum.")
    
    start_time = time.time()
    iterations = 0
    
    try:
        while time.time() - start_time < 10: # Run for max 10 seconds
            iterations += 1
            
            # THE LOGICAL FLOW (The 'Transaction' we want to be isolated)
            # T1: Read A
            bal_a = get_balance(wallet_a)
            # T2: Read B
            bal_b = get_balance(wallet_b)
            
            current_total = bal_a + bal_b
            
            if abs(current_total - total_invariant) > 0.01:
                print("\n!!! ISOLATION FAILURE OBSERVED !!!")
                print(f"Iteration: {iterations}")
                print(f"Read 1 (Wallet A): {bal_a}")
                print(f"Read 2 (Wallet B): {bal_b}")
                print(f"Sum: {current_total}")
                print(f"Expected Invariant: {total_invariant}")
                print("REASON: Read Skew / Non-Repeatable Read occurred.")
                print("Another transaction modified the state between Read 1 and Read 2.")
                stop_event.set()
                sys.exit(0) # SUCCESS: We found the bug
            
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(0.1)

    except KeyboardInterrupt:
        stop_event.set()
    
    stop_event.set()
    print("\nNo isolation failure observed in 10 seconds.")
    print("The system might be accidentally isolated or load was too low.")
    sys.exit(1) # FAILURE: We wanted to prove it's broken

if __name__ == "__main__":
    run_test()
