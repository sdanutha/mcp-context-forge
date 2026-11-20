"""Expose date calculations through MCP Streamable HTTP."""

from datetime import date

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP(
    "Dates MCP", host="0.0.0.0", port=8001, stateless_http=True, json_response=True
)


@mcp.tool()
def days_between(start_date: str, end_date: str) -> int:
    """Return the signed number of days from start_date to end_date.

    Dates use YYYY-MM-DD. An earlier end date returns a negative result.
    Invalid dates raise ValueError.
    """
    return (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Return container readiness."""
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
