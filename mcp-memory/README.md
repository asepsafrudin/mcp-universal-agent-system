# MCP Server

Ini adalah server MCP universal yang menyediakan tool execution environment untuk berbagai agen.

## Fitur

-   **Web-based API**: Server menggunakan FastAPI untuk menyediakan JSON-RPC API melalui HTTP.
-   **Extensible Tools**: Mudah untuk menambahkan tool baru dengan meletakkannya di direktori `tools`.
-   **Memory System**: Terintegrasi dengan PostgreSQL dan pgvector untuk long-term memory dengan hybrid search.
-   **Containerized**: Disediakan dengan Dockerfile untuk deployment yang mudah.

## Cara Menjalankan

### Menggunakan Docker

1.  **Build Docker image:**

    ```bash
    docker build -t mcp-server .
    ```

2.  **Run Docker container:**

    ```bash
    docker run -p 8000:8000 mcp-server
    ```

### Menjalankan Secara Lokal

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run server:**

    ```bash
    python mcp_server.py
    ```

## API

Server menyediakan endpoint tunggal di `/` yang menerima request `POST` dengan body JSON-RPC.

### `tools/list`

Mendapatkan daftar tool yang tersedia.

**Request:**

```json
{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
}
```

### `tools/call`

Memanggil tool tertentu.

**Request:**

```json
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "read_file",
        "arguments": {
            "path": "README.md"
        }
    },
    "id": 2
}
```