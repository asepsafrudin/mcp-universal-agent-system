import asyncio
from typing import List, Dict, Any
from engine.planning import ExecutionPlan, SubTask
from agents.specialized_agents import FileAgent, CodeAgent, TerminalAgent, SearchAgent, ResearchAgent, WindowsAgent, GitHubAgent

class ExecutionScheduler:
    """Orkestrator yang menjadwalkan dan mengeksekusi sub-tasks berdasarkan dependensi"""
    
    def __init__(self):
        self.agents = {
            "FileAgent": FileAgent(),
            "CodeAgent": CodeAgent(),
            "TerminalAgent": TerminalAgent(),
            "SearchAgent": SearchAgent(),
            "ResearchAgent": ResearchAgent(),
            "WindowsAgent": WindowsAgent(),
            "GitHubAgent": GitHubAgent()
        }

    async def run(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Menjalankan rencana eksekusi dan mengembalikan hasil agregat"""
        results = {}
        completed_tasks = set()
        
        # Urutkan tugas berdasarkan dependensi (penyederhanaan: sekuensial untuk saat ini)
        # TODO: Implementasi graf dependensi untuk eksekusi paralel yang aman
        for task in plan.subtasks:
            # Tunggu dependensi (jika ada)
            # Karena kita jalankan sekuensial, dependensi dasar sudah terpenuhi
            
            print(f"[*] Meluncurkan {task.agent_type} untuk operasi {task.operation}...")
            task.status = "IN_PROGRESS"
            
            agent = self.agents.get(task.agent_type)
            if not agent:
                task.status = "FAILED"
                task.result = f"Agen {task.agent_type} tidak ditemukan"
                continue
                
            try:
                # Masukkan hasil dari tugas sebelumnya ke params jika dibutuhkan (Context Linkage)
                # Contoh: Jika task 2 bergantung pada task 1, berikan hasil task 1 ke task 2
                if task.dependencies:
                    for dep_id in task.dependencies:
                        task.params[f"context_from_task_{dep_id}"] = results.get(dep_id)

                result = await agent.execute(task.operation, task.params)
                task.result = result
                task.status = "COMPLETED"
                results[task.id] = result
                completed_tasks.add(task.id)
            except Exception as e:
                task.status = "FAILED"
                task.result = str(e)
                print(f"[!] Gagal mengeksekusi tugas {task.id}: {e}")

        return {
            "task_id": plan.task_id,
            "objective": plan.objective,
            "status": "COMPLETED" if all(t.status == "COMPLETED" for t in plan.subtasks) else "PARTIAL_SUCCESS",
            "subtask_results": results
        }
