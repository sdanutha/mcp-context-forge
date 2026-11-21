# Agent instructions

Write responses, comments, and documentation in English.

## Scope and layout

This repository runs ContextForge and custom MCP servers through the root `docker-compose.yml`.

- Put custom MCP implementations under `mcps/<name>/`.
- Keep ContextForge application code under `contextforge/`; see "Protected: contextforge/" below.
- Reuse `mcps/register.py` for automatic registration.
- Keep one Git repository at the project root.
- Keep secrets in the ignored `.env`, which links to `contextforge/.env`.

## Protected: contextforge/

`contextforge/` is the main upstream code project, a copy of the IBM ContextForge repository.
Do not modify anything in it. Only the user may change it, for example to update it to the current upstream version.

- Do not edit, add, delete, rename, or reformat files under `contextforge/`, including its Compose files, Containerfile, plugins, catalog, docs, and tests.
- Do all platform and MCP work outside it: in `mcps/`, the root `docker-compose.yml`, and the root `README.md`.
- Change Gateway behavior through the root `docker-compose.yml` (environment variables, ports, mounts) instead of patching `contextforge/`.
- Read `contextforge/` freely to understand its behavior and settings.
- The ignored `contextforge/.env` secrets file is the one exception: it is local configuration, not upstream code, and it is not committed.
- If a task seems to need a change inside `contextforge/`, stop and tell the user what is needed and why. Do not make the change.

## Add an existing MCP implementation

1. Inspect the supplied code, dependencies, startup command, transport, required configuration, and external service requirements.
   Preserve the supplied implementation and its dependency manifests.
   Use `mcps/add/` and `mcps/dates/` as deployment references.

2. Copy the implementation into `mcps/<name>/`.
   Exclude nested `.git` directories, secrets, virtual environments, caches, and generated output.
   Keep runtime assets and dependency lockfiles required by the implementation.

3. Add or adapt its Dockerfile.
   Install dependencies from its manifests, copy required files, and configure the correct working directory and startup command.
   Preserve the implementation's language and runtime.
   Run as a non-root user when supported.

4. Expose MCP through Streamable HTTP.
   Bind to `0.0.0.0` inside the container.
   Confirm the actual MCP path and port; existing examples use `/mcp` on port `8001`.
   For a stdio-only implementation, use `mcpgateway.translate` as an HTTP adapter instead of treating a CLI as an HTTP server.
   Provide a lightweight readiness endpoint or another reliable container health check.

5. Add the server and registration services to the root `docker-compose.yml`.
   Use the template below, replacing the service name, folder, image, display names, port, and paths.
   Keep service names unique and stable.
   Place both services on `mcpnet`.
   Internal MCP services need no published host ports.

6. Reuse the registration anchors from the same Compose file.
   Override the dependency map so registration waits for the new MCP and Gateway health checks.
   Merge `registration_environment` before setting the new MCP values.
   Pass runtime configuration through environment variables or secret mounts.
   Keep token creation and authentication in the shared registration script.
   If upstream MCP authentication is required, extend the shared registration flow to support it before declaring integration complete.

7. Validate the integration using the checks below.
   Update the root README example table and explicit image-build command to include the new MCP.

## Compose template

Add this under the root `services:` mapping, after the existing registration anchors:

```yaml
  example_mcp:
    build: ./mcps/example
    image: mcp-platform/example:local
    restart: unless-stopped
    networks: [mcpnet]
    healthcheck:
      test: [CMD, python, -c, "import urllib.request; urllib.request.urlopen('http://localhost:8001/health', timeout=3)"]
      interval: 5s
      timeout: 4s
      retries: 12

  register_example_mcp:
    <<: *mcp_registration
    depends_on:
      gateway:
        condition: service_healthy
      example_mcp:
        condition: service_healthy
    environment:
      <<: *registration_environment
      MCP_NAME: example-mcp
      MCP_URL: http://example_mcp:8001/mcp
      VIRTUAL_SERVER_NAME: Example MCP
      VIRTUAL_SERVER_DESCRIPTION: Describe the tools provided by this MCP
```

The sample health check requires Python inside the image. Adapt it to the actual runtime.
`MCP_URL` uses the Compose service hostname, not `localhost` or a host-published port.
The shared registrar currently supports `STREAMABLEHTTP` and creates missing gateways and virtual servers by name.
It reuses existing virtual servers; it does not update their selected tools automatically.
For changed tool definitions, refresh Gateway tools and update the virtual server's tool selection explicitly.

## Validation and completion

Run commands from the repository root. Replace `example_mcp` with the new service name.

```bash
docker compose config --quiet
docker compose build example_mcp
docker compose up -d example_mcp register_example_mcp
docker compose ps -a
docker compose logs --tail=50 example_mcp register_example_mcp
```

Integration is complete when all of these checks pass:

- The MCP container is healthy and the registration job exits with code `0`.
- ContextForge discovers the expected tools and creates the intended virtual server.
- An actual tool call through the ContextForge virtual server returns the expected result.
- Invalid input produces the expected error without crashing the MCP server.
- Repeating registration reuses the gateway and virtual server without creating duplicates.
- Existing MCP services still work, and `docker compose up -d` includes the new MCP without extra profiles.

If Docker or an external dependency is unavailable, report the missing verification instead of claiming runtime success.
