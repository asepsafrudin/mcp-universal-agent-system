from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json

class SubTask(BaseModel):
    id: int
    agent_type: str
    operation: str
    params: Dict[str, Any]
    dependencies: List[int] = []
    status: str = "PENDING"
    result: Optional[Any] = None

class ExecutionPlan(BaseModel):
    task_id: str
    objective: str
    subtasks: List[SubTask]
    risk_level: str = "low"

class PlanningEngine:
    """Mesin dekomposisi tugas menjadi rencana eksekusi terstruktur"""
    
    def __init__(self):
        pass

    async def decompose(self, task_content: str) -> ExecutionPlan:
        """
        Dekomposisi tugas menggunakan logika cerdas.
        """
        subtasks = []
        content_lower = task_content.lower()
        
        if "audit" in content_lower and "storage" not in content_lower and "docker" not in content_lower:
            subtasks = [
                SubTask(id=1, agent_type="FileAgent", operation="list", params={"path": "."}),
                SubTask(id=2, agent_type="CodeAgent", operation="analyze", params={"task": "security audit"}, dependencies=[1]),
                SubTask(id=3, agent_type="FileAgent", operation="write", params={"path": "audit_report.md", "content": "Hasil Audit..."}, dependencies=[2])
            ]
        elif "docker" in content_lower or "storage" in content_lower:
            subtasks = [
                SubTask(id=1, agent_type="TerminalAgent", operation="execute", params={"command": "docker system df"}),
                SubTask(id=2, agent_type="TerminalAgent", operation="execute", params={"command": "docker container prune -f && docker image prune -f"}),
                SubTask(id=3, agent_type="TerminalAgent", operation="execute", params={"command": "docker system df"}),
            ]
        elif "research" in content_lower or "cari" in content_lower or "radar" in content_lower:
            # Ekstraksi keyword sederhana (hilangkan stop words)
            search_query = task_content
            for word in ["Lakukan", "research", "tentang", "cari", "tampilkan", "radar"]:
                search_query = search_query.replace(word, "").replace(word.lower(), "")
            search_query = search_query.strip().strip(".")
            
            subtasks = [
                SubTask(id=1, agent_type="ResearchAgent", operation="tech_scan", params={"query": search_query}),
                SubTask(id=2, agent_type="FileAgent", operation="write", params={"path": "research_report.md", "content": "Hasil riset akan diupdate..."}, dependencies=[1])
            ]
        elif any(kw in content_lower for kw in ["win", "powershell", "ps1", "get-process", "get-service", "stop-process"]):
            is_admin_req = any(kw in content_lower for kw in ["admin", "feature", "enable", "disable", "install"])
            subtasks = [
                SubTask(id=1, agent_type="WindowsAgent", operation="powershell", params={
                    "command": task_content,
                    "elevated": is_admin_req
                }),
            ]
        elif any(kw in content_lower for kw in ["git", "github", "gh", "repo", "commit", "push", "pull request", "issue"]):
            operation = "gh" if any(kw in content_lower for kw in ["gh", "issue", "pr", "repo", "release"]) else "git"
            subtasks = [
                SubTask(id=1, agent_type="GitHubAgent", operation=operation, params={"command": task_content}),
            ]
        else:
            # Default fallback: Coba cari di memori lalu eksekusi shell
            subtasks = [
                SubTask(id=1, agent_type="SearchAgent", operation="search", params={"query": task_content}),
                SubTask(id=2, agent_type="TerminalAgent", operation="execute", params={"command": f"echo 'Processing: {task_content}'"}),
            ]
            
        return ExecutionPlan(
            task_id="task_" + str(hash(task_content))[:8],
            objective=task_content,
            subtasks=subtasks
        )
