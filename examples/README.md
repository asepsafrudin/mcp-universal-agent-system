# MCP Examples

Direktori ini berisi contoh-contoh penggunaan MCP Server.

## Files

### [mcp_usage_examples.py](file:///home/aseps/MCP/examples/mcp_usage_examples.py)
Contoh lengkap penggunaan MCP tools dari Python:
- File operations (list_dir, read_file, write_file)
- Memory operations (memory_save, memory_search)
- Shell operations (run_shell)
- Complete workflow example

**Cara menjalankan:**
```bash
# Pastikan MCP server running
bash /home/aseps/MCP/mcp-quickstart.sh

# Run examples
python3 /home/aseps/MCP/examples/mcp_usage_examples.py
```

## Use Cases

### 1. Code Analysis dengan Persistent Memory
```python
from shared.mcp_client import mcp_read_file, mcp_memory_save

# Baca dan analisis code
code = mcp_read_file("/workspace/main.py")
analysis = analyze_code(code)

# Simpan ke memory untuk session berikutnya
mcp_memory_save("main_py_analysis", analysis)
```

### 2. Project Documentation
```python
from shared.mcp_client import mcp_list_dir, mcp_write_file

# Explore structure
structure = mcp_list_dir("/workspace")

# Generate docs
docs = generate_documentation(structure)
mcp_write_file("/workspace/DOCS.md", docs)
```

### 3. Iterative Development
```python
from shared.mcp_client import mcp_memory_search, mcp_run_shell

# Retrieve context dari session sebelumnya
context = mcp_memory_search("previous implementation")

# Run tests
result = mcp_run_shell("pytest tests/")
```

## Tips

1. **Memory Search Strategies**:
   - `hybrid` (default) - Best untuk most cases
   - `semantic` - Best untuk conceptual queries
   - `keyword` - Best untuk exact matches

2. **Error Handling**:
   ```python
   result = mcp_read_file(path)
   if result["status"] == "success":
       data = result["data"]
   else:
       print(f"Error: {result['error']}")
   ```

3. **Batch Operations**:
   ```python
   files = ["file1.py", "file2.py", "file3.py"]
   for f in files:
       content = mcp_read_file(f)
       # process...
   ```
