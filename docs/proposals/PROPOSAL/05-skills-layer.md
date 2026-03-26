# 05 - Skills Layer

**Skill Registry & Circular Dependency Detection**

---

## 1. Skill Registry with Cycle Detection

```python
# skills/registry.py
from typing import Dict, List, Set
from skills.base import BaseSkill

class CircularDependencyError(Exception):
    """Raised when circular dependency detected."""
    pass

class SkillRegistry:
    """
    Central registry untuk semua skills.
    Includes circular dependency detection via DFS.
    """
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
    
    def register(self, skill: BaseSkill) -> None:
        """
        Register skill dengan circular dependency check.
        Raises CircularDependencyError jika cycle detected.
        """
        if self._detect_cycle(skill.name, skill.dependencies):
            raise CircularDependencyError(
                f"Circular dependency detected for skill: {skill.name}\n"
                f"Dependencies: {skill.dependencies}"
            )
        
        self._skills[skill.name] = skill
        self._dependency_graph[skill.name] = set(skill.dependencies)
    
    def _detect_cycle(
        self,
        skill_name: str,
        dependencies: List[str]
    ) -> bool:
        """
        DFS-based cycle detection.
        Returns True jika cycle detected.
        """
        visited = set()
        path = set()
        
        def dfs(node: str) -> bool:
            if node in path:  # Cycle found
                return True
            if node in visited:
                return False
            
            visited.add(node)
            path.add(node)
            
            for dep in self._dependency_graph.get(node, []):
                if dfs(dep):
                    return True
            
            path.remove(node)
            return False
        
        # Simulate adding new skill
        self._dependency_graph[skill_name] = set(dependencies)
        has_cycle = dfs(skill_name)
        del self._dependency_graph[skill_name]
        
        return has_cycle
    
    def get_execution_order(self, skill_name: str) -> List[str]:
        """
        Topological sort untuk skill dependencies.
        Returns execution order (dependencies first).
        """
        visited = set()
        order = []
        
        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            skill = self._skills.get(name)
            if skill:
                for dep in skill.dependencies:
                    visit(dep)
            
            order.append(name)
        
        visit(skill_name)
        return order
```

---

## 2. Skill Composition Example

```python
# Example: Legal research skill yang depend on research dan communication

class LegalResearcherSkill(BaseSkill):
    name = "legal.researcher"
    description = "Research legal documents and precedents"
    dependencies = ["research.synthesizer", "communication.presenter"]
    
    async def execute(self, context: SkillContext) -> TaskResult:
        # 1. Get dependencies
        synthesizer = skill_registry.get("research.synthesizer")
        presenter = skill_registry.get("communication.presenter")
        
        # 2. Query knowledge base
        kb = knowledge_manager.get("hukum-perdata")
        results = await kb.query(context.task.input_data["query"])
        
        # 3. Synthesize findings
        synth_result = await synthesizer.execute(
            SkillContext(
                task=Task(...),  # Sub-task
                memory=context.memory,
                tools_available=context.tools_available
            )
        )
        
        # 4. Format output
        return await presenter.execute(...)
```

---

## 3. Cross-References

- Lihat `04-knowledge-layer.md` untuk knowledge yang digunakan skills
- Lihat `06-agents-layer.md` untuk agent yang menggunakan skills

---

**Prev:** [04-knowledge-layer.md](04-knowledge-layer.md)  
**Next:** [06-agents-layer.md](06-agents-layer.md)
