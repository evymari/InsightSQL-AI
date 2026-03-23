## Ejecutar el servicio DAB en Docker

```bash
docker compose -f dab/docker-compose.yml up
docker compose -f dab/docker-compose.yml down
```

## Ver la configuración del servicio
```bash
docker compose -f dab/docker-compose.yml config
```

## Generar token de sesión según Rol
```bash
curl -N "http://localhost:5000/mcp/sse" -H "X-MS-API-ROLE: analyst"

# Esto queda "colgado" esperando eventos — es correcto. En la respuesta inicial verás algo como:
# event: endpoint
# data: /mcp/message?sessionId=abc123-def456
```

## REST con rol analyst — debe devolver filas de orders
```bash
curl "http://localhost:5000/api/Orders" -H "X-MS-API-ROLE: analyst"
```

## MCP — debe devolver las entidades disponibles
```bash
curl -X POST "http://localhost:5000/mcp/message?sessionId=<SESSION_ID>" -H "Content-Type: application/json" -H "X-MS-API-ROLE: analyst" -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}"
```