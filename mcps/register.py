"""Register a local MCP server and its virtual server without printing tokens."""

import asyncio
import json
import os
import time
import urllib.error
import urllib.request

from mcpgateway.utils.create_jwt_token import create_jwt_token


def register() -> None:
    """Register the configured MCP server and expose its discovered tools.

    Raises:
        RuntimeError: Registration does not complete within the retry limit.
    """
    email = os.environ["PLATFORM_ADMIN_EMAIL"]
    token = asyncio.run(
        create_jwt_token(
            {"sub": email, "email": email, "is_admin": True},
            expires_in_minutes=10,
            teams=None,
            user_data={"email": email, "is_admin": True},
        )
    )

    def request(method: str, path: str, payload: dict | None = None):
        """Send an authenticated request to the gateway.

        Args:
            method: HTTP method.
            path: Gateway API path.
            payload: Optional JSON payload.

        Returns:
            The decoded JSON response.
        """
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            os.environ["GATEWAY_URL"] + path,
            data=data,
            method=method,
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    for attempt in range(60):
        try:
            gateways = request("GET", "/gateways")
            gateway = next(
                (item for item in gateways if item["name"] == os.environ["MCP_NAME"]),
                None,
            )
            if gateway is None:
                gateway = request(
                    "POST",
                    "/gateways",
                    {
                        "name": os.environ["MCP_NAME"],
                        "url": os.environ["MCP_URL"],
                        "transport": "STREAMABLEHTTP",
                    },
                )
            gateway_id = gateway["id"]
            tools = request("GET", "/tools")
            tool_ids = [
                item["id"]
                for item in tools
                if item.get("gatewayId", item.get("gateway_id")) == gateway_id
            ]
            if not tool_ids:
                request(
                    "POST",
                    f"/gateways/{gateway_id}/tools/refresh?include_resources=true&include_prompts=true",
                )
                raise RuntimeError("Tool discovery is pending")
            servers = request("GET", "/servers")
            server = next(
                (
                    item
                    for item in servers
                    if item["name"] == os.environ["VIRTUAL_SERVER_NAME"]
                ),
                None,
            )
            if server is None:
                server = request(
                    "POST",
                    "/servers",
                    {
                        "server": {
                            "name": os.environ["VIRTUAL_SERVER_NAME"],
                            "description": os.environ.get(
                                "VIRTUAL_SERVER_DESCRIPTION",
                                "Integer addition MCP tools",
                            ),
                            "associated_tools": tool_ids,
                        }
                    },
                )
            print(
                f"Registered {os.environ['MCP_NAME']}: {len(tool_ids)} tools; virtual server {server['id']}",
                flush=True,
            )
            return
        except urllib.error.HTTPError as error:
            print(f"Registration attempt {attempt + 1}: HTTP {error.code}", flush=True)
            if error.code not in (401, 409, 429, 500, 502, 503, 504):
                raise RuntimeError(
                    f"Registration rejected: HTTP {error.code}"
                ) from None
        except (urllib.error.URLError, TimeoutError, RuntimeError):
            print(
                f"Registration attempt {attempt + 1}: gateway or tools are not ready",
                flush=True,
            )
        time.sleep(2)
    raise RuntimeError("Registration did not complete within the retry limit")


if __name__ == "__main__":
    register()
