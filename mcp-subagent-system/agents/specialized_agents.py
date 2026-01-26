import abc
import os
from typing import Any, Dict, List, Optional

class BaseAgent(abc.ABC):
    """Kelas dasar untuk semua sub-agent spesialis"""
    
    def __init__(self, name: str):
        self.name = name

    @abc.abstractmethod
    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Eksekusi operasi spesifik agen"""
        pass

class FileAgent(BaseAgent):
    """Agen untuk operasi file (read, write, list, delete)"""
    
    def __init__(self):
        super().__init__("FileAgent")

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        from shared.mcp_client import call_mcp_tool
        
        # Mapping operasi ke tools mcp-memory/shared
        tool_map = {
            "read": "read_file",
            "write": "write_file",
            "list": "list_dir",
            "delete": "run_shell" # delete via rm
        }
        
        tool_name = tool_map.get(operation)
        if not tool_name:
            return {"status": "error", "message": f"Operasi {operation} tidak didukung oleh FileAgent"}
            
        # Panggil mcp_client (mengarah ke mcp-memory server)
        # Catatan: Kita asumsikan server mcp-memory berjalan di port 8000
        result = await call_mcp_tool(tool_name, params)
        return result

class CodeAgent(BaseAgent):
    """Agen untuk analisis dan manipulasi kode"""
    
    def __init__(self):
        super().__init__("CodeAgent")

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Implementasi logika analisis kode sederhana atau delegasi ke tool eksternal
        return {"status": "success", "message": f"CodeAgent mengeksekusi {operation}", "data": params}

class TerminalAgent(BaseAgent):
    """Agen untuk eksekusi perintah terminal (Mandiri)"""
    
    def __init__(self):
        super().__init__("TerminalAgent")

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess
        if operation == "execute":
            command = params.get("command")
            try:
                # Eksekusi langsung untuk keandalan roleplay
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
                return {
                    "status": "success" if result.returncode == 0 else "error",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            except Exception as e:
                return {"status": "error", "message": f"Subprocess error: {str(e)}"}
        return {"status": "error", "message": "Operasi terminal tidak dikenal"}

class SearchAgent(BaseAgent):
    """Agen untuk pencarian (memory & semantic search)"""
    
    def __init__(self):
        super().__init__("SearchAgent")

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        from shared.mcp_client import call_mcp_tool
        if operation == "search":
            return await call_mcp_tool("memory_search", params)
        return {"status": "error", "message": "Operasi search tidak dikenal"}

class ResearchAgent(BaseAgent):
    """Agen spesialis riset teknologi (TechRadar)"""
    
    def __init__(self):
        super().__init__("ResearchAgent")

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        from tools.tech_radar import TechRadarTool
        if operation == "tech_scan":
            query = params.get("query")
            limit = params.get("limit", 5)
            if not query:
                return {"status": "error", "message": "Query riset diperlukan"}
            
            radar = TechRadarTool()
            results = await radar.search(query, limit)
            return {
                "status": "success",
                "query": query,
                "findings": results,
                "summary": f"Ditemukan {len(results)} referensi teknologi untuk '{query}'"
            }
        return {"status": "error", "message": f"Operasi {operation} tidak didukung oleh ResearchAgent"}

class WindowsAgent(BaseAgent):
    """Agen spesialis manipulasi sistem host Windows via PowerShell (Secure Elevation)"""
    
    def __init__(self):
        super().__init__("WindowsAgent")
        self.secret_path = "/home/aseps/MCP/.env.secret"

    def _load_secrets(self) -> Dict[str, str]:
        """Load kredensial dari file secret dengan trimming"""
        secrets = {}
        if os.path.exists(self.secret_path):
            with open(self.secret_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        # Trim quotes and spaces
                        secrets[key.strip()] = val.strip().strip('"').strip("'")
        
        # Diagnostic logging (Safe: only show existence and length)
        user = secrets.get("WIN_ADMIN_USER")
        password = secrets.get("WIN_ADMIN_PASS")
        print(f"[*] Windows Secrets Loaded: User={user}, PassLength={len(password) if password else 0}")
        
        return secrets

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess
        import os
        
        if operation == "powershell":
            command = params.get("command")
            elevated = params.get("elevated", False)
            
            if not command:
                return {"status": "error", "message": "Perintah PowerShell diperlukan"}
            
            secrets = self._load_secrets()
            user = secrets.get("WIN_ADMIN_USER")
            password = secrets.get("WIN_ADMIN_PASS")

            if elevated and (not user or not password):
                return {
                    "status": "error", 
                    "message": "Elevasi diminta tapi kredensial (WIN_ADMIN_USER/PASS) tidak ditemukan di .env.secret"
                }

            if elevated:
                # Mode: Admin Command Generator
                # Memberikan instruksi manual karena batasan keamanan Windows untuk akun interaktif
                ps_admin_command = f'powershell.exe -Command "Start-Process powershell.exe -ArgumentList \\"-NoProfile\\", \\"-Command\\", \\"{command}\\" -Verb RunAs"'
                
                return {
                    "status": "MANUAL_ACTION_REQUIRED",
                    "reason": "Administrative privileges required (UAC Elevation)",
                    "instruction": "Salin dan jalankan perintah di bawah ini di Terminal/PowerShell Windows Anda:",
                    "command_to_run": command,
                    "wrapper_command": ps_admin_command,
                    "note": "Perintah ini akan membuka jendela UAC Windows untuk konfirmasi hak akses administrator."
                }
            else:
                # Mode: Full Autonomous (Non-Admin)
                full_command = ["powershell.exe", "-NoProfile", "-Command", command]
                try:
                    result = subprocess.run(full_command, capture_output=True, text=True, timeout=60)
                    return {
                        "status": "success" if result.returncode == 0 else "error",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    }
                except Exception as e:
                    return {"status": "error", "message": f"Windows Execution Error: {str(e)}"}
                
        return {"status": "error", "message": f"Operasi {operation} tidak didukung oleh WindowsAgent"}

class GitHubAgent(BaseAgent):
    """Agen spesialis manajemen repositori dan kolaborasi GitHub"""
    
    def __init__(self):
        super().__init__("GitHubAgent")
        self.secret_path = "/home/aseps/MCP/.env.secret"

    def _load_token(self) -> Optional[str]:
        """Load GITHUB_TOKEN dari file secret"""
        if os.path.exists(self.secret_path):
            with open(self.secret_path, "r") as f:
                for line in f:
                    if "GITHUB_TOKEN=" in line:
                        return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        return None

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess
        import os
        
        token = self._load_token()
        env = os.environ.copy()
        if token:
            env["GITHUB_TOKEN"] = token
            # Juga set untuk git credential helper jika dibutuhkan
            env["GH_TOKEN"] = token

        if operation == "git":
            command = params.get("command", "")
            # Avoid duplicating prefix
            cmd_body = command.replace("git ", "", 1) if command.startswith("git ") else command
            full_command = f"git {cmd_body}"
        elif operation == "gh":
            command = params.get("command", "")
            # Avoid duplicating prefix
            cmd_body = command.replace("gh ", "", 1) if command.startswith("gh ") else command
            full_command = f"gh {cmd_body}"
        else:
            return {"status": "error", "message": f"Operasi {operation} tidak dikenal"}

        try:
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True, env=env, timeout=60)
            return {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"status": "error", "message": f"GitHub Execution Error: {str(e)}"}
