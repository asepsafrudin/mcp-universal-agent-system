#!/usr/bin/env python3
"""
WSL Health Monitor untuk MCP Unified Hub
========================================

Script ini berjalan di dalam WSL dan melakukan health check ke MCP server.
Bisa dijalankan sebagai systemd service terpisah atau cron job.

Usage:
    # Manual run
    python3 /home/aseps/MCP/scripts/wsl-health-monitor.py
    
    # As systemd service
    sudo cp scripts/wsl-health-monitor.service /etc/systemd/system/
    sudo systemctl enable wsl-health-monitor
    sudo systemctl start wsl-health-monitor

Author: MCP Unified Setup
Version: 1.0
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================
# Configuration
# ============================================
HEALTH_CHECK_INTERVAL = 300  # 5 minutes
MCP_HEALTH_URL = "http://localhost:8000/health"
VANE_HEALTH_URL = "http://localhost:3001"  # Simple UI check
WAHA_HEALTH_URL = "http://localhost:3000"  # WAHA API check

MCP_SERVICE = "mcp-unified"
LOG_FILE = Path("/home/aseps/MCP/logs/wsl-health-monitor.log")
MAX_RETRIES = 3
RETRY_DELAY = 5

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ============================================
# Setup Logging
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("wsl-health-monitor")


# ============================================
# Helper Functions
# ============================================
def run_command(cmd: list[str], check: bool = False) -> tuple[int, str, str]:
    """Run shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_http_health(url: str, name: str) -> bool:
    """Check health of a service via simple GET request."""
    try:
        import urllib.request
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.getcode() < 400
    except Exception as e:
        logger.warning(f"Health check for {name} failed: {e}")
        return False


def restart_docker_service(name: str) -> bool:
    """Restart a docker container."""
    logger.warning(f"Attempting to start docker container: {name}")
    code, stdout, stderr = run_command(['docker', 'start', name])
    return code == 0


def restart_mcp_service() -> bool:
    """Restart MCP service using systemctl."""
    logger.warning("Attempting to restart MCP service...")
    
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Restart attempt {attempt}/{MAX_RETRIES}")
        
        # Stop service
        run_command(['sudo', 'systemctl', 'stop', MCP_SERVICE])
        time.sleep(2)
        
        # Start service
        code, stdout, stderr = run_command(
            ['sudo', 'systemctl', 'start', MCP_SERVICE]
        )
        
        if code == 0:
            # Wait for service to be ready
            time.sleep(5)
            
            # Verify
            code, stdout, stderr = run_command(
                ['systemctl', 'is-active', MCP_SERVICE]
            )
            
            if stdout.strip() == 'active':
                logger.info("✓ MCP service restarted successfully")
                return True
        
        logger.error(f"Restart attempt {attempt} failed: {stderr}")
        time.sleep(RETRY_DELAY)
    
    logger.error("✗ All restart attempts failed")
    return False


def get_service_status() -> dict:
    """Get detailed service status."""
    code, stdout, stderr = run_command(
        ['systemctl', 'status', MCP_SERVICE, '--no-pager']
    )
    
    return {
        'exit_code': code,
        'status': 'active' if code == 0 else 'inactive/error',
        'output': stdout if code == 0 else stderr
    }


# ============================================
# Main Monitor Loop
# ============================================
async def monitor_loop():
    """Main monitoring loop."""
    logger.info("=" * 60)
    logger.info("WSL Health Monitor Started")
    logger.info(f"Health check interval: {HEALTH_CHECK_INTERVAL} seconds")
    logger.info(f"MCP Service: {MCP_SERVICE}")
    logger.info(f"Health URL: {MCP_HEALTH_URL}")
    logger.info("=" * 60)
    
    consecutive_failures = 0
    
    while True:
        try:
            logger.info("Performing comprehensive health check...")
            
            # 1. Check MCP Hub (Port 8000)
            mcp_ok = check_http_health(MCP_HEALTH_URL, "MCP-Hub")
            if mcp_ok:
                logger.info("✓ MCP-Hub is UP")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    restart_mcp_service()
            
            # 2. Check Vane AI (Port 3001)
            vane_ok = check_http_health(VANE_HEALTH_URL, "Vane-AI")
            if not vane_ok:
                logger.warning("✗ Vane-AI is DOWN - attempting restart")
                restart_docker_service("vane")
            else:
                logger.info("✓ Vane-AI is UP")

            # 3. Check WAHA (Port 3000)
            waha_ok = check_http_health(WAHA_HEALTH_URL, "WAHA")
            if not waha_ok:
                logger.warning("✗ WAHA is DOWN - attempting restart")
                restart_docker_service("waha")
            else:
                logger.info("✓ WAHA is UP")
            
            logger.info(f"Next check in {HEALTH_CHECK_INTERVAL} seconds...")
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in monitor loop: {e}")
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)


def main():
    """Entry point."""
    try:
        asyncio.run(monitor_loop())
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
