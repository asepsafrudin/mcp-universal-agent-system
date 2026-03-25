# TODO: MCP Semantic Analysis Integration
Status: 🔄 In Progress

## Steps:
- [✅] 1. Ensure editable install mcp-unified & semantic_analysis ✅ (`cd mcp-unified && pip install -r requirements.txt`, `cd core/semantic_analysis && pip install -r requirements.txt && pip install -e .`)
- [✅] 2. Create tools/code/semantic_tools.py (4 tools: semantic_analyze_file, ai_semantic_analyze, get_code_context, find_references) ✅
- [ ] 3. Edit mcp_server.py (add imports & registry.register)
- [ ] 4. Update requirements.txt (add semantic deps)
- [ ] 5. Test server (`cd mcp-unified && ./run.sh`), verify tools listed
- [ ] 6. VSCode test integration

Current step: 1/6
