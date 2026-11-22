# NeoMCP

Run ContextForge and custom MCP servers with one Docker Compose command.

## Project structure

```text
neomcp/
├── docker-compose.yml    # The only Compose file: ContextForge, Web UI, and MCP servers
├── .env                  # Symlink to contextforge/.env
├── contextforge/         # ContextForge source, plugin config, and MCP catalog
└── mcps/
    ├── register.py       # Automatic MCP registration
    ├── add/              # Integer addition MCP
    └── dates/            # Date calculation MCP
```

## Setup

Requirements: Docker Desktop with Compose v2 and `uv`.
Start Docker Desktop before running these commands.
These steps assume you have already cloned the repository and are in its root folder.
Keep your existing `.env` when updating an existing installation.

### 1. Configure secrets

```bash
cp contextforge/.env.example contextforge/.env
ln -s contextforge/.env .env

# Use Python 3.12 instead of the macOS system Python.
(
  cd contextforge
  uv run --no-project --python 3.12 --with python-dotenv \
    python -m mcpgateway.scripts.init_secrets --patch-env .env
)
```

Secret initialization replaces weak values for `JWT_SECRET_KEY`, `AUTH_ENCRYPTION_SECRET`, and the configured passwords.
The root `.env` is a symlink to `contextforge/.env`; both paths refer to the same configuration.

### 2. Start the stack

```bash
docker compose up -d
```

The first run builds the custom MCP images from `mcps/` and pulls the other images.
Every image uses a pinned version tag; the Gateway version is set once by `x-gateway-image` at the top of `docker-compose.yml`.

### 3. Check status

```bash
docker compose ps -a
```

Registration and migration jobs exit with code `0` after completing their work.

### 4. View logs

```bash
docker compose logs -f gateway
```

### 5. Open the UI

Open the [Web UI](http://localhost:3001/app/) to manage MCP servers, tools, virtual servers, users, and tokens.
Sign in with `PLATFORM_ADMIN_EMAIL` and `PLATFORM_ADMIN_PASSWORD` from `.env`.

| Host port | Service | Use |
| --- | --- | --- |
| `3001` | `web_ui` | Web UI, the only management UI |
| `4444` | `gateway` | Gateway API and virtual server MCP endpoints |

The stack has no nginx and no legacy Admin UI at `/admin`; both are removed in [docker-compose.yml](docker-compose.yml).

## Example MCP servers

The stack starts `add_mcp` and `dates_mcp`.
Registration services automatically add them to ContextForge and create their virtual servers.
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

Run commands from `neomcp`, using the root Compose file.
To add another MCP, create a folder under `mcps/` and add its server and registration services to `docker-compose.yml`.
If tool definitions change, refresh the MCP server's tools in the Web UI and update the virtual server's selected tools.
