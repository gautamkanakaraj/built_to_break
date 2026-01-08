# G-Wallet (Hardened Rebuild Phase)

This project contains a **production-hardened** wallet transaction engine designed to resist concurrency anomalies, race conditions, and adversarial attacks. It now includes a **Batch Payouts Layer** for high-volume transaction coordination. 
video link :
https://vimeo.com/1152641810?share=copy&fl=sv&fe=ci

## 🌐 Live Application (Judge Access)
> [!IMPORTANT]
> **Live Demo**: [https://commemorational-believingly-azaria.ngrok-free.dev](https://commemorational-believingly-azaria.ngrok-free.dev)
> (Note: This link is active while the developer tunnel is open).

---

## 🛡️ Hardening Features (ACID Guaranteed)

1.  **Concurrency Safety**: Uses pessimistic row-level locking (`SELECT ... FOR UPDATE`) with deterministic ordering to prevent deadlocks and double-spending.
2.  **Atomicity**: Every transfer is a single, atomic database transaction. Internal `CheckConstraint` ensures balances never go negative.
3.  **Idempotency**: Forced request-level idempotency via a unique `idempotency_key` enforced at the database layer.
4.  **JWT Authentication**: All transfer operations require a valid JWT token to identify the caller.
5.  **Isolation**: Prevents Read Skew using atomic bulk-read endpoints for multi-wallet state checks.

---

## 📦 Mass Payouts (Batch Execution)

The system includes a batch coordination layer allowing users to execute hundreds of payouts via a single CSV upload.

- **Hardened Batch Coordination**: Resumable, state-tracked batch processing with row-level transparency.
- **Transaction PIN Authorization**: Mandatory 4-digit PIN for all money-moving operations to protect against compromised JWTs.

### Hardened Batch Flow:
1.  **Create Batch**: Define a source wallet and an optional **Batch Idempotency Key** to prevent duplicate CSV submissions.
2.  **Upload & Sync**: Provide a CSV. The engine syncs every row into a tracking table before execution.
3.  **Execute with Resumability**: If the server crashes, execution can be resumed from the `last_processed_row`.
4.  **Monitor Status**: Track states: `PENDING` → `PROCESSING` → `COMPLETED` or `PARTIALLY_FAILED`.
5.  **Authorization**: Execute payouts. Requires **Transaction PIN** for final approval.
6.  **Compensation**: Programmatically reverse specific rows if needed (Requires PIN).

### CSV Format:
```csv
recipient_id,amount
2,50.00
3,125.50
4,10.00
```

---

## 🚀 Getting Started

### 1. Run the Hardened Engine
Ensure you have Docker and Docker Compose installed.

```bash
# Clean start (recommended to apply schema changes)
docker-compose -f infra/docker-compose.yml down -v
docker-compose -f infra/docker-compose.yml up --build -d
```

*   **Premium Web UI**: [http://localhost:3000](http://localhost:3000)
*   **Interactive API Docs**: [http://localhost:4000/docs](http://localhost:4000/docs)

### 2. Deployment Independence (Judge-Ready)
> [!IMPORTANT]
> **This project is fully independent of the local developer machine.** 
> Judges can deploy the complete G-Wallet environment on any cloud instance (AWS, GCP, DigitalOcean) or local Linux server without needing the source code. The engine is served via pre-built public images on Docker Hub.

#### Self-Service Deployment for Evaluators
For a quick, reproducible evaluation on a remote server, use the pre-built images from Docker Hub.

**Create a `docker-compose.yml` with the following:**
```yaml
version: '3.9'
services:
  backend:
    image: gautamkanakaraj/g-wallet-backend:latest
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/wallet_db
    depends_on:
      - db
    restart: always

  frontend:
    image: gautamkanakaraj/g-wallet-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - BACKEND_URL=http://backend:4000
    depends_on:
      - backend
    restart: always

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=wallet_db
    restart: always
```

**Run command:**
```bash
docker-compose up -d
```
The system will be accessible at `http://<server-ip>:3000`.

### 3. Run Verification Suite
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
- [ARCHITECTURE.md](ARCHITECTURE.md): Comprehensive system architecture, hardening journey, and database schema.
- [ui_guide.md](ui_guide.md): field-level guide for the Control Panel UI.
- [EXPECTED_FAILURES.md](EXPECTED_FAILURES.md): Detailed scenarios of race conditions and vulnerabilities.

## 🛠 Tech Stack
- **FastAPI**: Modern high-performance web framework.
- **PostgreSQL**: Robust relational database for strong consistency.
- **SQLAlchemy 2.0**: Type-safe ORM with transaction support.
- **python-jose**: JWT security implementation.
