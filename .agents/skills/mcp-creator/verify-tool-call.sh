#!/usr/bin/env bash
# Call one tool (or list tools) on a ContextForge virtual server and print the JSON-RPC response.
# Run from the repository root with the stack up.
#
# Usage:
#   verify-tool-call.sh "<virtual server name>" --list
#   verify-tool-call.sh "<virtual server name>" <gateway tool name> '<json arguments>'
set -euo pipefail

NAME=${1:?virtual server name}
TOOL=${2:?gateway tool name or --list}
ARGS=${3-}
[ -n "$ARGS" ] || ARGS='{}'
GATEWAY=${GATEWAY_URL:-http://localhost:4444}

TOKEN=$(docker compose exec -T gateway sh -c \
  'python3 -m mcpgateway.utils.create_jwt_token --username "$PLATFORM_ADMIN_EMAIL" --admin --exp 30' 2>/dev/null | tail -1)
[ -n "$TOKEN" ] || { echo "Could not create a token; is the gateway running?" >&2; exit 1; }

SERVER_ID=$(curl -fsS -H "Authorization: Bearer $TOKEN" "$GATEWAY/servers" | python3 -c '
import json, sys
name = sys.argv[1]
data = json.load(sys.stdin)
items = data.get("items", data) if isinstance(data, dict) else data
print(next((s["id"] for s in items if s["name"] == name), ""))' "$NAME")
[ -n "$SERVER_ID" ] || { echo "No virtual server named '$NAME'." >&2; exit 1; }

URL="$GATEWAY/servers/$SERVER_ID/mcp"
HEADERS=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream")

SESSION=$(curl -fsS -D - -o /dev/null "${HEADERS[@]}" "$URL" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"mcp-creator","version":"1"}}}' \
  | awk -F': ' 'tolower($1)=="mcp-session-id"{print $2}' | tr -d '\r')
[ -n "$SESSION" ] || { echo "MCP initialize returned no session id." >&2; exit 1; }
HEADERS+=(-H "Mcp-Session-Id: $SESSION")

curl -fsS "${HEADERS[@]}" "$URL" -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' >/dev/null

if [ "$TOOL" = "--list" ]; then
  PAYLOAD='{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
else
  PAYLOAD=$(python3 -c '
import json, sys
print(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                  "params": {"name": sys.argv[1], "arguments": json.loads(sys.argv[2])}}))' "$TOOL" "$ARGS")
fi
curl -sS "${HEADERS[@]}" "$URL" -d "$PAYLOAD"
echo
