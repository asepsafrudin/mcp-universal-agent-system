# 06 - Agents Layer

**Agent Profiles, Mission Manager & Multi-Agent Orchestrator**

---

## 1. Mission Manager (The Soul)

Komponen otonomi yang memberikan agen kemampuan proaktif.

```python
# agents/mission_manager.py

class MissionManager:
    """
    Sistem saraf pusat otonomi agen.
    Memberikan agen kemampuan self-initiated actions.
    """
    
    def __init__(self, agent: 'BaseAgent', config: Dict[str, Any]):
        self.agent = agent
        self.check_interval = config.get("check_interval", 3600)  # 1 jam
        
    async def run_autonomy_cycle(self):
        """Siklus 'kehendak' agen."""
        active_missions = await self.get_active_missions()
        
        for mission in active_missions:
            # 1. SENSE - Perception
            evidence = await self.agent.knowledge.query(
                query=mission.success_criteria,
                namespace=self.agent.namespace
            )
            
            # 2. CONTEMPLATE - Reasoning
            evaluation = await self.evaluate_gap(mission, evidence)
            
            if evaluation.has_gap:
                # 3. ACT - Proactive Planning
                proactive_plan = await self.agent.plan(
                    description=f"Proactive: {mission.objective}",
                    context={"gap": evaluation.gap_description}
                )
                
                # Submit ke orchestrator
                for task in proactive_plan:
                    await self.agent.orchestrator.submit(task)
                
                mission.status = MissionStatus.IN_PROGRESS
                mission.current_gap = evaluation.gap_description
            
            mission.last_evaluated = datetime.now()
            await self.save_mission_state(mission)
```

### Governor Pattern (Safety)

```python
# core/governor.py

class Governor:
    """
    Safety guard untuk otonomi agen.
    Mencegah runaway agents dan kontrol biaya.
    """
    
    def __init__(self):
        self.daily_token_budget = 100_000  # Token limit per hari
        self.requires_approval = True       # HITL untuk misi kritis
    
    async def approve_mission_action(
        self,
        mission: Mission,
        proposed_tasks: List[Task]
    ) -> bool:
        """
        Approve atau reject proactive action.
        Returns True jika approved.
        """
        # Check token budget
        estimated_tokens = self.estimate_tokens(proposed_tasks)
        if estimated_tokens > self.daily_token_budget:
            return False
        
        # HITL untuk misi kritis
        if mission.priority >= 8 and self.requires_approval:
            return await self.request_human_approval(mission, proposed_tasks)
        
        return True
```

---

## 2. Agent Orchestrator

```python
# agents/orchestrator.py
from enum import Enum
from typing import Dict, List, Optional
from agents.base import BaseAgent
from core.task import Task, TaskResult

class OrchestrationStrategy(Enum):
    HIERARCHICAL = "hierarchical"  # Manager → Workers → Manager
    PARALLEL = "parallel"          # Independent sub-tasks
    SEQUENTIAL = "sequential"      # Chain: A → B → C

class MultiAgentOrchestrator:
    """
    Coordinates multiple agents untuk complex tasks.
    """
    
    def __init__(self):
        self.manager_agent: Optional[BaseAgent] = None
        self.worker_agents: Dict[str, BaseAgent] = {}
    
    async def execute(
        self,
        task: Task,
        strategy: OrchestrationStrategy = OrchestrationStrategy.HIERARCHICAL
    ) -> TaskResult:
        if strategy == OrchestrationStrategy.HIERARCHICAL:
            return await self._hierarchical(task)
        elif strategy == OrchestrationStrategy.PARALLEL:
            return await self._parallel(task)
        else:
            return await self._sequential(task)
    
    async def _hierarchical(self, task: Task) -> TaskResult:
        # 1. Manager decomposes
        sub_tasks = await self.manager_agent.plan(task)
        
        # 2. Execute dengan workers
        results = []
        for sub in sub_tasks:
            worker = self._select_worker(sub)
            result = await worker.run(sub)
            results.append(result)
        
        # 3. Manager synthesizes
        return await self.manager_agent.synthesize(results, task)
    
    def _select_worker(self, task: Task) -> BaseAgent:
        """Route task ke most appropriate worker."""
        scores = {
            name: agent.can_handle(task)
            for name, agent in self.worker_agents.items()
        }
        best = max(scores, key=scores.get)
        return self.worker_agents[best]
```

---

## 2. Cross-References

- Lihat `07-domain-examples.md` untuk concrete agent implementations

---

**Prev:** [05-skills-layer.md](05-skills-layer.md)  
**Next:** [07-domain-examples.md](07-domain-examples.md)
