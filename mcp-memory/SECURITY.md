# Security Guide - MCP Server

Dokumentasi keamanan komprehensif untuk MCP Server, mencakup best practices, threat model, dan konfigurasi keamanan.

## 📋 Daftar Isi
- [Security Overview](#security-overview)
- [Threat Model](#threat-model)
- [Current Security Features](#current-security-features)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Production Security](#production-security)
- [Monitoring & Alerting](#monitoring--alerting)
- [Incident Response](#incident-response)
- [Security Updates](#security-updates)

## 🔒 Security Overview

### Design Philosophy
MCP Server dirancang dengan **"Security First"** approach dalam environment trusted. Server ini mengimplementasikan multiple layers of security untuk melindungi sistem dan data.

### Trust Model
- **Trusted Environment**: Server ini dirancang untuk berjalan dalam environment yang trusted
- **Local Communication**: Kommunikasi melalui STDIN/STDOUT (local process)
- **Limited Scope**: Fokus pada operasi file system dan shell commands yang aman
- **Container Isolation**: Menggunakan Docker untuk isolation tambahan

## 🎯 Threat Model

### Assets to Protect
1. **Host Filesystem**: Akses ke file dan direktori di host
2. **Container Runtime**: Integritas container dan runtime environment
3. **Data Integrity**: Konsistensi data yang diproses
4. **System Resources**: CPU, memory, dan disk space

### Potential Threats

#### High Risk
- **Arbitrary Code Execution**: Command injection melalui run_shell tool
- **File System Access**: Unauthorized file access atau modification
- **Privilege Escalation**: Attempt untuk mendapatkan privileges lebih tinggi
- **Resource Exhaustion**: Denial of service melalui excessive resource usage

#### Medium Risk
- **Data Leakage**: Exposure of sensitive information
- **Path Traversal**: Access ke file di luar workspace yang diizinkan
- **Command Injection**: Malicious input dalam shell commands

#### Low Risk
- **Information Disclosure**: System information leakage
- **Denial of Service**: Temporary service disruption

### Attack Vectors

#### 1. Command Injection
```bash
# Malicious input yang bisa disalahgunakan
"ls; rm -rf /"
"cat /etc/passwd"
"find / -name '*.txt' -exec rm {} \;"
```

**Mitigation**: Command whitelist + input validation

#### 2. Path Traversal
```bash
# Attempt untuk akses file di luar workspace
"../../../etc/passwd"
"/workspace/../../../home/user/secret.txt"
```

**Mitigation**: Path normalization + workspace restrictions

#### 3. Resource Exhaustion
```bash
# Commands yang menggunakan resource berlebihan
"yes > /dev/null"
"fork bomb"
"dd if=/dev/zero of=/dev/null"
```

**Mitigation**: Timeout limits + resource monitoring

## 🛡️ Current Security Features

### 1. Command Whitelist
**Implementation**: Hanya command yang explicitly diizinkan yang dapat dijalankan

```python
ALLOWED_COMMANDS = {
    "ls", "pwd", "whoami", "date", 
    "df", "free", "git", "cat", "find"
}
```

**Coverage**:
- ✅ System information: `pwd`, `whoami`, `date`
- ✅ File operations: `ls`, `cat`, `find`
- ✅ System monitoring: `df`, `free`
- ✅ Version control: `git`
- ❌ File modification: `rm`, `cp`, `mv` (blocked)
- ❌ Network operations: `curl`, `wget` (blocked)
- ❌ Process management: `kill`, `ps` (blocked)

### 2. Timeout Protection
**Implementation**: Maksimal 10 detik eksekusi per command

```python
result = subprocess.run(
    parts,
    capture_output=True,
    text=True,
    timeout=10,  # 10 second timeout
    cwd=cwd
)
```

**Benefits**:
- Prevents infinite loops
- Limits resource consumption
- Ensures responsive server

### 3. Path Mapping & Validation
**Implementation**: Controlled access melalui path mapping

```python
# Path mapping rules
if path.startswith("/workspace/"):
    real_path = "/app" + path[10:]
elif path.startswith("/host/"):
    real_path = "/home/aseps" + path[5:]
else:
    real_path = path  # Relative path
```

**Security Benefits**:
- Controlled access scope
- Prevention of path traversal
- Clear separation of concerns

### 4. Container Security
**Implementation**: Docker container dengan non-root user

```dockerfile
# Dockerfile security features
RUN useradd -m mcpuser
USER mcpuser
```

**Features**:
- Non-root execution
- Minimal attack surface
- Resource isolation

### 5. Input Validation
**Implementation**: JSON schema validation untuk semua inputs

```python
# Tool parameter validation
inputSchema = {
    "type": "object",
    "properties": {"path": {"type": "string"}},
    "required": ["path"]
}
```

## ⚙️ Configuration

### Environment Variables

#### Security-Related Variables
```bash
# Set custom timeout (in seconds)
export MCP_TIMEOUT=30

# Enable debug mode (not recommended for production)
export MCP_DEBUG=false

# Set allowed commands (comma-separated)
export MCP_ALLOWED_COMMANDS="ls,pwd,whoami,date,cat"

# Set workspace root
export MCP_WORKSPACE_ROOT=/app/workspace
```

#### Docker Security Configuration
```bash
# Run dengan security options
docker run -it --rm \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --read-only \
  --tmpfs /tmp \
  -v $(pwd):/workspace:ro \
  -v /etc/passwd:/etc/passwd:ro \
  mcp-mvp:slim
```

### Command Whitelist Customization

#### Adding New Commands
```python
# tools/run_shell.py - Modify ALLOWED_COMMANDS
ALLOWED_COMMANDS = {
    "ls", "pwd", "whoami", "date", 
    "df", "free", "git", "cat", "find",
    "grep", "sort", "uniq"  # Additional safe commands
}
```

#### Removing Commands
```python
# Remove potentially dangerous commands
ALLOWED_COMMANDS = {
    "ls", "pwd", "whoami", "date", 
    "df", "free",  # Removed git, cat, find
    "echo", "head", "tail"  # Safer alternatives
}
```

### Path Restrictions

#### Workspace-Only Mode
```python
# Modify path mapping untuk restrict ke workspace saja
def _map_path(path):
    if not path.startswith("/workspace/"):
        raise ValueError("Only workspace paths allowed")
    return "/app" + path[10:]
```

#### Read-Only Mode
```python
# Disable write operations
def write_file(args):
    return {
        "success": False, 
        "error": "Write operations disabled"
    }
```

## 📋 Best Practices

### Development Environment

#### 1. Use Docker untuk Development
```bash
# Selalu gunakan Docker untuk development
docker run -it --rm \
  -v $(pwd):/workspace \
  -v $HOME:/host \
  --name mcp-dev \
  mcp-mvp:slim
```

#### 2. Regular Security Updates
```bash
# Update base image secara regular
docker pull python:3.11-slim
docker build -t mcp-mvp:slim .
docker rmi $(docker images -q --filter "dangling=true")
```

#### 3. Code Review Process
- Review semua perubahan pada command whitelist
- Validate input sanitization
- Check for potential injection points

### Production Environment

#### 1. Container Hardening
```bash
# Multi-layer security configuration
docker run -it --rm \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp:noexec,nosuid,size=100m \
  --memory=512m \
  --cpus=1.0 \
  --pids-limit=100 \
  -v $(pwd):/workspace:ro \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  mcp-mvp:slim
```

#### 2. Network Isolation
```bash
# Create isolated network
docker network create --internal mcp-isolated

# Run dalam isolated network
docker run -it --rm \
  --network mcp-isolated \
  --name mcp-server \
  mcp-mvp:slim
```

#### 3. Resource Limits
```yaml
# docker-compose.prod.yml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
          pids: 100
        reservations:
          memory: 256M
          cpus: '0.5'
```

#### 4. Logging & Monitoring
```yaml
# Enable comprehensive logging
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service=mcp-server,environment=production"
```

### Client-Side Security

#### Input Sanitization
```python
# Always sanitize inputs
import shlex

def sanitize_command(command):
    # Remove potentially dangerous characters
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>']
    for char in dangerous_chars:
        command = command.replace(char, '')
    
    # Validate command structure
    parts = shlex.split(command)
    if not parts or parts[0] not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {parts[0]}")
    
    return command
```

#### Request Validation
```python
# Validate JSON-RPC requests
def validate_request(request):
    required_fields = ['jsonrpc', 'method', 'id']
    for field in required_fields:
        if field not in request:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate method
    if request['method'] not in ['tools/list', 'tools/call']:
        raise ValueError(f"Invalid method: {request['method']}")
```

## 🚀 Production Security

### Security Checklist

#### Pre-Deployment
- [ ] Command whitelist reviewed dan minimized
- [ ] Container running as non-root user
- [ ] Resource limits configured
- [ ] Network isolation enabled
- [ ] Logging enabled
- [ ] Security scanning completed
- [ ] Backup strategy implemented
- [ ] Monitoring configured

#### Runtime Security
- [ ] Regular security updates
- [ ] Log monitoring
- [ ] Resource usage monitoring
- [ ] Error rate monitoring
- [ ] Performance monitoring

#### Post-Deployment
- [ ] Security testing
- [ ] Penetration testing
- [ ] Compliance verification
- [ ] Documentation update

### Hardened Configuration

#### Production Dockerfile
```dockerfile
# Multi-stage build untuk security
FROM python:3.11-slim as builder

# Security: Install only necessary packages
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Security: Create non-root user dengan specific UID/GID
RUN groupadd -r mcpuser -g 1000 \
    && useradd -r -g mcpuser -u 1000 -d /app -s /bin/bash -c "MCP User" mcpuser

# Security: Set ownership dan permissions
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# Security: Copy application dengan proper ownership
COPY --chown=mcpuser:mcpuser . .

# Security: Set permissions
RUN chmod 755 /app \
    && chmod 644 /app/*.py \
    && find /app -type d -exec chmod 755 {} \;

# Security: Switch to non-root user
USER mcpuser

# Security: Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import json, sys; sys.exit(0)" || exit 1

CMD ["python3", "mcp_server.py"]
```

#### Production Security Script
```bash
#!/bin/bash
# secure-run.sh - Secure production runner

set -euo pipefail

# Configuration
IMAGE_NAME="mcp-mvp:slim"
CONTAINER_NAME="mcp-server-prod"
WORKSPACE_DIR="$(pwd)"
HOST_HOME="$HOME"
MEMORY_LIMIT="512m"
CPU_LIMIT="1.0"
PID_LIMIT="100"

# Security checks
if [[ $EUID -eq 0 ]]; then
   echo "❌ Do not run as root" >&2
   exit 1
fi

# Validate workspace directory
if [[ ! -d "$WORKSPACE_DIR" ]]; then
    echo "❌ Workspace directory not found: $WORKSPACE_DIR" >&2
    exit 1
fi

# Run dengan security options
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    \
    # Security options
    --security-opt no-new-privileges:true \
    --cap-drop ALL \
    --read-only \
    --tmpfs /tmp:noexec,nosuid,size=100m \
    \
    # Resource limits
    --memory="$MEMORY_LIMIT" \
    --cpus="$CPU_LIMIT" \
    --pids-limit="$PID_LIMIT" \
    \
    # Network isolation
    --network none \
    \
    # Volumes
    -v "$WORKSPACE_DIR:/workspace:ro" \
    -v "$HOST_HOME:/host" \
    -v /etc/passwd:/etc/passwd:ro \
    -v /etc/group:/etc/group:ro \
    \
    # Logging
    --log-driver json-file \
    --log-opt max-size=10m \
    --log-opt max-file=3 \
    \
    "$IMAGE_NAME" \
    tail -f /dev/null

echo "✅ MCP Server started securely"
echo "📊 Container: $CONTAINER_NAME"
echo "🔒 Security: Non-root, Isolated, Resource-limited"
```

## 📊 Monitoring & Alerting

### Security Monitoring

#### Log Analysis
```bash
# Monitor untuk suspicious activities
docker logs mcp-server 2>&1 | grep -E "(error|Error|ERROR)" | tail -20

# Monitor command usage
docker logs mcp-server 2>&1 | grep -E "(command|Command)" | tail -20

# Monitor file access patterns
docker logs mcp-server 2>&1 | grep -E "(file|File)" | tail -20
```

#### Resource Monitoring
```bash
# CPU usage
docker stats mcp-server --no-stream

# Memory usage
docker exec mcp-server free -h

# Disk usage
docker exec mcp-server df -h

# Process monitoring
docker exec mcp-server ps aux
```

#### Network Monitoring
```bash
# Monitor network connections (jika network enabled)
docker exec mcp-server netstat -tuln

# Monitor file descriptor usage
docker exec mcp-server lsof
```

### Alerting Rules

#### Security Alerts
```bash
# Alert: High error rate
if [[ $(docker logs mcp-server 2>&1 | grep -c "error\|Error") -gt 10 ]]; then
    echo "🚨 High error rate detected"
fi

# Alert: Command timeout
if [[ $(docker logs mcp-server 2>&1 | grep -c "Timeout") -gt 5 ]]; then
    echo "🚨 Multiple timeouts detected"
fi

# Alert: Resource exhaustion
if [[ $(docker stats mcp-server --no-stream | awk 'NR==2 {print $3}' | sed 's/MiB//') -gt 480 ]]; then
    echo "🚨 High memory usage detected"
fi
```

### Performance Metrics

#### Key Metrics to Track
1. **Response Time**: Average tool execution time
2. **Error Rate**: Percentage of failed requests
3. **Resource Usage**: CPU, memory, disk I/O
4. **Command Frequency**: Most used commands
5. **File Access Patterns**: Most accessed files/directories

#### Monitoring Script
```bash
#!/bin/bash
# monitor-security.sh

CONTAINER_NAME="mcp-server"
LOG_FILE="/var/log/mcp-security.log"

# Function to log security events
log_security_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Monitor for suspicious patterns
monitor_suspicious_activity() {
    # Check for command injection attempts
    if docker logs "$CONTAINER_NAME" 2>&1 | grep -q "not diizinkan\|not allowed"; then
        log_security_event "BLOCKED: Command injection attempt detected"
    fi
    
    # Check for path traversal attempts
    if docker logs "$CONTAINER_NAME" 2>&1 | grep -q "No such file\|Permission denied"; then
        log_security_event "WARNING: Potential path traversal attempt"
    fi
    
    # Check for resource exhaustion
    CPU_USAGE=$(docker stats "$CONTAINER_NAME" --no-stream --format "{{.CPUPerc}}" | sed 's/%//')
    if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
        log_security_event "WARNING: High CPU usage: ${CPU_USAGE}%"
    fi
}

# Run monitoring
monitor_suspicious_activity
```

## 🚨 Incident Response
