# Fortinet MCP Server

An MCP (Model Context Protocol) server that exposes FortiManager operations as tools for Claude. Built with Python using the FastMCP SDK and pyFMG library.

## Available Tools

- **list_adoms** — List all ADOMs (Administrative Domains) on FortiManager
- **list_devices** — List all devices in a given ADOM (name, serial, platform, connection status)

## Prerequisites

### Claude Code CLI

Native install (recommended, no Node.js required):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

This auto-updates in the background. See https://code.claude.com/docs/en/setup for details.

### Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install pyFMG "mcp[cli]" python-dotenv
```

## Configuration

Create a `.env` file in the project root:

```
FMG_HOST=your-fortimanager-hostname
FMG_API_KEY=your-api-key
```

## Starting the Server

```bash
source venv/bin/activate
python server.py
```

The server listens on `http://0.0.0.0:8000` with the MCP endpoint at `/mcp`.

## Connecting Claude Code

Register the MCP server with Claude Code:

```bash
claude mcp add fortinet-fmg --transport http http://localhost:8000/mcp
```

Then launch Claude Code:

```bash
cd /path/to/fortinet-mcp
claude
```

Claude can now call the FortiManager tools directly, e.g. "list the ADOMs on FortiManager".
