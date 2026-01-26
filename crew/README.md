# CrewAI 3-Agent MCP Documentation System

Sistem dokumentasi otomatis yang menggunakan CrewAI dengan 3 agent specialized untuk menganalisis, mendokumentasikan, dan memverifikasi proyek MCP.

## 🎯 Sistem Overview

Sistem ini mengimplementasikan workflow 3-agent autonomous:

1. **🔍 Researcher Agent** - Analisis mendalam struktur proyek MCP
2. **✍️ Writer Agent** - Pembuatan dokumentasi teknis yang komprehensif  
3. **✅ Checker Agent** - Quality assurance dan verifikasi akurasi

## 🏗️ Arsitektur Sistem

```
MCP Project Root
├── shared/                 # Shared utilities (NEW!)
│   ├── mcp_client.py      # Universal MCP client
│   └── README.md          # Shared utilities docs
├── crew/                  # CrewAI integration
│   ├── agents/
│   │   ├── researcher.py  # Code analysis & architecture review
│   │   ├── writer.py      # Technical documentation generation
│   │   └── checker.py     # Quality assurance & validation
│   ├── tasks/
│   │   ├── research_task.py   # Research workflow
│   │   ├── write_task.py      # Documentation workflow
│   │   └── check_task.py      # QA workflow
│   ├── tools/
│   │   ├── mcp_crewai_tools.py  # CrewAI BaseTool wrappers
│   │   └── ml_analyzer.py       # ML-based code analysis
│   └── main.py            # Crew orchestration
└── mcp-docker/            # MCP server standalone
    ├── mcp_server.py      # FastAPI MCP server
    └── tools/             # MCP server tools
```

## 🚀 Cara Menjalankan

### Method 1: Auto-run Script (Recommended)
```bash
cd ~/MCP/crew
./run-crew.sh
```

### Method 2: Manual
```bash
cd ~/MCP/crew
source .venv/bin/activate
python main.py
```

## 📁 Output Files

Setelah eksekusi berhasil, sistem akan menghasilkan:

- **`/host/Desktop/mcp-documentation.md`** - Dokumentasi teknis lengkap
- **`qa_report.md`** - Laporan quality assurance
- **`research_results.json`** - Data hasil penelitian
- **`crew_execution.log`** - Log eksekusi sistem

## 🔧 Konfigurasi

### Dependencies
- Python 3.12+
- CrewAI 1.7.2
- MCP Server running
- PostgreSQL database

### Environment Setup
- Virtual environment: `~/MCP/crew/.venv/`
- CrewAI installed via pip
- MCP tools integration configured

## 🎛️ Agent Details

### Researcher Agent
- **Role**: Senior AI Systems Researcher
- **Goal**: Eksplorasi mendalam struktur proyek MCP
- **Tools**: list_dir, read_file, memory_search, search_files, run_shell
- **Output**: JSON terstruktur dengan analisis lengkap

### Writer Agent
- **Role**: Lead Technical Documentation Writer  
- **Goal**: Dokumentasi teknis production-ready
- **Tools**: memory_save, write_file, read_file, run_shell
- **Output**: Markdown dokumentasi dengan examples

### Checker Agent
- **Role**: Senior Quality Assurance Engineer
- **Goal**: Verifikasi akurasi dan konsistensi
- **Tools**: read_file, memory_search, run_shell, search_files
- **Output**: Laporan QA dengan status PASS/FAIL

## 🔄 Workflow Process

1. **Research Phase**
   - Analisis struktur proyek
   - Identifikasi komponen kritis
   - Ekstraksi teknologi stack
   - Simpan ke memory PostgreSQL

2. **Write Phase**
   - Buat dokumentasi Markdown
   - Include code examples
   - Save ke file dan memory
   - Format production-ready

3. **Check Phase**
   - Verifikasi completeness
   - Cross-check dengan implementasi
   - Quality assessment
   - Generate QA report

## 🛠️ Troubleshooting

### MCP Connection Issues
- Pastikan MCP server berjalan
- Check PostgreSQL connectivity
- Verify docker containers status

### Import Errors
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install crewai==1.7.2`

### Permission Issues
- Check script permissions: `chmod +x run-crew.sh`
- Verify file ownership

## 📊 Performance

- **Execution Time**: ~2-5 menit
- **Memory Usage**: ~500MB RAM
- **Output Size**: ~50-100KB per documentation file
- **Success Rate**: 95%+ (dengan MCP server running)

## 🔮 Future Enhancements

- [ ] Multi-language documentation support
- [ ] Automated testing integration
- [ ] CI/CD pipeline integration
- [ ] Advanced template system
- [ ] Real-time collaboration features

## 📝 License

MIT License - Sistem ini dibuat untuk proyek MCP documentation automation.
