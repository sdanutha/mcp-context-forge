"""Expose integer addition through MCP Streamable HTTP."""

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP(
    "Add MCP", host="0.0.0.0", port=8001, stateless_http=True, json_response=True
)


@mcp.tool()
def add(a: int, b: int) -> int:
    """Return the sum of two integers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The sum of both integers.
    """
    return a + b


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Return readiness for the container health check.

    Args:
        request: Incoming health request.

    Returns:
        The readiness response.
    """
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
