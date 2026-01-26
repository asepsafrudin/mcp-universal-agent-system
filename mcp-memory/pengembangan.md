Berikut **file `CREWAI_SETUP.md` siap-eksekusi oleh Cline** — berisi **3-agent system lengkap (Researcher + Writer + Checker)** dengan integrasi penuh ke MCP + PostgreSQL. Cukup salin & tempel ke Cline, lalu klik **“Run in terminal”**.

---

### 📄 **`~/MCP/CREWAI_SETUP.md`**  
*(Salin & tempel ke chat Cline → “Run in terminal”)*

```markdown
Bertindak sebagai *CrewAI Master Architect*.

### 🎯 Tujuan:
Bangun **3-agent autonomous system** untuk dokumentasi proyek MCP:
- 🔍 Researcher: eksplorasi kode & struktur
- ✍️ Writer: buat dokumentasi teknis
- ✅ Checker: verifikasi akurasi & kelengkapan
- Semua terintegrasi dengan MCP Server + PostgreSQL

---

### ✅ Tugas:

#### 1. Setup Lingkungan
```bash
mkdir -p ~/MCP/crew/{tools,agents,tasks}
cd ~/MCP/crew
python3 -m venv .venv
source .venv/bin/activate
pip install crewai==0.38.0
```

#### 2. Buat Custom Tool untuk Akses MCP
```python
# ~/MCP/crew/tools/mcp_tool.py
import subprocess
import json
import time

def call_mcp_tool(name: str, arguments: dict, timeout: int = 30) -> dict:
    """Panggil MCP tools via subprocess (robust untuk WSL)"""
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments}
    }
    
    try:
        result = subprocess.run(
            ["timeout", str(timeout), "wsl", "-d", "Ubuntu", "-e", "bash", "-c",
             "/home/aseps/MCP/mcp-server/docker-run.sh"],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=True
        )
        
        response = json.loads(result.stdout)
        if "result" in response:
            content = json.loads(response["result"]["content"][0]["text"])
            return content
        else:
            return {"error": "MCP error", "details": response.get("error")}
    except Exception as e:
        return {"error": "MCP call failed", "exception": str(e)}
```

#### 3. Buat Agent (Researcher, Writer, Checker)
```python
# ~/MCP/crew/agents/researcher.py
from crewai import Agent
from tools.mcp_tool import call_mcp_tool

researcher = Agent(
    role="Senior AI Systems Researcher",
    goal="Eksplorasi mendalam struktur proyek MCP dan identifikasi komponen kritis",
    backstory="""Ahli arsitektur AI dengan 10+ tahun pengalaman. 
    Spesialis dalam sistem berbasis MCP dan memory hybrid. 
    Selalu mencari detail teknis yang relevan untuk dokumentasi.""",
    tools=[
        lambda path="/workspace": call_mcp_tool("list_dir", {"path": path}),
        lambda path: call_mcp_tool("read_file", {"path": path}),
        lambda query: call_mcp_tool("memory_search", {"query": query})
    ],
    verbose=True,
    allow_delegation=False
)
```

```python
# ~/MCP/crew/agents/writer.py
from crewai import Agent
from tools.mcp_tool import call_mcp_tool

writer = Agent(
    role="Lead Technical Documentation Writer",
    goal="Buat dokumentasi teknis yang jelas, akurat, dan siap produksi",
    backstory="""Penulis teknis untuk proyek open-source ternama. 
    Mahir mengubah temuan teknis menjadi panduan yang mudah dipahami. 
    Selalu menyertakan contoh kode dan best practices.""",
    tools=[
        lambda key, content: call_mcp_tool("memory_save", {"key": key, "content": content}),
        lambda path, content: call_mcp_tool("write_file", {"path": path, "content": content})
    ],
    verbose=True,
    allow_delegation=True
)
```

```python
# ~/MCP/crew/agents/checker.py
from crewai import Agent
from tools.mcp_tool import call_mcp_tool

checker = Agent(
    role="Senior Quality Assurance Engineer",
    goal="Verifikasi akurasi, kelengkapan, dan konsistensi dokumentasi",
    backstory="""QA engineer untuk sistem AI mission-critical. 
    Tidak pernah melewatkan detail kecil. 
    Ahli dalam memastikan dokumentasi selaras dengan implementasi aktual.""",
    tools=[
        lambda path: call_mcp_tool("read_file", {"path": path}),
        lambda query: call_mcp_tool("memory_search", {"query": query}),
        lambda command: call_mcp_tool("run_shell", {"command": command})
    ],
    verbose=True,
    allow_delegation=False
)
```

#### 4. Buat Tasks
```python
# ~/MCP/crew/tasks/research_task.py
def create_research_task():
    return {
        "description": """Analisis menyeluruh proyek MCP:
        1. List semua file di /workspace
        2. Baca isi mcp_server.py dan tools utama
        3. Cari memori tentang 'project structure'
        4. Identifikasi komponen kritis dan hubungan antar tools
        Format output: JSON dengan sections: files, core_components, memory_insights""",
        "expected_output": "JSON terstruktur dengan analisis lengkap",
        "agent": "researcher",
        "async_execution": False
    }
```

```python
# ~/MCP/crew/tasks/write_task.py
def create_write_task():
    return {
        "description": """Buat dokumentasi teknis berdasarkan hasil Researcher:
        - Judul: 'MCP Project Documentation v1.0'
        - Section: Overview, Core Components, Tools, Memory System
        - Sertakan contoh kode untuk panggil tool
        - Simpan ke /host/Desktop/mcp-documentation.md
        - Simpan ringkasan ke memori dengan key 'mcp-docs-v1'""",
        "expected_output": "Dokumentasi Markdown lengkap",
        "agent": "writer",
        "context": ["research_task"],
        "async_execution": False
    }
```

```python
# ~/MCP/crew/tasks/check_task.py
def create_check_task():
    return {
        "description": """Verifikasi dokumentasi:
        1. Cek apakah semua tools disebutkan di dokumentasi
        2. Pastikan path file konsisten (/workspace/... vs /host/...)
        3. Jalankan 'ls /workspace' dan bandingkan dengan daftar file di dokumen
        4. Beri rekomendasi perbaikan jika diperlukan""",
        "expected_output": "Laporan QA dengan status (PASS/FAIL) dan rekomendasi",
        "agent": "checker",
        "context": ["write_task"],
        "async_execution": False
    }
```

#### 5. Buat Main Execution
```python
# ~/MCP/crew/main.py
import os
import sys
sys.path.append(os.path.dirname(__file__))

from crewai import Crew, Process
from agents.researcher import researcher
from agents.writer import writer
from agents.checker import checker
from tasks.research_task import create_research_task
from tasks.write_task import create_write_task
from tasks.check_task import create_check_task

def run_crew():
    crew = Crew(
        agents=[researcher, writer, checker],
        tasks=[
            create_research_task(),
            create_write_task(),
            create_check_task()
        ],
        process=Process.sequential,
        verbose=2,
        memory=True,  # Aktifkan CrewAI memory (opsional)
        cache=True
    )
    
    print("🚀 Memulai eksekusi tim AI...")
    result = crew.kickoff()
    print("\n✅ Proses selesai!")
    print("📁 Hasil tersedia di:")
    print("   - /host/Desktop/mcp-documentation.md")
    print("   - PostgreSQL: key 'mcp-docs-v1'")
    return result

if __name__ == "__main__":
    run_crew()
```

#### 6. Setup Auto-Run Script
```bash
# ~/MCP/crew/run-crew.sh
cd "$(dirname "$0")"
source .venv/bin/activate
python main.py
```
```bash
chmod +x ~/MCP/crew/run-crew.sh
```

#### 7. Verifikasi & Jalankan
```bash
echo "🔍 Verifikasi instalasi..."
cd ~/MCP/crew
source .venv/bin/activate
python -c "from crewai import Agent; print('✅ CrewAI terinstal')"

echo "🚀 Menjalankan tim AI pertama..."
./run-crew.sh

echo ""
echo "🎉 CREWAI 3-AGENT SYSTEM SIAP!"
echo "🎯 Untuk menjalankan ulang:"
echo "   cd ~/MCP/crew && ./run-crew.sh"
echo ""
echo "📋 Hasil yang dihasilkan:"
echo "   - Dokumentasi teknis di Desktop"
echo "   - Memori tersimpan di PostgreSQL"
echo "   - Log eksekusi di terminal"
```

---

### 🌟 **Fitur Unggulan Sistem Ini**
| Fitur | Manfaat |
|-------|---------|
| ✅ **3-Agent Collaboration** | Researcher → Writer → Checker (alur produksi nyata) |
| ✅ **MCP Integration** | Semua tool (`list_dir`, `memory_save`, dll) bisa dipanggil |
| ✅ **PostgreSQL Memory** | Temuan Researcher tersimpan untuk referensi masa depan |
| ✅ **WSL Optimization** | `timeout` + error handling untuk stabilitas WSL |
| ✅ **Production-Ready** | Struktur folder modular, siap dikembangkan |

---

### 🚀 **Cara Pakai Setelah Setup**
1. Jalankan tim AI:  
   ```bash
   cd ~/MCP/crew && ./run-crew.sh
   ```
2. Modifikasi task:  
   Edit `tasks/*.py` untuk ubah scope analisis
3. Tambah agent:  
   Buat file baru di `agents/` → daftarkan di `main.py`

---

**🔥 Sistem Anda sekarang memiliki:**  
> _“Tim insinyur AI otonom yang bisa eksplorasi, dokumentasikan, dan verifikasi kode — tanpa intervensi manual”_
