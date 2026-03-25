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
HEALTH_CHECK_INTERVAL = 300  # 5 minutes (hemat resource)
MCP_HEALTH_URL = "http://localhost:8000/health"
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


def check_mcp_health() -> dict:
    """Check MCP server health via HTTP endpoint."""
    try:
        import urllib.request
        import urllib.error
        
        req = urllib.request.Request(
            MCP_HEALTH_URL,
            method='GET',
            headers={'Accept': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                'healthy': data.get('status') == 'healthy',
                'data': data
            }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }


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
            logger.info("Performing health check...")
            
            # Check HTTP health endpoint
            health = check_mcp_health()
            
            if health['healthy']:
                logger.info(f"✓ Health check PASSED - Tools: {health['data'].get('tools_available', 'N/A')}")
                consecutive_failures = 0
            else:
                logger.warning(f"✗ Health check FAILED - {health.get('error', 'Unknown error')}")
                consecutive_failures += 1
                
                # Check service status
                status = get_service_status()
                logger.info(f"Service status: {status['status']}")
                
                # If multiple failures, attempt restart
                if consecutive_failures >= 2:
                    logger.error(f"Multiple failures detected ({consecutive_failures})")
                    if restart_mcp_service():
                        consecutive_failures = 0
                    else:
                        logger.critical("CRITICAL: MCP service restart failed!")
            
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
