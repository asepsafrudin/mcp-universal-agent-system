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

# [SECURITY] Check for credentials in environment
if [ -z "$RABBITMQ_DEFAULT_USER" ] || [ -z "$RABBITMQ_DEFAULT_PASS" ]; then
  echo "❌ Error: RABBITMQ_DEFAULT_USER and RABBITMQ_DEFAULT_PASS environment variables must be set."
  echo "Please define them in your environment or source a .env file."
  exit 1
fi

# 2. Start RabbitMQ (Message Broker)
echo "🐰 Starting RabbitMQ Container..."
if docker ps | grep -q mcp-rabbitmq; then
    echo "   RabbitMQ already running."
else
    # Credentials are passed from environment variables
    docker run -d \
      --name mcp-rabbitmq \
      -p 5672:5672 \
      -p 15672:15672 \
      -e RABBITMQ_DEFAULT_USER="$RABBITMQ_DEFAULT_USER" \
      -e RABBITMQ_DEFAULT_PASS="$RABBITMQ_DEFAULT_PASS" \
      rabbitmq:3-management
      
    echo "   RabbitMQ deployed. Dashboard at http://localhost:15672"
    echo "   Login with the user '$RABBITMQ_DEFAULT_USER' and the password from your environment."
fi

# 3. Verify Connectivity logic would go here
echo "✅ Setup Complete! You can now use 'publish_remote_task'."
