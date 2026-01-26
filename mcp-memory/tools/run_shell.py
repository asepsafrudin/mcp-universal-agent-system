import subprocess
import shlex
import os
from typing import Dict, Any

ALLOWED_COMMANDS = {"ls", "pwd", "whoami", "date", "df", "free", "git", "cat", "find"}

def _translate_path_in_command(cmd: str) -> str:
    """Ganti /workspace/ → /app/ di command shell"""
    return cmd.replace("/workspace/", "/app/")

def run_shell(args: Dict[str, Any]) -> Dict[str, Any]:
    """Jalankan command aman — otomatis sesuaikan working directory."""
    try:
        cmd = args["command"]
        cmd = _translate_path_in_command(cmd)
        parts = shlex.split(cmd)
        
        if not parts or parts[0] not in ALLOWED_COMMANDS:
            return {"success": False, "error": f"Command '{parts[0]}' tidak diizinkan."}
        
        # Tentukan working directory:
        # - Di container: /app (jika ada)
        # - Di host: folder saat ini
        cwd = "/app" if os.path.exists("/app") else os.getcwd()
        
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd
        )
        
        return {
            "success": True,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout (>10 detik)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
