# Dockerfile minimalis (tanpa mcp-server library)
FROM python:3.12-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Buat user non-root
RUN useradd -m mcpuser
WORKDIR /app

# Copy hanya file yang diperlukan
COPY tools/ ./tools/
COPY mcp_server.py .

# Izin & user
RUN chown -R mcpuser:mcpuser ./tools ./mcp_server.py
USER mcpuser

EXPOSE 8000

# Jalankan langsung (tanpa venv)
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]
