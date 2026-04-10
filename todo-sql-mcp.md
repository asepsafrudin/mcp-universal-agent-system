# SQL MCP Server INTEGRATED to mcp-unified ✅

## Integration Complete

**services/sql/sql_tools.py**
- query_db(query, params=[], namespace="default")
- list_tables(namespace="default")
- describe_table(table)
- count_rows(table)

**Using internal Postgres pool (mcp DB)**

**Bootstrap**: Added to core/bootstrap.py

**Next**: Restart mcp-unified process (pgrep -f mcp_server.py ; pkill -f mcp_server.py)

**Test**:
```
use_mcp_tool server_name="mcp-unified" tool_name="list_tables" arguments="{}"
```

Node sql-server optional now (remove config if want).

Ready!
