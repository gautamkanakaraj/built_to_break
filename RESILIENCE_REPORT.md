# Resilience & Failure Mode Analysis (Post-Hardening)

While the system is now protected against core financial vulnerabilities like double-spending and negative balances, it still has defined boundaries where it will "fail" or behave in specific ways.

## 🔴 Fixed Vulnerabilities (Will No Longer Fail)
These are now strictly prevented by the hardened logic and DB constraints:
- **Double Spend**: Guaranteed to fail one of the concurrent requests via row-level locking (`FOR UPDATE`).
- **Negative Balances**: Prevented by DB `CHECK` constraints and Pydantic validators.
- **Replay Attacks**: Prevented by `idempotency_key` uniqueness in the ledger.

## 🟠 Strategic Failures (By Design)
These are scenarios where the system "fails" in a controlled, non-destructive way:
- **Partial Batch Execution**: If the server crashes during a 1000-item batch, the batch stops at (e.g.) item 500. This is a "failure" of the automation, but NOT a failure of the ledger. Successes are permanent; failures are untried.
- **Insufficient Funds (Mid-Batch)**: If a batch runs out of source funds at item 10, items 11-100 will fail. The system does not "undo" the first 9 successful transfers to ensure immediate liquidity.

## 🟡 External & Infrastructure Failures
- **Database Availability**: If the Postgres instance goes offline, the system enters a "Hard Fail" state (500 errors). No money can move, preserving integrity.
- **Network Partitions**: Between the backend and database. Handled by SQLAlchemy/Postgres transaction semantics; money remains safe, but requests will timeout.

## 🟢 Operational Boundaries
- **Hot Wallet Latency**: High contention on a single wallet (e.g., a "company wallet" paying 10,000 people at once) will cause performance serialization. Requests will queue up behind the row lock, causing high latency but maintain accuracy.
- **Manual Reversals**: The system cannot "detect" if you sent money to the wrong person. This is a human logic failure. The solution is using the **Compensation API** to reverse the mistake after the fact.

---

### Summary Table
| Scenario | Resulting State | Recovery Method |
| :--- | :--- | :--- |
| **Server Crash mid-batch** | `PROCESSING` (Stalled) | Trigger `/execute` again (Resumability) |
| **Simultaneous Transfer** | 1 Success, 1 Rejected | Client retry (if desired) |
| **DB Constraint Violation** | Transaction Rollback | Correct request data |
| **Wrong Recipient** | Success (Ledger Accurate) | Use `/compensate` endpoint |
