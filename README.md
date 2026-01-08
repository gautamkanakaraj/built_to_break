# G-Wallet (Hardened Rebuild Phase)

This project contains a **production-hardened** wallet transaction engine designed to resist concurrency anomalies, race conditions, and adversarial attacks.

## 🛡️ Hardening Features (ACID Guaranteed)

1.  **Concurrency Safety**: Uses pessimistic row-level locking (`SELECT ... FOR UPDATE`) with deterministic ordering to prevent deadlocks and double-spending.
2.  **Atomicity**: Every transfer is a single, atomic database transaction. Internal `CheckConstraint` ensures balances never go negative.
3.  **Idempotency**: Forced request-level idempotency via a unique `idempotency_key` enforced at the database layer.
4.  **JWT Authentication**: All transfer operations require a valid JWT token to identify the caller.
5.  **Isolation**: Prevents Read Skew using atomic bulk-read endpoints for multi-wallet state checks.

---

## 🚀 Getting Started

### 1. Run the Hardened Engine
Ensure you have Docker and Docker Compose installed.

```bash
# Clean start (recommended to apply schema changes)
docker-compose down -v
docker-compose up --build -d
```

*   **Premium Web UI**: [http://localhost:8000](http://localhost:8000)
*   **Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Run Verification Suite
We have provided specialized scripts to prove the engine's resilience against build-phase failures.

```bash
# Verify Idempotency (Replay Attack Protection)
python3 test_idempotency.py

# Verify Atomicity (Partial Commit Protection)
python3 test_atomicity.py

# Verify Isolation (Read Skew Protection)
python3 isolation_test.py
```

---

## 📖 Documentation
Detailed architectural analysis and failure mapping:
- [document2.txt](document2.txt): Hardened Architecture & failure-to-fix mapping.
- [document.txt](document.txt): Analysis of the original build-phase vulnerabilities (for comparison).

## 🛠 Tech Stack
- **FastAPI**: Modern high-performance web framework.
- **PostgreSQL**: Robust relational database for strong consistency.
- **SQLAlchemy 2.0**: Type-safe ORM with transaction support.
- **python-jose**: JWT security implementation.
