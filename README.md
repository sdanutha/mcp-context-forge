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

Requirements: Docker Desktop with Compose `include` support and `uv`.
Start Docker Desktop before running these commands.
These steps assume a fresh clone. Keep your existing `.env` when updating an existing installation.

### 1. Clone the repository

```bash
git clone https://github.com/sdanutha/mcp-context-forge.git mcp-platform
cd mcp-platform
```

### 2. Configure secrets and pull the Gateway image

```bash
cp contextforge/.env.example contextforge/.env
ln -s contextforge/.env .env

# Use Python 3.12 instead of the macOS system Python.
(
  cd contextforge
  uv run --no-project --python 3.12 --with python-dotenv \
    python -m mcpgateway.scripts.init_secrets --patch-env .env
)

# Pull the pre-built Gateway image; no local Gateway build is required.
docker pull ghcr.io/ibm/mcp-context-forge:latest

# Use the image for the Gateway, migrations, and registration jobs.
cat >> .env <<'ENV'

IMAGE_LOCAL=ghcr.io/ibm/mcp-context-forge:latest
GUNICORN_WORKERS=2
GATEWAY_REPLICAS=1
COMPOSE_PROFILES=ui
ENV
```

Secret initialization replaces weak values for `JWT_SECRET_KEY`, `AUTH_ENCRYPTION_SECRET`, and the configured passwords.
The root `.env` is a symlink to `contextforge/.env`; both paths refer to the same configuration.

### 3. Build local images and start the stack

Nginx and the two custom MCP servers need local builds. Other images are pulled as needed.

```bash
docker compose build nginx add_mcp dates_mcp
docker compose up -d --no-build
```

### 4. Check status

```bash
docker compose ps -a
```

Registration and migration jobs exit with code `0` after completing their work.

### 5. View logs

```bash
docker compose logs -f gateway
```

### 6. Open the UI

- [Admin UI](http://localhost:8080/admin/): manage gateways, tools, and virtual servers.
- [Web UI](http://localhost:3001): separate frontend for ContextForge.

Sign in with `PLATFORM_ADMIN_EMAIL` and `PLATFORM_ADMIN_PASSWORD` from `.env`.

### 7. Generate an API token (optional)

Use Admin UI to create a token with the required team and permissions.
For local development, this command generates an administrator token that expires after seven days:

```bash
docker compose exec gateway sh -c \
  'python3 -m mcpgateway.utils.create_jwt_token --username "$PLATFORM_ADMIN_EMAIL" --admin --exp 10080'
```

The command uses the signing configuration inside the Gateway container.
It prints the token; keep it private and use it as an `Authorization: Bearer` header.

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
