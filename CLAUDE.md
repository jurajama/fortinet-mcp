# Fortinet MCP Server

## Project Overview

MCP (Model Context Protocol) server exposing FortiManager operations as tools for Claude. The server runs on `http://0.0.0.0:8000` with the endpoint at `/mcp`.

## Environment

- Python virtualenv at `venv/` — activate before running: `source venv/bin/activate`
- Configuration in `.env` (not committed to git): `FMG_HOST` and `FMG_API_KEY`
- Python dependencies: `pyFMG`, `mcp[cli]`, `python-dotenv`

## Architecture

### server.py — MCP server (single file)

- Uses **FastMCP** (`mcp.server.fastmcp`) with `streamable-http` transport
- Uses **pyFMG** (`pyFMG.fortimgr.FortiManager`) for FortiManager API access
- Creates a **new FortiManager connection per tool call** via `_fmg_get()` helper — pyFMG's context manager handles login/logout, avoids session timeout issues

### FortiManager API patterns

- pyFMG `fmg.get(endpoint)` returns `(status_code, data)` — status `0` means success
- API key auth with `verify_ssl=False` (self-signed cert on FortiManager)
- `dynamic_mapping` field on metadata variables can be `None`, always use `or []` when iterating

### Key FortiManager API endpoints

- `/dvmdb/adom` — list all ADOMs
- `/dvmdb/adom/{adom}/device` — list devices in an ADOM
- `/pm/config/adom/{adom}/obj/fmg/variable` — metadata variables for an ADOM

## Adding New Tools

1. Add a new function decorated with `@mcp.tool()` in `server.py`
2. Use `_fmg_get(endpoint)` for read operations
3. For write operations, create a `_fmg_set()` or `_fmg_execute()` helper following the same pattern (new connection per call)
4. Return structured dicts/lists — FastMCP handles serialization
5. Write clear docstrings — Claude uses them to understand when and how to call the tool

## Running

```bash
source venv/bin/activate
python server.py
```

## Testing

Smoke test with curl:
```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```
