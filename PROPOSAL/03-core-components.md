# 03 - Core Components

**Base Classes, Task Schema, & Registry Pattern**

---

## 1. Task & TaskResult Schema

Standardized contract untuk komunikasi antar semua layer.

```python
# core/task.py
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """
    Standardized task definition across all layers.
    """
    id: str
    type: str                          # e.g., "legal.research", "admin.draft"
    description: str
    input_data: Dict[str, Any]
    
    # Execution context
    agent_id: Optional[str] = None
    namespace: str = "default"
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Timeout & retry
    timeout_seconds: int = 300
    max_retries: int = 3
    
    # Metadata
    created_at: Optional[str] = None
    parent_task_id: Optional[str] = None  # For sub-tasks
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass  
class TaskResult:
    """
    Standardized result from any layer (tool, skill, agent).
    """
    task_id: str
    status: TaskStatus
    
    # Output
    output: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Metadata
    execution_time_ms: int = 0
    retries: int = 0
    
    # Provenance
    executed_by: str = ""           # tool/skill/agent name
    sub_tasks: List['TaskResult'] = None  # For hierarchical execution
    
    def __post_init__(self):
        if self.sub_tasks is None:
            self.sub_tasks = []
    
    @property
    def is_success(self) -> bool:
        return self.status == TaskStatus.COMPLETED and self.error is None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "error_code": self.error_code,
            "execution_time_ms": self.execution_time_ms,
            "executed_by": self.executed_by
        }
```

---

## 2. BaseTool (Execution Layer)

```python
# tools/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from core.task import TaskResult

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    Tools = executable actions that interact with external systems.
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    tags: List[str] = []  # For discovery
    
    @abstractmethod
    async def execute(self, **kwargs) -> TaskResult:
        """
        Execute the tool with given parameters.
        Must be implemented by concrete tool classes.
        """
        pass
    
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate parameters before execution.
        Return True if valid, False otherwise.
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
```

---

## 3. BaseSkill (Intelligence Layer)

```python
# skills/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from core.task import Task, TaskResult

class SkillContext:
    """Context passed to skill execution."""
    def __init__(
        self,
        task: Task,
        memory: Dict[str, Any],
        tools_available: List[str]
    ):
        self.task = task
        self.memory = memory
        self.tools_available = tools_available

class BaseSkill(ABC):
    """
    Abstract base class for all skills.
    Skills = cognitive capabilities that require decision-making.
    """
    name: str
    description: str
    tags: List[str] = []           # For discovery
    required_tools: List[str] = [] # Tools this skill needs
    dependencies: List[str] = []   # ⭐ Skills this skill depends on
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> TaskResult:
        """
        Execute skill with given context.
        Must be implemented by concrete skill classes.
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: Task) -> float:
        """
        Check if this skill can handle the given task.
        Return confidence score (0.0 - 1.0).
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """Return list of skill dependencies."""
        return self.dependencies
```

---

## 4. BaseKnowledge (RAG Layer)

```python
# knowledge/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from dataclasses import dataclass

@dataclass
class KnowledgeChunk:
    """Single chunk of knowledge."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float  # Relevance score

@dataclass
class KnowledgeVersion:
    """Version metadata for knowledge base."""
    version_id: str
    created_at: str
    document_count: int
    vector_count: int

class BaseKnowledge(ABC):
    """
    Abstract base class for knowledge bases.
    Knowledge = external facts retrievable via RAG.
    """
    domain: str
    namespace: str
    
    @abstractmethod
    async def ingest(self, sources: List[str]) -> Dict[str, Any]:
        """
        Ingest documents from sources.
        Returns ingestion statistics.
        """
        pass
    
    @abstractmethod
    async def query(
        self,
        query: str,
        top_k: int = 5
    ) -> List[KnowledgeChunk]:
        """
        Query knowledge base.
        Returns ranked list of knowledge chunks.
        """
        pass
    
    @abstractmethod
    async def create_version(self) -> KnowledgeVersion:
        """Create immutable snapshot of current KB."""
        pass
    
    @abstractmethod
    async def rollback(self, version_id: str) -> bool:
        """Rollback to specific version."""
        pass
```

---

## 5. BaseAgent (Agent Layer)

```python
# agents/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from core.task import Task, TaskResult

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Agents = domain-specific coordinators that combine skills & tools.
    """
    name: str
    description: str
    
    # Configuration
    talents: List[str] = []     # skill names
    tools: List[str] = []       # tool names
    knowledge: List[str] = []   # knowledge namespace names
    
    @abstractmethod
    async def run(self, task: Task) -> TaskResult:
        """
        Execute task using configured talents, tools, and knowledge.
        """
        pass
    
    @abstractmethod
    async def plan(self, task: Task) -> List[Task]:
        """
        Decompose task into sub-tasks.
        Returns execution plan.
        """
        pass
    
    def can_handle(self, task: Task) -> float:
        """
        Check if agent can handle task.
        Return confidence score (0.0 - 1.0).
        """
        # Default implementation: check task type prefix
        for talent in self.talents:
            if task.type.startswith(talent.split('.')[0]):
                return 0.8
        return 0.0
```

---

## 6. Registry Pattern

### 6.1 ToolRegistry

```python
# tools/registry.py
from typing import Dict, List, Type
from tools.base import BaseTool

class ToolRegistry:
    """Central registry for all tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> BaseTool:
        """Get tool by name."""
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' not found")
        return tool
    
    def list_all(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def list_by_tag(self, tag: str) -> List[BaseTool]:
        """Find tools by tag."""
        return [t for t in self._tools.values() if tag in t.tags]
    
    def discover(self, capability: str) -> List[BaseTool]:
        """Discover tools by capability keyword."""
        results = []
        for tool in self._tools.values():
            if capability.lower() in tool.description.lower():
                results.append(tool)
        return results

# Global instance
tool_registry = ToolRegistry()
```

### 6.2 SkillRegistry (with Circular Dependency Detection)

```python
# skills/registry.py
from typing import Dict, List, Set
from skills.base import BaseSkill

class CircularDependencyError(Exception):
    """Raised when circular dependency detected."""
    pass

class SkillRegistry:
    """
    Central registry for all skills.
    Includes circular dependency detection.
    """
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
    
    def register(self, skill: BaseSkill) -> None:
        """
        Register a skill with circular dependency check.
        """
        # Check for circular dependency before registration
        if self._detect_cycle(skill.name, skill.dependencies):
            raise CircularDependencyError(
                f"Circular dependency detected for skill: {skill.name}"
            )
        
        self._skills[skill.name] = skill
        self._dependency_graph[skill.name] = set(skill.dependencies)
    
    def get(self, name: str) -> BaseSkill:
        """Get skill by name."""
        skill = self._skills.get(name)
        if not skill:
            raise KeyError(f"Skill '{name}' not found")
        return skill
    
    def _detect_cycle(
        self,
        skill_name: str,
        dependencies: List[str]
    ) -> bool:
        """
        DFS-based cycle detection.
        Returns True if cycle detected.
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
        del self._dependency_graph[skill_name]  # Clean up simulation
        
        return has_cycle
    
    def get_execution_order(self, skill_name: str) -> List[str]:
        """
        Get topological sort of skill dependencies.
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

# Global instance
skill_registry = SkillRegistry()
```

---

## 7. Error Handling Contract

```python
# core/errors.py

class LayerError(Exception):
    """Base error for all layers."""
    def __init__(self, message: str, layer: str, error_code: str):
        super().__init__(message)
        self.layer = layer
        self.error_code = error_code

class ToolError(LayerError):
    """Error from tool execution."""
    def __init__(self, message: str, error_code: str = "TOOL_ERROR"):
        super().__init__(message, "tool", error_code)

class SkillError(LayerError):
    """Error from skill execution."""
    def __init__(self, message: str, error_code: str = "SKILL_ERROR"):
        super().__init__(message, "skill", error_code)

class KnowledgeError(LayerError):
    """Error from knowledge query."""
    def __init__(self, message: str, error_code: str = "KNOWLEDGE_ERROR"):
        super().__init__(message, "knowledge", error_code)

# Error propagation example:
# Tool fails → Skill catches → SkillError → Agent handles → User sees friendly message
```

---

## 8. Mission & Autonomy (The "Soul")

Extension untuk memberikan agen kemampuan otonom (proaktif, bukan hanya reaktif).

```python
# core/mission.py
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class MissionStatus(Enum):
    ACTIVE = "active"           # Agen memantau tujuan
    IN_PROGRESS = "in_progress" # Agen menjalankan tugas untuk misi
    SATISFIED = "satisfied"     # Tujuan tercapai
    CRITICAL = "critical"       # Deviasi besar, butuh tindakan
    ABORTED = "aborted"         # Misi dibatalkan

@dataclass
class Mission:
    """
    Mission = tujuan jangka panjang yang dikejar agen secara otonom.
    Berbeda dengan Task yang reaktif (menunggu perintah).
    """
    id: str
    agent_id: str
    objective: str              # Deskripsi tujuan
    success_criteria: str       # Definisi teknis keberhasilan
    priority: int = 5           # 1-10 (10 tertinggi)
    status: MissionStatus = MissionStatus.ACTIVE
    
    # State & History
    current_gap: Optional[str] = None
    last_evaluated: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Autonomy Loop

```
┌─────────────────────────────────────────┐
│         MISSION MANAGER                 │
│           (The Soul)                    │
├─────────────────────────────────────────┤
│ 1. SENSE                                │
│    Query Knowledge untuk evidence       │
│         ↓                               │
│ 2. CONTEMPLATE                          │
│    Evaluate: Ada gap?                   │
│         ↓                               │
│ 3. ACT (jika ada gap)                   │
│    Create proactive tasks               │
│         ↓                               │
│    Submit ke Orchestrator               │
└─────────────────────────────────────────┘
```

---

## 9. Cross-References

- Lihat `02-architecture-overview.md` untuk struktur direktori
- Lihat `04-knowledge-layer.md` untuk RAG stores detail
- Lihat `05-skills-layer.md` untuk skill composition patterns
- Lihat `11-mission-manager.md` untuk detail otonomi agen

---

**Prev:** [02-architecture-overview.md](02-architecture-overview.md)  
**Next:** [04-knowledge-layer.md](04-knowledge-layer.md)
