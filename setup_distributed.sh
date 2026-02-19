#!/bin/bash

echo "🌍 Setting up Distributed MCP Environment..."

# 1. Install Python Dependencies
echo "📦 Installing Python libraries..."
# Check for venv usage
PIP_CMD="pip"
if [ -d "/home/aseps/MCP/.venv" ]; then
    PIP_CMD="/home/aseps/MCP/.venv/bin/pip"
fi

$PIP_CMD install aio-pika grpcio grpcio-tools

# 2. Start RabbitMQ (Message Broker)
echo "🐰 Starting RabbitMQ Container..."
if docker ps | grep -q mcp-rabbitmq; then
    echo "   RabbitMQ already running."
else
    # Simple auth for LAN usage, change for public internet!
    docker run -d \
      --name mcp-rabbitmq \
      -p 5672:5672 \
      -p 15672:15672 \
      -e RABBITMQ_DEFAULT_USER=mcp \
      -e RABBITMQ_DEFAULT_PASS=mcp_secure_pass \
      rabbitmq:3-management
      
    echo "   RabbitMQ deployed. Dashboard at http://localhost:15672 (mcp/mcp_secure_pass)"
fi

# 3. Verify Connectivity logic would go here
echo "✅ Setup Complete! You can now use 'publish_remote_task'."
