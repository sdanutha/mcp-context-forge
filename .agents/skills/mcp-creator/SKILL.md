---
name: mcp-creator
description: Create a new MCP server under mcps/, or integrate an existing MCP implementation, then deploy, register, and verify it through the ContextForge Gateway. Use when asked to add, create, build, or integrate an MCP server.
---

# mcp-creator

Deliver an MCP server that follows this repository's rules and is proven working through a ContextForge virtual server.

## Rules

`AGENTS.md` at the repository root is the single source of truth: read its sections "Protected: contextforge/", "Add an existing MCP implementation", "Compose template", and "Validation and completion" before step 1. When this skill and `AGENTS.md` differ, `AGENTS.md` wins.

Edits land only in `mcps/<name>/`, the root `docker-compose.yml`, and the root `README.md`.

## Steps

Work the steps in order. Each ends on a completion criterion; meet it before moving on.

### 1. Intake

Decide the mode: **new** (author the server here) or **existing** (the user supplies code to integrate).

Settle these with the user, asking for any that are missing:

- `<name>`: lowercase, one word or snake_case. Folder `mcps/<name>/`, Compose services `<name>_mcp` and `register_<name>_mcp`, registered gateway `<name>-mcp`, virtual server `<Display Name> MCP`.
- Tools: each tool's name, arguments, result, and error cases.
- Runtime configuration and secrets, and any external service the server calls.

Done when the name, folder, tool list (arguments, result, error cases), and configuration needs are written down in your reply.

### 2. Implement

**New:** mirror `mcps/add/`: `server.py` plus `Dockerfile`.

- `FastMCP(..., host="0.0.0.0", port=8001, stateless_http=True, json_response=True)`, served with `transport="streamable-http"`.
- One `@mcp.tool()` per tool, with type hints and a docstring covering arguments, result, and errors.
- Invalid input raises `ValueError` (or another plain exception) so the tool call returns an error and the server keeps running.
- A `/health` route through `@mcp.custom_route("/health", methods=["GET"])`.
- Dockerfile identical in shape to `mcps/add/Dockerfile`: same base image, same pinned `mcp` version, non-root user `10001`, `EXPOSE 8001`.

**Existing:** follow `AGENTS.md` steps 1 to 4 and keep the supplied implementation intact.

Done when the MCP path (`/mcp`), port, and readiness endpoint are identified and `docker compose build <name>_mcp` succeeds (run it after step 3).

### 3. Compose

Append the two services from the `AGENTS.md` "Compose template" at the end of `docker-compose.yml`, below the existing registration services so the `mcp_registration` and `registration_environment` anchors are already defined.

Done when `docker compose config --quiet` passes and both services are on `mcpnet`.

### 4. README

Add the MCP to the example table (virtual server, tool, example arguments, result) and to the `docker compose build` command in the root `README.md`.

Done when both README spots list the new MCP.

### 5. Verify

Run the `AGENTS.md` validation commands, then prove each completion check with observed output. Use [verify-tool-call.sh](verify-tool-call.sh) for the tool calls; it resolves the virtual server by name, opens an MCP session on the Gateway (`http://localhost:4444`), and prints the JSON-RPC response:

```bash
.agents/skills/mcp-creator/verify-tool-call.sh "<Display Name> MCP" --list
.agents/skills/mcp-creator/verify-tool-call.sh "<Display Name> MCP" <gateway-tool-name> '{"arg": "value"}'
```

- Gateway tool names are `<MCP_NAME>-<tool>` with underscores turned into hyphens: tool `days_between` on `dates-mcp` is `dates-mcp-days-between`. Take the exact name from the `--list` output.
- Invalid input: call a tool with a bad argument, then confirm the response is an error and `docker compose ps` still shows the container healthy.
- Repeat registration with `docker compose up -d register_<name>_mcp`, then confirm one gateway and one virtual server carry the name (`GET /gateways`, `GET /servers`).
- Run an existing MCP's tool through its virtual server to confirm nothing regressed.

Done when each `AGENTS.md` completion check has observed evidence, or is listed as unverified with the reason (for example Docker not running, or `.env` missing, which README step 2 creates).

### 6. Report

Reply with the files changed and a checklist of the completion checks, each marked verified or unverified. Commit and push only when the user asks.
