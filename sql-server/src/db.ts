#!/usr/bin/env node
import { Pool, PoolClient, QueryResult } from 'pg';

const pool = new Pool({
  host: process.env.PG_HOST || 'localhost',
  port: parseInt(process.env.PG_PORT || '5432'),
  database: process.env.PG_DB || 'rag_knowledge',
  user: process.env.PG_USER || '',
  password: process.env.PG_PASS || '',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on('error', (err: Error) => {
  console.error('Unexpected Postgres pool error:', err.stack);
});

export async function query(text: string, params?: any[]): Promise<QueryResult<any>> {
  const client: PoolClient = await pool.connect();
  try {
    const result = await client.query(text, params);
    return result;
  } finally {
    client.release();
  }
}

export async function getPool() {
  return pool;
}

export async function listTables(): Promise<string[]> {
  const res = await query(`
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
  `);
  return res.rows.map((row: any) => row.table_name);
}

export async function describeTable(tableName: string): Promise<any> {
  const res = await query(`
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name = $1
  `, [tableName]);
  return res.rows;
}
