# MCP Platform

Run ContextForge and custom MCP servers with one Docker Compose command.

## Project structure

```text
mcp-platform/
├── docker-compose.yml    # Main entry point; includes ContextForge services
├── .env                  # Symlink to contextforge/.env
├── contextforge/         # ContextForge Gateway, UI, and infrastructure
└── mcps/
    ├── register.py       # Automatic MCP registration
    ├── add/              # Integer addition MCP
    └── dates/            # Date calculation MCP
```

## Setup

Requirements: Docker Desktop with Compose `include` support, `uv`, and `make`.
Start Docker Desktop before running these commands.

From the `mcp-platform` directory, initialize configuration if needed:

```bash
make -C contextforge setup
ln -s contextforge/.env .env
```

The root `.env` points to `contextforge/.env`. Set these values in that file for local development:

```dotenv
GUNICORN_WORKERS=2
GATEWAY_REPLICAS=1
COMPOSE_PROFILES=ui
```

Build and start the stack:

```bash
docker compose up -d --build
```

Open:

- [Admin UI](http://localhost:8080/admin/): manage gateways, tools, and virtual servers.
- [Web UI](http://localhost:3001): separate frontend for ContextForge.

Use `PLATFORM_ADMIN_EMAIL` and `PLATFORM_ADMIN_PASSWORD` from `.env` to sign in.

## Example MCP servers

The stack starts `fast_time_server`, `add_mcp`, and `dates_mcp`.
Registration services automatically add the custom MCP servers and create their virtual servers.
Registration containers exit successfully after setup; they do not need to stay running.

| Virtual server | Tool | Example arguments | Result |
| --- | --- | --- | --- |
| Add MCP | `add` | `{"a": 10, "b": 20}` | `30` |
| Dates MCP | `days_between` | `{"start_date": "2026-11-20", "end_date": "2026-11-25"}` | `5` |

Custom MCP containers share the internal Docker network with ContextForge and do not publish host ports.

## Daily commands

```bash
# Start all services
docker compose up -d

# Check services, including completed registration jobs
docker compose ps -a

# View custom MCP logs
docker compose logs -f add_mcp dates_mcp

# Rebuild after changing an MCP server
docker compose up -d --build add_mcp dates_mcp

# Stop the stack and retain database volumes
docker compose down
```

Run commands from `mcp-platform`, using the root Compose file.
To add another MCP, create a folder under `mcps/` and add its server and registration services to `docker-compose.yml`.
If tool definitions change, refresh the gateway tools in Admin UI and update the virtual server's selected tools.
