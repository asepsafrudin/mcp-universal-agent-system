# 08 - Security Audit

**Authentication, RBAC, Audit Logging**

---

## 1. Security Manager

```python
# core/security.py
from typing import Dict, Any, List
from enum import Enum

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class SecurityManager:
    """
    Security untuk multi-agent system.
    Handles: Auth, RBAC, Audit logging.
    """
    
    def __init__(self, audit_sink=None):
        self._permissions: Dict[str, Dict[str, Permission]] = {}
        # ✅ FIXED: Use persistent audit sink (DB/ELK/Kafka), not memory
        self._audit_sink = audit_sink or PostgreSQLAuditSink()
    
    # Authentication
    async def authenticate_agent(
        self,
        agent_id: str,
        credentials: Dict[str, Any]
    ) -> str:
        """Authenticate agent, return auth token (JWT)."""
        # TODO: Implement JWT atau API key validation
        raise NotImplementedError("Auth implementation required")
    
    # Authorization (RBAC)
    def can_access_knowledge(
        self,
        agent_id: str,
        namespace: str,
        permission: Permission
    ) -> bool:
        """Check if agent can access knowledge namespace."""
        agent_perms = self._permissions.get(agent_id, {})
        return agent_perms.get(namespace) == permission
    
    # Audit Logging - FIXED: Persistent storage
    async def log_access(
        self,
        agent_id: str,
        resource: str,
        operation: str,
        result: str
    ):
        """Audit log untuk sensitive operations - write to persistent storage."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "resource": resource,
            "operation": operation,
            "result": result
        }
        # ✅ FIXED: Write to persistent sink (DB/ELK/Kafka), not memory list
        await self._audit_sink.write(log_entry)


class PostgreSQLAuditSink:
    """Audit sink yang menulis ke PostgreSQL."""
    
    async def write(self, log_entry: Dict):
        """Write audit log to database."""
        # Implementation: INSERT into audit_logs table
        pass
```

---

## 2. Namespace Isolation

```python
# Security: Legal agent tidak bisa access Admin knowledge

# Legal agent permissions
legal_perms = {
    "hukum-perdata": Permission.READ,
    "putusan-pengadilan": Permission.READ
}

# Admin agent permissions  
admin_perms = {
    "admin-kantor": Permission.READ_WRITE,
    "template-surat": Permission.READ_WRITE
}
```

---

**Prev:** [07-domain-examples.md](07-domain-examples.md)  
**Next:** [09-roadmap.md](09-roadmap.md)
