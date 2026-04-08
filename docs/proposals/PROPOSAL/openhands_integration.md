# OpenHands ↔ mcp-unified Integration

> Panduan lengkap: Arsitektur, System Prompt, dan Kode Plugin  
> Target: OpenHands SDK via Python, dijalankan sebagai tool & orchestrated dari MCP pipeline

---

## 1. Arsitektur Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        mcp-unified                              │
│                                                                 │
│  ┌──────────────┐    ┌───────────────────────────────────────┐  │
│  │  Telegram /  │    │          MCP Pipeline                 │  │
│  │  WhatsApp    │───▶│  Planner  ──▶  Tool Dispatcher        │  │
│  │  Bot         │    │                     │                 │  │
│  └──────────────┘    └─────────────────────┼─────────────────┘  │
│                                            │                    │
│                      ┌─────────────────────▼─────────────────┐  │
│                      │   plugins/openhands/                  │  │
│                      │                                       │  │
│                      │  ┌─────────────────────────────────┐  │  │
│                      │  │  openhands_tool.py              │  │  │
│                      │  │  @registry.register             │  │  │
│                      │  │  - run_coding_task()            │  │  │
│                      │  │  - get_task_status()            │  │  │
│                      │  │  - list_active_agents()         │  │  │
│                      │  │  - cancel_task()                │  │  │
│                      │  └──────────────┬──────────────────┘  │  │
│                      │                 │                      │  │
│                      │  ┌──────────────▼──────────────────┐  │  │
│                      │  │  OpenHandsOrchestrator          │  │  │
│                      │  │  (SDK wrapper + session mgmt)   │  │  │
│                      │  └──────────────┬──────────────────┘  │  │
│                      └─────────────────┼──────────────────────┘  │
└────────────────────────────────────────┼────────────────────────┘
                                         │ OpenHands SDK
                                         ▼
                        ┌────────────────────────────┐
                        │  OpenHands Agent Runtime   │
                        │  - CodeActAgent            │
                        │  - Sandboxed Docker env    │
                        │  - LLM Backend (Claude/GPT)│
                        └────────────────────────────┘
```

### Aliran Data (Happy Path)

```
User/Bot  ──▶  tools/call {run_coding_task}
               │
               ▼
         OpenHandsOrchestrator.submit(task)
               │  async, returns task_id
               ▼
         Redis: store task_id + status="running"
               │
               ▼  (background)
         OpenHands SDK: Conversation.run()
               │
               ▼
         Callback: update Redis status="done" + result
               │
               ▼
         tools/call {get_task_status} ──▶ return result
```

---

## 2. Struktur Direktori Plugin

```
plugins/openhands/
├── __init__.py
├── openhands_tool.py        ← MCP tool registrations
├── orchestrator.py          ← SDK wrapper & session manager
├── prompt_templates.py      ← System prompts untuk agent
├── config.py                ← Konfigurasi via env vars
└── schemas.py               ← Pydantic models
```

---

## 3. System Prompt untuk OpenHands Agent

File: `plugins/openhands/prompt_templates.py`

### 3.1 — Base System Prompt (CodeAct Agent)

```
OPENHANDS_BASE_SYSTEM_PROMPT = """
Kamu adalah software engineering agent yang beroperasi di dalam ekosistem mcp-unified.
Kamu memiliki akses ke terminal, file system (sandbox), dan web browser.

## Identitasmu
- Nama: OpenHands Agent (dipanggil oleh MCP Orchestrator)
- Mode: Autonomous coding execution
- Bahasa output default: Bahasa Indonesia (kecuali untuk kode/error teknis)

## Prinsip Kerja
1. SELALU buat rencana singkat (1-3 baris) sebelum mengeksekusi
2. Gunakan bash untuk mengecek kondisi environment sebelum menulis kode
3. Simpan progress ke file `TASK_LOG.md` di workspace
4. Jika menemui error, coba maksimal 3x sebelum report ke orchestrator
5. Saat task selesai, WAJIB buat file `RESULT.json` dengan format:
   {
     "status": "success" | "failed" | "partial",
     "summary": "ringkasan apa yang dilakukan",
     "files_created": [],
     "files_modified": [],
     "errors": [],
     "next_steps": []
   }

## Batasan
- JANGAN akses network ke luar sandbox kecuali diminta eksplisit
- JANGAN modifikasi file di luar workspace yang ditentukan
- JANGAN simpan credential atau secret ke file apapun
- Maksimum durasi eksekusi: sesuai REQUEST_TIMEOUT di config

## Konteks mcp-unified
Kamu dipanggil dari sistem MCP. Task yang kamu terima sudah divalidasi oleh
planner dan dispatcher. Workspace-mu ada di: {workspace_path}
"""
```

### 3.2 — Task-Specific Prompt Wrapper

```
CODING_TASK_PROMPT = """
## Task ID: {task_id}
## Diminta oleh: {requested_by}
## Timestamp: {timestamp}

## Deskripsi Task:
{task_description}

## Konteks Tambahan:
{context}

## File/Resource yang Disediakan:
{provided_files}

## Output yang Diharapkan:
{expected_output}

---
Mulai eksekusi. Ingat: buat RESULT.json saat selesai.
"""
```

### 3.3 — Orchestrator Meta-Prompt (untuk LLM yang mengontrol OpenHands)

```
ORCHESTRATOR_PROMPT = """
Kamu adalah MCP Orchestrator yang memutuskan kapan dan bagaimana mendelegasikan
task ke OpenHands agent.

## Kapan delegasikan ke OpenHands:
- Task membutuhkan penulisan/modifikasi kode > 20 baris
- Task membutuhkan eksekusi multi-langkah di filesystem
- Task melibatkan debugging, refactoring, atau test generation
- Task butuh interaksi dengan shell command kompleks

## Kapan JANGAN delegasikan ke OpenHands:
- Query informasi sederhana (gunakan memory_search)
- Task < 5 menit yang bisa diselesaikan inline
- Task yang butuh human approval dulu

## Format Delegasi:
Saat memutuskan delegasi, output JSON ini:
{
  "delegate_to": "openhands",
  "task_description": "...",  // deskripsi jelas dan spesifik
  "expected_output": "...",   // apa yang harus ada di RESULT.json
  "context": "...",           // konteks dari conversation history
  "priority": "high|medium|low",
  "timeout_minutes": 30
}
"""
```

---

## 4. Kode Plugin Lengkap

### 4.1 — `plugins/openhands/config.py`

```python
import os
from pydantic import BaseSettings

class OpenHandsConfig(BaseSettings):
    # LLM Backend untuk OpenHands
    llm_model: str = os.getenv("OPENHANDS_LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    
    # Workspace
    workspace_base: str = os.getenv("OPENHANDS_WORKSPACE", "/tmp/openhands_workspaces")
    
    # Timeouts
    task_timeout_seconds: int = int(os.getenv("OPENHANDS_TIMEOUT", "1800"))  # 30 menit
    max_concurrent_agents: int = int(os.getenv("OPENHANDS_MAX_AGENTS", "3"))
    
    # Redis key prefix
    redis_prefix: str = "openhands:task:"

config = OpenHandsConfig()
```

### 4.2 — `plugins/openhands/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class TaskStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    SUCCESS   = "success"
    FAILED    = "failed"
    CANCELLED = "cancelled"
    TIMEOUT   = "timeout"

class CodingTaskRequest(BaseModel):
    task_description: str = Field(..., description="Deskripsi task yang jelas dan spesifik")
    expected_output: str  = Field(..., description="Output yang diharapkan dari task ini")
    context: str          = Field("", description="Konteks tambahan dari conversation history")
    requested_by: str     = Field("mcp_orchestrator", description="Siapa/apa yang memanggil task ini")
    priority: str         = Field("medium", description="high | medium | low")
    timeout_minutes: int  = Field(30, description="Batas waktu dalam menit")
    provided_files: List[str] = Field([], description="Path file yang perlu disediakan ke agent")

class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    summary: str = ""
    files_created: List[str] = []
    files_modified: List[str] = []
    errors: List[str] = []
    next_steps: List[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    workspace_path: str = ""
```

### 4.3 — `plugins/openhands/orchestrator.py`

```python
import asyncio
import json
import uuid
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import redis.asyncio as aioredis

from .config import config
from .schemas import CodingTaskRequest, TaskResult, TaskStatus
from .prompt_templates import (
    OPENHANDS_BASE_SYSTEM_PROMPT,
    CODING_TASK_PROMPT,
)

logger = logging.getLogger(__name__)


class OpenHandsOrchestrator:
    """
    Wrapper di atas OpenHands SDK.
    Mengelola lifecycle task: submit → monitor → retrieve result.
    """

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self._semaphore = asyncio.Semaphore(config.max_concurrent_agents)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def submit_task(self, request: CodingTaskRequest) -> str:
        """Submit task ke OpenHands agent. Returns task_id."""
        task_id = str(uuid.uuid4())[:8]
        workspace_path = self._create_workspace(task_id)

        initial_state = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            started_at=datetime.utcnow(),
            workspace_path=str(workspace_path),
        )
        await self._save_task(task_id, initial_state)

        # Jalankan di background agar tidak blocking MCP pipeline
        asyncio.create_task(
            self._run_agent(task_id, request, workspace_path)
        )

        logger.info(f"[OpenHands] Task {task_id} submitted, workspace: {workspace_path}")
        return task_id

    async def get_status(self, task_id: str) -> Optional[TaskResult]:
        """Ambil status + hasil task dari Redis."""
        raw = await self.redis.get(f"{config.redis_prefix}{task_id}")
        if not raw:
            return None
        return TaskResult(**json.loads(raw))

    async def cancel_task(self, task_id: str) -> bool:
        """Set flag cancel di Redis; agent akan cek flag ini."""
        await self.redis.set(f"{config.redis_prefix}{task_id}:cancel", "1", ex=3600)
        result = await self.get_status(task_id)
        if result:
            result.status = TaskStatus.CANCELLED
            await self._save_task(task_id, result)
        return True

    async def list_active_tasks(self) -> list[dict]:
        """List semua task yang sedang running/pending."""
        keys = await self.redis.keys(f"{config.redis_prefix}*")
        tasks = []
        for key in keys:
            if b":cancel" in key:
                continue
            raw = await self.redis.get(key)
            if raw:
                data = json.loads(raw)
                if data.get("status") in ("pending", "running"):
                    tasks.append({
                        "task_id": data["task_id"],
                        "status": data["status"],
                        "started_at": data.get("started_at"),
                        "workspace_path": data.get("workspace_path"),
                    })
        return tasks

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _create_workspace(self, task_id: str) -> Path:
        workspace = Path(config.workspace_base) / task_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    async def _save_task(self, task_id: str, result: TaskResult):
        await self.redis.set(
            f"{config.redis_prefix}{task_id}",
            result.json(),
            ex=86400  # TTL 24 jam
        )

    async def _run_agent(
        self,
        task_id: str,
        request: CodingTaskRequest,
        workspace_path: Path,
    ):
        """Jalankan OpenHands agent via SDK. Semaphore-limited."""
        async with self._semaphore:
            # Update status → running
            result = await self.get_status(task_id)
            result.status = TaskStatus.RUNNING
            await self._save_task(task_id, result)

            try:
                # Bangun prompt lengkap
                full_prompt = CODING_TASK_PROMPT.format(
                    task_id=task_id,
                    requested_by=request.requested_by,
                    timestamp=datetime.utcnow().isoformat(),
                    task_description=request.task_description,
                    context=request.context or "-",
                    provided_files="\n".join(request.provided_files) or "-",
                    expected_output=request.expected_output,
                )

                system_prompt = OPENHANDS_BASE_SYSTEM_PROMPT.format(
                    workspace_path=str(workspace_path)
                )

                # ── OpenHands SDK call ──────────────────────────────── #
                from openhands.sdk import LLM, Agent, Conversation
                from openhands.tools.file_editor import FileEditorTool
                from openhands.tools.terminal import TerminalTool
                from openhands.tools.task_tracker import TaskTrackerTool

                llm = LLM(
                    model=config.llm_model,
                    api_key=config.llm_api_key,
                    system_prompt=system_prompt,
                )

                agent = Agent(
                    llm=llm,
                    tools=[
                        TerminalTool(),
                        FileEditorTool(),
                        TaskTrackerTool(),
                    ],
                )

                conversation = Conversation(
                    agent=agent,
                    workspace=str(workspace_path),
                )

                # Cek cancel flag sebelum run
                cancel_flag = await self.redis.get(
                    f"{config.redis_prefix}{task_id}:cancel"
                )
                if cancel_flag:
                    result.status = TaskStatus.CANCELLED
                    await self._save_task(task_id, result)
                    return

                # Run dengan timeout
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: conversation.send_message(full_prompt)
                    ),
                    timeout=request.timeout_minutes * 60,
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, conversation.run
                )
                # ───────────────────────────────────────────────────── #

                # Parse RESULT.json yang dibuat agent
                result_file = workspace_path / "RESULT.json"
                if result_file.exists():
                    agent_result = json.loads(result_file.read_text())
                    result.status = TaskStatus(
                        agent_result.get("status", "success")
                    )
                    result.summary       = agent_result.get("summary", "")
                    result.files_created = agent_result.get("files_created", [])
                    result.files_modified= agent_result.get("files_modified", [])
                    result.errors        = agent_result.get("errors", [])
                    result.next_steps    = agent_result.get("next_steps", [])
                else:
                    result.status  = TaskStatus.SUCCESS
                    result.summary = "Task selesai (RESULT.json tidak ditemukan)"

            except asyncio.TimeoutError:
                result.status = TaskStatus.TIMEOUT
                result.errors = [f"Task melebihi batas waktu {request.timeout_minutes} menit"]
                logger.warning(f"[OpenHands] Task {task_id} TIMEOUT")

            except Exception as e:
                result.status = TaskStatus.FAILED
                result.errors = [str(e)]
                logger.exception(f"[OpenHands] Task {task_id} FAILED: {e}")

            finally:
                result.completed_at = datetime.utcnow()
                await self._save_task(task_id, result)
                logger.info(
                    f"[OpenHands] Task {task_id} completed with status: {result.status}"
                )
```

### 4.4 — `plugins/openhands/openhands_tool.py`

```python
"""
MCP Tool registrations untuk OpenHands integration.
Drop-in ke folder plugins/ — auto-discovery oleh mcp-unified.
"""
import json
import logging
from typing import Any

# Import registry dari mcp-unified core
from execution.registry import registry
from memory.redis_client import get_redis  # sesuaikan path import

from .orchestrator import OpenHandsOrchestrator
from .schemas import CodingTaskRequest

logger = logging.getLogger(__name__)
_orchestrator: OpenHandsOrchestrator | None = None


async def _get_orchestrator() -> OpenHandsOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        redis = await get_redis()
        _orchestrator = OpenHandsOrchestrator(redis)
    return _orchestrator


# ──────────────────────────────────────────────────────────────────────── #
# Tool 1: run_coding_task                                                  #
# ──────────────────────────────────────────────────────────────────────── #

@registry.register(
    name="run_coding_task",
    description=(
        "Delegasikan task coding/engineering ke OpenHands agent. "
        "Agent akan menulis kode, menjalankan command, dan menghasilkan file. "
        "Returns task_id untuk polling status."
    ),
    parameters={
        "task_description": {
            "type": "string",
            "description": "Deskripsi task yang jelas: apa yang harus dibuat/diubah/diperbaiki",
            "required": True,
        },
        "expected_output": {
            "type": "string",
            "description": "Output yang diharapkan: file apa, fungsi apa, test apa",
            "required": True,
        },
        "context": {
            "type": "string",
            "description": "Konteks tambahan: riwayat conversation, codebase info, dsb",
            "required": False,
        },
        "requested_by": {
            "type": "string",
            "description": "Identifier pemanggil (telegram_bot, planner, user_id, dll)",
            "required": False,
        },
        "priority": {
            "type": "string",
            "description": "high | medium | low",
            "required": False,
        },
        "timeout_minutes": {
            "type": "integer",
            "description": "Batas waktu eksekusi dalam menit (default: 30)",
            "required": False,
        },
    },
)
async def run_coding_task(**kwargs) -> dict[str, Any]:
    try:
        request = CodingTaskRequest(**kwargs)
        orchestrator = await _get_orchestrator()
        task_id = await orchestrator.submit_task(request)

        return {
            "status": "submitted",
            "task_id": task_id,
            "message": (
                f"Task berhasil didelegasikan ke OpenHands agent. "
                f"Gunakan `get_task_status(task_id='{task_id}')` untuk cek progress."
            ),
            "poll_hint": f"Cek status setiap 30 detik dengan: get_task_status(task_id='{task_id}')",
        }
    except Exception as e:
        logger.exception(f"run_coding_task error: {e}")
        return {"status": "error", "message": str(e)}


# ──────────────────────────────────────────────────────────────────────── #
# Tool 2: get_task_status                                                  #
# ──────────────────────────────────────────────────────────────────────── #

@registry.register(
    name="get_task_status",
    description=(
        "Cek status dan hasil dari OpenHands coding task. "
        "Gunakan setelah run_coding_task untuk polling progress atau ambil hasil akhir."
    ),
    parameters={
        "task_id": {
            "type": "string",
            "description": "Task ID yang dikembalikan oleh run_coding_task",
            "required": True,
        },
    },
)
async def get_task_status(task_id: str) -> dict[str, Any]:
    try:
        orchestrator = await _get_orchestrator()
        result = await orchestrator.get_status(task_id)

        if not result:
            return {"status": "not_found", "task_id": task_id}

        return result.dict()
    except Exception as e:
        logger.exception(f"get_task_status error: {e}")
        return {"status": "error", "message": str(e)}


# ──────────────────────────────────────────────────────────────────────── #
# Tool 3: list_active_agents                                               #
# ──────────────────────────────────────────────────────────────────────── #

@registry.register(
    name="list_active_agents",
    description="List semua OpenHands agent yang sedang berjalan atau pending.",
    parameters={},
)
async def list_active_agents() -> dict[str, Any]:
    try:
        orchestrator = await _get_orchestrator()
        tasks = await orchestrator.list_active_tasks()
        return {
            "active_count": len(tasks),
            "tasks": tasks,
        }
    except Exception as e:
        logger.exception(f"list_active_agents error: {e}")
        return {"status": "error", "message": str(e)}


# ──────────────────────────────────────────────────────────────────────── #
# Tool 4: cancel_task                                                       #
# ──────────────────────────────────────────────────────────────────────── #

@registry.register(
    name="cancel_coding_task",
    description="Batalkan OpenHands coding task yang sedang berjalan.",
    parameters={
        "task_id": {
            "type": "string",
            "description": "Task ID yang ingin dibatalkan",
            "required": True,
        },
    },
)
async def cancel_coding_task(task_id: str) -> dict[str, Any]:
    try:
        orchestrator = await _get_orchestrator()
        success = await orchestrator.cancel_task(task_id)
        return {
            "status": "cancelled" if success else "not_found",
            "task_id": task_id,
        }
    except Exception as e:
        logger.exception(f"cancel_coding_task error: {e}")
        return {"status": "error", "message": str(e)}
```

---

## 5. Environment Variables Tambahan

Tambahkan ke `.env` kamu:

```bash
# OpenHands SDK
OPENHANDS_LLM_MODEL=anthropic/claude-sonnet-4-5-20250929
LLM_API_KEY=sk-ant-...              # atau ANTHROPIC_API_KEY
OPENHANDS_WORKSPACE=/tmp/openhands_workspaces
OPENHANDS_TIMEOUT=1800              # 30 menit
OPENHANDS_MAX_AGENTS=3              # max concurrent agents
```

---

## 6. Cara Install OpenHands SDK

```bash
# Di virtual environment mcp-unified
pip install openhands-ai

# Atau dari source (untuk versi terbaru)
pip install git+https://github.com/OpenHands/software-agent-sdk.git
```

Tambahkan ke `requirements.txt`:
```
openhands-ai>=0.1.0
```

---

## 7. Contoh Penggunaan dari Telegram Bot

```python
# Contoh: user kirim pesan ke Telegram bot
# "buatkan CRUD API untuk tabel produk"

# Bot mengirim ke MCP pipeline:
response = await mcp_client.call_tool("run_coding_task", {
    "task_description": """
        Buat CRUD API untuk tabel 'produk' menggunakan FastAPI.
        Tabel memiliki field: id, nama, harga, stok, created_at.
        Gunakan SQLAlchemy + PostgreSQL.
    """,
    "expected_output": "File: models.py, routers/produk.py, schemas.py",
    "context": "Project ini adalah bagian dari mcp-unified backend",
    "requested_by": "telegram_bot:user_123",
    "priority": "medium",
    "timeout_minutes": 20,
})

task_id = response["task_id"]

# Polling status (bisa diloop di bot)
import asyncio

for _ in range(40):  # max 20 menit (40 x 30 detik)
    await asyncio.sleep(30)
    status = await mcp_client.call_tool("get_task_status", {"task_id": task_id})
    
    if status["status"] in ("success", "failed", "timeout", "cancelled"):
        # Kirim hasil ke user Telegram
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Task selesai!\n\n{status['summary']}\n\nFile dibuat: {status['files_created']}"
        )
        break
    else:
        # Opsional: kirim update progress
        await bot.send_message(chat_id=user_id, text=f"⏳ Agent masih bekerja...")
```

---

## 8. Integrasi dengan Admin UI

Tambahkan service `openhands` ke daftar service yang bisa dikontrol dari Admin UI (`/admin/services`):

```python
# Di konfigurasi service controller mcp-unified
AVAILABLE_SERVICES = {
    ...existing services...,
    "openhands_agent": {
        "display_name": "OpenHands Agent Runtime",
        "description": "Background agent untuk autonomous coding tasks",
        "status_check": lambda: check_redis_active_agents(),
    }
}
```

---

## 9. Checklist Implementasi

- [ ] Install `openhands-ai` ke `requirements.txt`
- [ ] Buat folder `plugins/openhands/` dengan semua file di atas
- [ ] Tambahkan env vars ke `.env`
- [ ] Pastikan Redis running (sudah ada di mcp-unified)
- [ ] Test via `POST /tools/call` dengan payload `run_coding_task`
- [ ] Integrasikan polling ke Telegram bot handler
- [ ] Tambahkan `openhands_agent` ke Admin UI service list
- [ ] Sesuaikan path import `from execution.registry import registry` dengan struktur actual mcp-unified
