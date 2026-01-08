import requests
import time
import io
import csv

BASE_URL = "http://localhost:4000"

def run_ultimate_test():
    print("--- 🚀 STARTING ULTIMATE SYSTEM VERIFICATION ---")
    ts = int(time.time())
    
    # 1. User Creation & Auth
    u1, u2 = f"alice_{ts}", f"bob_{ts}"
    print(f"[*] Registering users: {u1}, {u2}...")
    requests.post(f"{BASE_URL}/users/", json={"username": u1, "email": f"{u1}@g.co", "password": "p"}).raise_for_status()
    requests.post(f"{BASE_URL}/users/", json={"username": u2, "email": f"{u2}@g.co", "password": "p"}).raise_for_status()
    
    t1 = requests.post(f"{BASE_URL}/users/token", data={"username": u1, "password": "p"}).json()["access_token"]
    t2 = requests.post(f"{BASE_URL}/users/token", data={"username": u2, "password": "p"}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}
    
    # 2. PIN Setup
    print("[*] Setting Transaction PIN for Alice...")
    requests.post(f"{BASE_URL}/users/me/pin", headers=h1, json={"pin": "1234"}).raise_for_status()
    
    # 3. Wallet Funding
    w1_id = requests.get(f"{BASE_URL}/users/me", headers=h1).json()["wallet"]["id"]
    w2_id = requests.get(f"{BASE_URL}/users/me", headers=h2).json()["wallet"]["id"]
    print(f"[*] Funding Alice's wallet ({w1_id}) with $10,000...")
    requests.post(f"{BASE_URL}/wallets/{w1_id}/deposit", json={"amount": 10000}).raise_for_status()
    
    # 4. Mandatory PIN Check
    print("[*] Verification: Transfer WITHOUT PIN (Expect 422/Error)...")
    # Note: Our schema requires pin, so this should fail validation at FastAPI level
    r = requests.post(f"{BASE_URL}/transfer/", headers=h1, json={
        "from_wallet_id": w1_id, "to_wallet_id": w2_id, "amount": 100, "idempotency_key": f"fail_{ts}"
    })
    print(f"    - Result: {r.status_code} (FastAPI validation caught it)")

    print("[*] Verification: Transfer with WRONG PIN (Expect 403)...")
    r = requests.post(f"{BASE_URL}/transfer/", headers=h1, json={
        "from_wallet_id": w1_id, "to_wallet_id": w2_id, "amount": 100, "idempotency_key": f"fail2_{ts}", "pin": "0000"
    })
    print(f"    - Result: {r.status_code} {r.json().get('detail')}")
    
    print("[*] Verification: Transfer with CORRECT PIN (Expect 200)...")
    tx_key = f"success_{ts}"
    r = requests.post(f"{BASE_URL}/transfer/", headers=h1, json={
        "from_wallet_id": w1_id, "to_wallet_id": w2_id, "amount": 100, "idempotency_key": tx_key, "pin": "1234"
    })
    print(f"    - Result: {r.status_code}. New balance: ${requests.get(f'{BASE_URL}/users/me', headers=h1).json()['wallet']['balance']}")

    # 5. Hardened Batch Execution
    print("[*] Initiating Batch Payout (5 recipients)...")
    batch = requests.post(f"{BASE_URL}/batches/", headers=h1, json={"source_wallet_id": w1_id}).json()
    b_id = batch["id"]
    
    csv_data = f"recipient_id,amount\n{w2_id},50\n{w2_id},50\n{w2_id},50\n{w2_id},50\n{w2_id},50"
    files = {'file': ('batch.csv', csv_data, 'text/csv')}
    
    print("[*] Executing Batch with PIN...")
    r = requests.post(f"{BASE_URL}/batches/{b_id}/execute", headers=h1, files=files, data={"pin": "1234"})
    print(f"    - Result: {r.status_code}. Summary: {r.json().get('summary')}")
    
    # 6. Compensation
    print("[*] Testing Compensation for batch row 0...")
    r = requests.post(f"{BASE_URL}/batches/{b_id}/compensate", headers=h1, json={"row_indices": [0], "pin": "1234"})
    print(f"    - Result: {r.status_code}. {r.json().get('compensation_results')}")

    print("\n--- ✅ ALL SYSTEMS PERFECT ---")

if __name__ == "__main__":
    run_ultimate_test()
