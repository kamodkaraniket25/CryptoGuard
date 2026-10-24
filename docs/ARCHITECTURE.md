# CryptoGuard architecture

CryptoGuard is a local academic web application. The browser never performs the cryptographic checks or the vulnerability queries itself. It sends requests to a FastAPI backend. The backend hashes files, computes HMAC tags, signs and verifies messages, reads manifests, builds SBOMs, and talks to external data sources.

## Components

- **React frontend** (`frontend/`): pages, forms, tables, and charts. It calls the backend with Axios.
- **FastAPI backend** (`backend/app/`): validation, cryptography, manifest parsing, OSV and optional NVD clients, SBOM generation, and history.
- **SQLite database** (`backend/data/cryptoguard.db`): verification history, vulnerability-query cache, and source-status checks.
- **Vendored CycloneDX schema** (`backend/app/data/bom-1.7.schema.json`): used offline to validate generated SBOMs.

## Data flow

1. A person chooses a file, message, key, or manifest in the browser.
2. The browser sends that input to a `/api/...` endpoint.
3. The backend checks the size and shape of the input.
4. Cryptographic work uses Python's `hashlib`, `hmac`, `secrets`, and the `cryptography` library.
5. Vulnerability work, when requested, sends only a package name, ecosystem, and exact version to OSV. It does not send file bytes, messages, HMAC secrets, or private keys.
6. A sanitized summary is stored in SQLite. The HTTP response returns the full result for that request, including secrets or private keys when the user just generated them. Those values are not written to the database.
7. The dashboard reads the stored summaries. It does not invent counts.

## Database design

SQLAlchemy models live in `backend/app/models/tables.py`. The application creates tables on startup with `Base.metadata.create_all`. Alembic is not used. The database URL is configurable, so a later PostgreSQL deployment can supply a different SQLAlchemy URL and driver without rewriting the models.

Timestamps are stored in UTC. Indexes cover operation id, operation type, status, cache identity, and source-check time.

## Security boundaries

- The browser is untrusted input.
- The backend is the trust boundary for validation, file-size limits, and external calls.
- OSV, NVD, and the CycloneDX schema host are external networks. Their responses are data, not instructions.
- Private keys and HMAC secrets cross the network only between the user's browser and the user's own backend. The intended deployment is localhost.

See `docs/SECURITY_MODEL.md` for the threat model.
