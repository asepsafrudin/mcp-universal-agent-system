export const tools = [
  {
    name: "query_db",
    description: "Execute SQL SELECT query on Postgres DB. Use params for safety. Returns JSON rows.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "SQL SELECT query e.g. 'SELECT * FROM table WHERE id = $1'"
        },
        params: {
          type: "array",
          description: "Params array matching $1, $2 etc."
        }
      },
      required: ["query"]
    }
  },
  {
    name: "list_tables",
    description: "List all tables in public schema.",
    inputSchema: {
      type: "object",
      properties: {}
    }
  },
  {
    name: "describe_table",
    description: "Get table schema (columns, types, nullable).",
    inputSchema: {
      type: "object",
      properties: {
        table: {
          type: "string",
          description: "Table name"
        }
      },
      required: ["table"]
    }
  },
  {
    name: "count_rows",
    description: "Count rows in table.",
    inputSchema: {
      type: "object",
      properties: {
        table: {
          type: "string",
          description: "Table name"
        }
      },
      required: ["table"]
    }
  }
];

export type ToolName = (typeof tools)[number]["name"];
