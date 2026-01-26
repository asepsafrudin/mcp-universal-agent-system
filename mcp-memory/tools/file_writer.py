import os
from typing import Dict, Any

def write_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """Tulis file dengan dukungan path:
    - /host/...      → Volume mount ke /home/aseps (WSL home)
    - /workspace/... → Volume mount ke folder proyek MCP
    - lainnya        → di dalam container
    
    Catatan: Path langsung digunakan karena volume mount Docker
    sudah menangani mapping ke host filesystem.
    """
    try:
        path = args["path"]
        content = args["content"]
        
        # Normalisasi path
        real_path = os.path.normpath(path)

        # Pastikan direktori ada
        dir_path = os.path.dirname(real_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Tulis file
        with open(real_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {
            "success": True, 
            "message": f"File ditulis ke: {real_path}"
        }
        
    except Exception as e:
        return {
            "success": False, 
            "error": str(e),
            "path": args.get("path", "")
        }
