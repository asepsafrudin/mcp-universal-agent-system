import os
from typing import Dict, Any

def list_dir(args: Dict[str, Any]) -> Dict[str, Any]:
    """List direktori dengan dukungan path khusus."""
    try:
        path = os.path.normpath(args.get("path", "."))
        
        # Mapping path
        if path.startswith("/host/"):
            real_path = "/home/aseps" + path[5:]
        elif path.startswith("/workspace/"):
            real_path = "/app" + path[10:]
        else:
            real_path = path

        items = os.listdir(real_path)
        dirs = [i for i in items if os.path.isdir(os.path.join(real_path, i))]
        files = [i for i in items if os.path.isfile(os.path.join(real_path, i))]
        
        return {
            "success": True,
            "path": real_path,
            "directories": dirs,
            "files": files
        }
    except Exception as e:
        return {"success": False, "error": str(e), "path": args.get("path", "")}
