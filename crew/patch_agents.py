
import os
import re

files = [
    '/home/aseps/MCP/crew/agents/researcher.py',
    '/home/aseps/MCP/crew/agents/writer.py',
    '/home/aseps/MCP/crew/agents/checker.py'
]

import_block = """
import sys
import os
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from llm_config import get_llm
except ImportError:
    # Fallback if running from root
    sys.path.append(os.getcwd())
    from llm_config import get_llm
"""

for file_path in files:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue

    with open(file_path, 'r') as f:
        content = f.read()

    modified = False
    if "from llm_config import get_llm" not in content:
        # Insert after docstring if possible, or just top
        # Check first line
        if content.startswith("#!"):
             lines = content.splitlines()
             lines.insert(1, import_block)
             content = "\n".join(lines)
        else:
             content = import_block + "\n" + content
        modified = True
        print(f"Added imports to {file_path}")

    if "llm=get_llm()" not in content:
        # Regex to safely replace Agent(
        # Assuming Agent( is used to init
        new_content = re.sub(r'Agent\s*\(', 'Agent(llm=get_llm(), ', content)
        if new_content != content:
            content = new_content
            modified = True
            print(f"Injected llm=get_llm() to {file_path}")
    
    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Saved updates to {file_path}")
    else:
        print(f"No changes needed for {file_path}")
