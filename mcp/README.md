## MCP (Fabric + PostgreSQL)

### Install

```powershell
uv pip install --python venv/Scripts/python.exe -r pyproject.toml
./venv/Scripts/python.exe -m uvicorn src.server:app --host 0.0.0.0 --port 8000
```

### Run server

```powershell
uvicorn src.server:app
```

Server endpoints:
- MCP JSON-RPC (streamable HTTP): `http://localhost:8000/mcp`
- Health: `http://localhost:8000/health`

### Standalone smoke test (without backend)

Start MCP first and then run:

```powershell
python scripts/smoke_test_mcp.py --base-url http://localhost:8000 --postgres-schema public
```

This smoke test validates:
- `health`
- `get_current_source`
- `switch_data_source` to `fabric` and `postgres`
- `list_fabric_tables` and `list_postgres_tables`
- basic read-only `query` on both sources