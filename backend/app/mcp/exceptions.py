class MCPConnectionError(Exception):
    """Raised when MCP client cannot reach server."""


class MCPToolError(Exception):
    """Raised when MCP tool invocation fails."""


class MCPTimeoutError(Exception):
    """Raised when MCP invocation times out."""
