# Installation Guide - MCP Server

Panduan lengkap untuk instalasi dan setup MCP Server dalam berbagai environment.

## 📋 Daftar Isi
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation Methods](#installation-methods)
- [Docker Setup](#docker-setup)
- [Development Setup](#development-setup)
- [Production Setup](#production-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements
- **Operating System**: Linux (recommended), macOS, atau Windows (dengan WSL2)
- **Python**: 3.8+ (jika menjalankan tanpa Docker)
- **Docker**: 20.10+ (untuk containerized setup)
- **RAM**: Minimum 512MB, Recommended 1GB+
- **Disk Space**: Minimum 100MB untuk image Docker

### Required Tools
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check Docker version
docker --version   # Should be 20.10+

# Check Docker daemon
sudo systemctl status docker
```

### Platform-Specific Setup

#### Linux (Ubuntu/Debian)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Python3 dan pip
sudo apt update
sudo apt install python3 python3-pip -y
```

#### macOS
```bash
# Install Docker Desktop
# Download dari https://www.docker.com/products/docker-desktop

# Install Python (jika belum ada)
brew install python3
```

#### Windows (WSL2)
```bash
# Install Docker Desktop for Windows
# Enable WSL2 backend

# Install Ubuntu di WSL2
wsl --install -d Ubuntu-20.04

# Install Docker dalam WSL2
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

## ⚡ Quick Start

### 1. Download/Clone Project
```bash
# Jika menggunakan git
git clone <repository-url>
cd mcp-server

# Atau download dan extract
wget <download-url>
tar -xzf mcp-server.tar.gz
cd mcp-server
```

### 2. Build dan Run dengan Docker
```bash
# Build image
./docker-build.sh

# Run container
./docker-run.sh
```

### 3. Test Server
```bash
# Test connection (dalam container atau local)
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python3 mcp_server.py
```

## 🐳 Installation Methods

### Method 1: Docker (Recommended)

#### Basic Docker Setup
```bash
# Build image
docker build -t mcp-mvp:slim .

# Run container
docker run -it --rm mcp-mvp:slim
```

#### Advanced Docker Setup
```bash
# Run dengan volume mounts
docker run -it --rm \
  -v $(pwd):/workspace \
  -v $HOME:/host \
  --name mcp-server \
  mcp-mvp:slim

# Run dengan port mapping (jika diperlukan)
docker run -it --rm \
  -v $(pwd):/workspace \
  -v $HOME:/host \
  -p 8080:8080 \
  mcp-mvp:slim

# Run di background
docker run -d \
  --name mcp-server \
  -v $(pwd):/workspace \
  -v $HOME:/host \
  mcp-mvp:slim tail -f /dev/null
```

#### Docker Compose Setup
Buat file `docker-compose.yml`:
```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    container_name: mcp-server
    volumes:
      - ./workspace:/workspace
      - /home/aseps:/host
      - mcp-data:/data
    environment:
      - MCP_DEBUG=false
      - MCP_TIMEOUT=10
    restart: unless-stopped
    stdin_open: true
    tty: true

volumes:
  mcp-data:
```

Jalankan dengan:
```bash
docker-compose up -d
docker-compose logs -f mcp-server
```

### Method 2: Native Python

#### Setup Virtual Environment
```bash
# Buat virtual environment
python3 -m venv mcp-env

# Activate virtual environment
# Linux/macOS:
source mcp-env/bin/activate

# Windows:
mcp-env\Scripts\activate

# Install dependencies (jika ada)
pip install -r requirements.txt
```

#### Run Server
```bash
# Jalankan server
python3 mcp_server.py

# Test server
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python3 mcp_server.py
```

## 🐳 Docker Setup

### Building Custom Image

#### Basic Dockerfile Customization
```dockerfile
# Dockerfile.custom
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install additional packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY tools/ ./tools/
COPY mcp_server.py .

# Create non-root user
RUN useradd -m mcpuser && \
    chown -R mcpuser:mcpuser /app
USER mcpuser

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_DEBUG=false

# Expose port (jika diperlukan)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

CMD ["python3", "mcp_server.py"]
```

#### Build dan Run Custom Image
```bash
# Build custom image
docker build -f Dockerfile.custom -t mcp-custom:latest .

# Run custom image
docker run -it --rm \
  -v $(pwd):/workspace \
  -v $HOME:/host \
  mcp-custom:latest
```

### Docker Networking

#### Network Setup
```bash
# Buat custom network
docker network create mcp-network

# Run container dalam network
docker run -it --rm \
  --network mcp-network \
  --name mcp-server \
  mcp-mvp:slim

# Run client dalam same network
docker run -it --rm \
  --network mcp-network \
  --name mcp-client \
  ubuntu:latest bash
```

#### Port Forwarding
```bash
# Forward STDIN/STDOUT through port
docker run -it --rm \
  -p 3000:3000 \
  mcp-mvp:slim socat TCP-LISTEN:3000,fork EXEC:"python3 mcp_server.py"
```

### Docker Volumes

#### Volume Management
```bash
# Buat named volume
docker volume create mcp-data

# Run dengan volume
docker run -it --rm \
  -v mcp-data:/data \
  -v $(pwd):/workspace \
  mcp-mvp:slim

# Inspect volume
docker volume inspect mcp-data

# Backup volume
docker run --rm -v mcp-data:/data -v $(pwd):/backup alpine tar czf /backup/mcp-data-backup.tar.gz -C /data .
```

#### Volume Permissions
```bash
# Run dengan specific user
docker run -it --rm \
  -u $(id -u):$(id -g) \
  -v $(pwd):/workspace \
  mcp-mvp:slim
```

## 💻 Development Setup

### Local Development Environment

#### 1. Clone Repository
```bash
git clone <repository-url>
cd mcp-server
```

#### 2. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install development dependencies
pip install -r requirements-dev.txt
```

#### 3. Development Scripts
Buat `scripts/dev-setup.sh`:
```bash
#!/bin/bash
set -e

echo "🚀 Setting up MCP Server development environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy

# Setup pre-commit hooks
pip install pre-commit
pre-commit install

echo "✅ Development environment ready!"
echo "📝 To activate: source venv/bin/activate"
```

#### 4. Testing Setup
```bash
# Run tests
python -m pytest tests/

# Run dengan coverage
python -m pytest --cov=. tests/

# Run specific test
python -m pytest tests/test_file_writer.py
```

### IDE Configuration

#### VS Code Setup
Buat `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    }
}
```

#### PyCharm Setup
1. Open project di PyCharm
2. Configure Python interpreter: `./venv/bin/python`
3. Install dependencies dari `requirements.txt`
4. Configure run configuration untuk `mcp_server.py`

### Debugging Setup

#### Python Debugging
```python
# Tambahkan di mcp_server.py untuk debugging
import pdb; pdb.set_trace()  # Breakpoint

# Atau gunakan logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Docker Debugging
```bash
# Run container dengan debugging
docker run -it --rm \
  -v $(pwd):/workspace \
  -p 5678:5678 \
  mcp-mvp:slim \
  python3 -m pdb mcp_server.py
```

## 🚀 Production Setup

### Production Docker Setup

#### Production Dockerfile
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN useradd -m -u 1000 mcpuser
WORKDIR /app

# Copy application
COPY --chown=mcpuser:mcpuser . .

USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import json, sys; sys.exit(0)" || exit 1

CMD ["python3", "mcp_server.py"]
```

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: mcp-server-prod
    restart: unless-stopped
    
    volumes:
      - workspace_data:/workspace
      - host_data:/host
      - ./logs:/app/logs
    
    environment:
      - MCP_ENV=production
      - MCP_DEBUG=false
      - MCP_TIMEOUT=30
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    
    security_opt:
      - no-new-privileges:true
    
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m

volumes:
  workspace_data:
  host_data:
```

#### Deploy Production
```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Monitor
docker-compose -f docker-compose.prod.yml logs -f
```

### Security Considerations

#### Container Security
```bash
# Run dengan security options
docker run -it --rm \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp \
  -v $(pwd):/workspace:ro \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  mcp-mvp:slim
```

#### Network Security
```bash
# Create isolated network
docker network create --internal mcp-isolated

# Run dalam isolated network
docker run -it --rm \
  --network mcp-isolated \
  --name mcp-server \
  mcp-mvp:slim
```

### Monitoring Setup

#### Health Checks
```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Manual health check
docker exec mcp-server python3 -c "import json, sys; print(json.dumps({'status': 'healthy'}))"
```

#### Logging
```bash
# View logs
docker logs -f mcp-server

# Logs dengan timestamps
docker logs -f -t mcp-server

# Export logs
docker logs mcp-server > mcp-server.log 2>&1
```

#### Metrics Collection
```bash
# Install monitoring tools
docker exec mcp-server apt-get update
docker exec mcp-server apt-get install -y htop iotop

# Monitor resources
docker stats mcp-server
```

## ✅ Verification

### Basic Functionality Tests

#### 1. Test Server Start
```bash
# Test server dapat dijalankan
timeout 5s python3 mcp_server.py
echo $?  # Should be 0 (success) or 124 (timeout)
```

#### 2. Test JSON-RPC Communication
```bash
# Test tools/list
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python3 mcp_server.py

# Test write_file
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "write_file", "arguments": {"path": "/workspace/test.txt", "content": "Hello World"}}, "id": 2}' | python3 mcp_server.py

# Test read_file
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "read_file", "arguments": {"path": "/workspace/test.txt"}}, "id": 3}' | python3 mcp_server.py
```

#### 3. Test Docker Setup
```bash
# Test Docker build
docker build -t mcp-mvp:slim . && echo "✅ Build successful"

# Test Docker run
docker run --rm mcp-mvp:slim timeout 5s python3 -c "print('Docker test successful')" && echo "✅ Docker run successful"
```

### Integration Tests

#### Python Client Test
```python
# test_integration.py
import json
import subprocess
import sys
import time

def test_mcp_server():
    """Test MCP server functionality."""
    # Start server process
    process = subprocess.Popen(
        ['python3', 'mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test tools/list
        request = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        response_data = json.loads(response.strip())
        
        assert response_data['result']['tools'], "No tools returned"
        print("✅ tools/list test passed")
        
        # Test write_file
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "write_file",
                "arguments": {
                    "path": "/workspace/test.txt",
                    "content": "Integration test"
                }
            },
            "id": 2
        }
        
        process.stdin.write(json.dumps(request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        response_data = json.loads(response.strip())
        
        assert response_data['result'], "Write failed"
        print("✅ write_file test passed")
        
        print("✅ All integration tests passed")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_mcp_server()
```

#### Docker Integration Test
```bash
#!/bin/bash
# test_docker_integration.sh

set -e

echo "🐳 Testing Docker integration..."

# Build image
docker build -t mcp-test:latest . || exit 1
echo "✅ Docker build successful"

# Test container startup
docker run --rm mcp-test:latest timeout 5s python3 -c "import sys; print('Container startup successful')" || exit
