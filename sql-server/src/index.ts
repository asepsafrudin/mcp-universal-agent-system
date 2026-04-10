#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  McpError,
  ErrorCode,
} from "@modelcontextprotocol/sdk/types.js";
import { tools } from "./tools.js";
import * as db from "./db.js";

const server = new Server(
  {
    name: "sql-mcp-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "query_db": {
        const { query, params = [] } = args as any;
        if (typeof query !== 'string') {
          throw new Error('Query must be string');
        }
        const result = await db.query(query, params);
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              success: true,
              rows: result.rows,
              rowCount: result.rowCount,
              fields: result.fields?.map((f: any) => f.name),
            }, null, 2),
          }],
        };
      }

      case "list_tables": {
        const tables = await db.listTables();
        return {
          content: [{
            type: "text",
            text: JSON.stringify(tables, null, 2),
          }],
        };
      }

      case "describe_table": {
        const { table } = args as any;
        if (typeof table !== 'string') {
          throw new Error('Table name must be string');
        }
        const schema = await db.describeTable(table);
        return {
          content: [{
            type: "text",
            text: JSON.stringify(schema, null, 2),
          }],
        };
      }

      case "count_rows": {
        const { table } = args as any;
        if (typeof table !== 'string') {
          throw new Error('Table name must be string');
        }
        const result = await db.query('SELECT COUNT(*) as count FROM $1', [table]);
        return {
          content: [{
            type: "text",
            text: `Row count in \`${table}\`: ${result.rows[0].count}`,
          }],
        };
      }

      default:
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${name}`
        );
    }
  } catch (error) {
    console.error('Tool error:', error);
    throw new McpError(
      ErrorCode.InternalError,
      error instanceof Error ? error.message : 'Internal server error'
    );
  }
});

async function main() {
  // Test DB connection
  try {
    await db.query('SELECT 1 as ping');
    console.error('DB connected successfully');
  } catch (error) {
    console.error('DB connection failed:', error);
    // Don't throw, let server start but tools will fail
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('SQL MCP server running on stdio');
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
