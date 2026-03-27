# Starts the local InsightSQL MCP server on port 5000
if (-not $env:MCP_HOST) {
	$env:MCP_HOST = "0.0.0.0"
}

if (-not $env:MCP_PORT) {
	$env:MCP_PORT = "5000"
}

Write-Host "Starting MCP server on http://localhost:$($env:MCP_PORT)" -ForegroundColor Cyan
python -m mcp.server
