# Expected Failures (Build Phase)

The following test cases are **guaranteed to fail** (or rather, succeed in breaking the system) due to the intentional lack of concurrency controls.

## 1. The Double-Spend Attack (Race Condition)
**Scenario:**
- User A has Balance **100.00**.
- User A sends **50.00** to User B (Request 1).
- AT THE EXACT SAME TIME, User A sends **50.00** to User C (Request 2).
- AT THE EXACT SAME TIME, User A sends **50.00** to User D (Request 3).

**Expected (Correct) Behavior:**
- 2 transfers succeed.
- 1 transfer fails ("Insufficient funds").
- Final Balance: **0.00**.

**Actual (Vulnerable) Behavior:**
- All 3 transfers verify `balance (100) >= 50` successfully.
- All 3 transfers subtract 50.
- Final Balance: **-50.00**.
- **RESULT: FAILED (Double Spend Executed)**

## 2. The Negative Balance Deposit
**Scenario:**
- User attempts to create a transfer of **-1000.00** (Negative amount).

**Expected (Correct) Behavior:**
- Rejected by validator (`amount > 0`).

**Actual Behavior (Build Phase):**
- Pydantic schema validation *might* catch this if `gt=0` is set, but if logic depends on `transfer` function, it might just credit the sender and debit receiver.
- *Note: Our `transfer_vulnerable` logic does NOT explicitly check `amount > 0` in python code, hoping Pydantic does, or assuming sequential trust. This is another vector.*

## 3. Replay Attack
**Scenario:**
- Captured API request for a valid transfer is sent again 1 second later.

**Expected (Correct) Behavior:**
- Rejected (Idempotency Key used/Transaction ID duplicate).

**Actual Behavior:**
- Transfer executed again. Money moved twice.

## 4. Read Skew (Reporting)
**Scenario:**
- Admin requests "Total System Balance".
- During the read, a transfer moves money from Wallet A (already read) to Wallet B (not yet read).

**Result:**
- The report misses the money in B or counts it twice depending on read order.
