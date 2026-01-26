import os
from typing import Dict, Any

def read_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """Baca file dengan dukungan path:
    - /host/... → /home/aseps/...
    - /workspace/... → /app/...
    """
    try:
        path = os.path.normpath(args["path"])
        
        # Mapping path
        if path.startswith("/host/"):
            real_path = "/home/aseps" + path[5:]
        elif path.startswith("/workspace/"):
            real_path = "/app" + path[10:]
        else:
            real_path = path

        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "content": content, "path": real_path}
    except Exception as e:
        return {"success": False, "error": str(e), "path": args.get("path", "")}
