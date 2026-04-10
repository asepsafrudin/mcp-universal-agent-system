# SQL MCP Server

**sql-mcp-server** - Model Context Protocol server untuk Postgres SQL operations.

## Features

### Tools
| Tool | Deskripsi | Example |
|------|-----------|---------|
| `query_db` | Execute SQL SELECT query (params supported) | `{query: 'SELECT * FROM documents LIMIT $1', params: [5]}` |
| `list_tables` | List tables in public schema | `{}` |
| `describe_table` | Table schema (columns, types) | `{table: 'documents'}` |
| `count_rows` | Count rows in table | `{table: 'documents'}` |

Returns JSON rows atau text summary.

## Setup

1. Env vars (wajib untuk MCP config):
   ```
   PG_HOST=localhost
   PG_PORT=5432
   PG_DB=rag_knowledge  # atau DB kamu
   PG_USER=postgres
   PG_PASS=your_password
   ```

2. Build:
   ```
   npm run build
   ```

## MCP Config

Tambah ke `blackbox_mcp_settings.json`:

```json
{
  \"mcpServers\": {
    \"sql-mcp-server\": {
      \"command\": \"node\",
      \"args\": [\"/home/aseps/MCP/sql-server/build/index.js\"],
      \"env\": {
        \"PG_HOST\": \"localhost\",
        \"PG_PORT\": \"5432\",
        \"PG_DB\": \"rag_knowledge\",
        \"PG_USER\": \"postgres\",
        \"PG_PASS\": \"your_pass\"
      }
    }
  }
}
```

## Testing

1. Build success.
2. Restart VSCode/Claude agar MCP server load.
3. Use tool: `use_mcp_tool server_name=\"sql-mcp-server\" tool_name=\"list_tables\"`

## Development

```
npm run watch  # auto rebuild
npm run inspector  # debug
```

## Security

- Prepared statements for params.
- No INSERT/UPDATE/DELETE (SELECT only for safety).
- Connection pool dengan timeout.
- Error logging.

DB connection test on start: console.error if fail.
