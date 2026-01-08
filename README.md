# Wallet Engine (Build Phase)

This project contains a **baseline** wallet transaction engine.

**⚠️ WARNING: INTENTIONALLY VULNERABLE ⚠️**

This system is designed for the "Build Phase" of the Build2Break hackathon.

## Known Limitations (By Design)

1.  **Race Conditions**: Simultaneous transfers from the same wallet can double-spend.
2.  **No Isolation**: Transactions are not isolated; read-skews are possible.
3.  **No Locking**: Database rows are not locked during updates.
4.  **No Idempotency**: Replaying requests will duplicate transactions.

## Quick Start

### 1. Run the Engine
```bash
docker-compose up --build
```
*   **Web UI**: [http://localhost:8000](http://localhost:8000)
*   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

> **Troubleshooting**: If you see `KeyError: 'ContainerConfig'` or build errors, run this instead:
> ```bash
> # Force legacy builder and clean orphans
> docker-compose down -v --remove-orphans
> DOCKER_BUILDKIT=0 docker-compose up --build
> ```

### 2. Verify Vulnerabilities
To confirm the engine is working (and vulnerable) as expected, run the failure test:
```bash
python3 tests/test_failures.py
```

## Architecture

- **FastAPI**: Backend
- **PostgreSQL**: Database
- **SQLAlchemy**: Synchronous ORM
