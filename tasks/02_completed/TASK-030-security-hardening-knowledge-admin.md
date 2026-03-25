# TASK-030: Security Hardening - Knowledge Admin

**Status:** ACTIVE  
**Priority:** 🔴 CRITICAL  
**Created:** 2026-03-03  
**Assignee:** TBD  
**Due:** 2026-03-08 (5 days)  
**Labels:** `security`, `critical`, `knowledge-admin`, `hardening`

---

## 🎯 Objective

Mengamankan Knowledge Admin System dengan menghilangkan hardcoded credentials, mengimplementasikan RBAC, dan memastikan production-ready security.

---

## 🚨 Problem Statement

Ditemukan critical security issues saat inspeksi:
1. **Hardcoded passwords** di `auth.py` (admin123, reviewer123, viewer123)
2. **RBAC bypass** di `namespace_manager.py` (semua agent bisa akses semua namespace)
3. **Mock ingestion** di `document_processor.py` (dokumen tidak benar-benar di-ingest)

---

## 📋 Requirements

### R1: Password Security
- [ ] Hash semua password dengan bcrypt/argon2
- [ ] Load credentials dari environment variables
- [ ] Implementasi password strength validation
- [ ] Force password change on first login

### R2: RBAC Implementation
- [ ] Definisikan role hierarchy (admin > reviewer > viewer)
- [ ] Implementasi permission matrix
- [ ] Namespace-level access control
- [ ] Audit logging untuk access attempts

### R3: Knowledge Ingestion
- [ ] Integrasi actual RAGEngine.ingest()
- [ ] Validasi chunk quality
- [ ] Error handling untuk failed ingestion
- [ ] Retry mechanism

### R4: Security Audit
- [ ] Scan hardcoded secrets di seluruh codebase
- [ ] Implementasi security headers
- [ ] Rate limiting untuk login attempts
- [ ] Session timeout management

---

## 🏗️ Implementation Plan

### Phase 1: Password Hardening (Day 1-2)

**File:** `mcp-unified/knowledge/admin/auth.py`

```python
# BEFORE (INSECURE)
DEFAULT_PASSWORDS = {
    "admin": "admin123",
    "reviewer": "reviewer123", 
    "viewer": "viewer123"
}

# AFTER (SECURE)
import bcrypt
import os
from typing import Optional

class SecureAuthManager:
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._tokens: Dict[str, AuthToken] = {}
        self._load_users_from_env()
    
    def _load_users_from_env(self):
        """Load users dari environment variables."""
        # Format: MCP_ADMIN_USER=admin
        #         MCP_ADMIN_PASS_HASH=<bcrypt_hash>
        for role in ["admin", "reviewer", "viewer"]:
            username = os.getenv(f"MCP_{role.upper()}_USER", role)
            pass_hash = os.getenv(f"MCP_{role.upper()}_PASS_HASH")
            
            if not pass_hash:
                # Generate hash jika belum ada
                temp_pass = self._generate_temp_password()
                pass_hash = bcrypt.hashpw(temp_pass.encode(), bcrypt.gensalt())
                logger.warning(f"No password hash for {role}, generated temp: {temp_pass}")
            
            self._users[username] = User(
                id=f"{role}_001",
                username=username,
                email=f"{username}@mcp.local",
                role=role,
                password_hash=pass_hash,
                created_at=datetime.now().isoformat(),
                must_change_password=True  # Force change on first login
            )
    
    def authenticate(self, username: str, password: str) -> Optional[AuthToken]:
        """Secure authentication dengan bcrypt."""
        user = self._users.get(username)
        if not user:
            # Timing attack protection: tetap hash walaupun user tidak ada
            bcrypt.checkpw(password.encode(), bcrypt.gensalt())
            return None
        
        if not bcrypt.checkpw(password.encode(), user.password_hash):
            return None
        
        if user.must_change_password:
            return AuthToken(
                token="FORCE_PASSWORD_CHANGE",
                user_id=user.id,
                role=user.role,
                must_change_password=True
            )
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        # ... rest of logic
```

**Tasks:**
- [ ] Install bcrypt dependency
- [ ] Refactor AuthManager dengan password hashing
- [ ] Create environment variable loader
- [ ] Implementasi password strength checker
- [ ] Add force password change mechanism
- [ ] Update login UI untuk password change flow

---

### Phase 2: RBAC Implementation (Day 2-3)

**File:** `mcp-unified/knowledge/sharing/namespace_manager.py`

```python
# BEFORE (INSECURE)
def _can_access(self, namespace: str, agent_id: Optional[str]) -> bool:
    # TODO: Implement role-based access control
    return True  # BYPASS SECURITY

# AFTER (SECURE)
class RBACManager:
    """Role-Based Access Control untuk namespaces."""
    
    # Permission matrix
    PERMISSIONS = {
        "admin": {
            "shared_legal": ["read", "write", "delete", "admin"],
            "shared_admin": ["read", "write", "delete", "admin"],
            "shared_tech": ["read", "write", "delete", "admin"],
            "shared_general": ["read", "write", "delete", "admin"],
        },
        "reviewer": {
            "shared_legal": ["read", "write"],
            "shared_admin": ["read", "write"],
            "shared_tech": ["read"],
            "shared_general": ["read", "write"],
        },
        "viewer": {
            "shared_legal": ["read"],
            "shared_admin": ["read"],
            "shared_tech": ["read"],
            "shared_general": ["read"],
        }
    }
    
    def can_access(self, namespace: str, role: str, permission: str = "read") -> bool:
        """Check jika role punya permission untuk namespace."""
        role_perms = self.PERMISSIONS.get(role, {})
        ns_perms = role_perms.get(namespace, [])
        return permission in ns_perms
    
    def can_create_namespace(self, role: str) -> bool:
        """Hanya admin yang bisa create namespace."""
        return role == "admin"
    
    def can_delete_document(self, namespace: str, role: str) -> bool:
        """Check delete permission."""
        return self.can_access(namespace, role, "delete")


class SecureNamespaceManager(NamespaceManager):
    """Namespace manager dengan RBAC."""
    
    def __init__(self, knowledge_engine=None, auth_manager=None):
        super().__init__(knowledge_engine)
        self.auth = auth_manager
        self.rbac = RBACManager()
        self.audit_log = []
    
    async def list_namespaces(self, token: str) -> List[Dict[str, Any]]:
        """List namespaces dengan RBAC check."""
        auth = self.auth.verify_token(token) if self.auth else None
        if not auth:
            self._audit("list_namespaces", None, "DENIED", "Invalid token")
            raise PermissionError("Invalid or expired token")
        
        all_namespaces = await super().list_namespaces()
        
        # Filter berdasarkan role
        accessible = []
        for ns in all_namespaces:
            if self.rbac.can_access(ns["name"], auth.role, "read"):
                accessible.append(ns)
        
        self._audit("list_namespaces", auth.user_id, "ALLOWED", f"{len(accessible)} namespaces")
        return accessible
    
    async def create_namespace(
        self, 
        name: str, 
        description: str, 
        token: str,
        access: str = "restricted",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create namespace dengan RBAC check."""
        auth = self.auth.verify_token(token) if self.auth else None
        if not auth:
            raise PermissionError("Invalid token")
        
        if not self.rbac.can_create_namespace(auth.role):
            self._audit("create_namespace", auth.user_id, "DENIED", f"Role {auth.role} cannot create")
            raise PermissionError(f"Role {auth.role} cannot create namespaces")
        
        result = super().create_namespace(name, description, access, tags, auth.user_id)
        self._audit("create_namespace", auth.user_id, "ALLOWED", name)
        return result
    
    def _audit(self, action: str, user_id: str, result: str, details: str):
        """Log audit trail."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user_id": user_id,
            "result": result,
            "details": details
        })
```

**Tasks:**
- [ ] Definisikan permission matrix
- [ ] Implementasi RBACManager
- [ ] Refactor NamespaceManager dengan RBAC
- [ ] Add audit logging
- [ ] Update API endpoints dengan RBAC checks
- [ ] Create audit log viewer (admin only)

---

### Phase 3: Actual Knowledge Ingestion (Day 3-4)

**File:** `mcp-unified/knowledge/ingestion/document_processor.py`

```python
# BEFORE (MOCK)
async def _ingest_to_knowledge_base(...):
    # TODO: Implementasi actual ingest menggunakan knowledge.rag_engine
    # For now, return mock result
    return {
        'success': True,
        'namespace': namespace,
        'chunks_ingested': len(chunks)  # MOCK
    }

# AFTER (ACTUAL)
async def _ingest_to_knowledge_base(
    self,
    chunks: List[Dict],
    namespace: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Ingest chunks ke knowledge base menggunakan RAGEngine.
    """
    if not self.knowledge:
        raise RuntimeError("Knowledge engine not available")
    
    ingested_count = 0
    failed_chunks = []
    
    for chunk in chunks:
        try:
            # Generate embedding
            embedding = await self.knowledge.generate_embedding(chunk['text'])
            
            # Store in vector database
            result = await self.knowledge.store_vector(
                vector=embedding,
                text=chunk['text'],
                metadata={
                    **chunk.get('metadata', {}),
                    **metadata,
                    'chunk_id': chunk.get('id'),
                    'ingested_at': datetime.now().isoformat()
                },
                namespace=namespace
            )
            
            if result.get('success'):
                ingested_count += 1
            else:
                failed_chunks.append({
                    'chunk_id': chunk.get('id'),
                    'error': result.get('error', 'Unknown error')
                })
                
        except Exception as e:
            logger.error(f"Failed to ingest chunk {chunk.get('id')}: {e}")
            failed_chunks.append({
                'chunk_id': chunk.get('id'),
                'error': str(e)
            })
    
    # Update namespace document count
    if hasattr(self, 'namespace_manager'):
        self.namespace_manager.update_document_count(namespace, ingested_count)
    
    success_rate = ingested_count / len(chunks) if chunks else 0
    
    return {
        'success': success_rate >= 0.95,  # 95% success threshold
        'namespace': namespace,
        'chunks_total': len(chunks),
        'chunks_ingested': ingested_count,
        'chunks_failed': len(failed_chunks),
        'success_rate': success_rate,
        'failed_chunks': failed_chunks[:10]  # Limit error details
    }
```

**Tasks:**
- [ ] Integrasi dengan RAGEngine.generate_embedding()
- [ ] Implementasi knowledge.store_vector()
- [ ] Add chunk validation sebelum ingest
- [ ] Implementasi retry mechanism dengan exponential backoff
- [ ] Update namespace document count
- [ ] Add success rate threshold (95%)

---

### Phase 4: Security Audit & Hardening (Day 4-5)

**Tasks:**
- [ ] Scan seluruh codebase untuk hardcoded secrets
- [ ] Implementasi security headers (CSP, HSTS, X-Frame-Options)
- [ ] Rate limiting untuk login (5 attempts per minute)
- [ ] Session timeout (24 hours)
- [ ] Secure cookie flags (HttpOnly, Secure, SameSite)
- [ ] Remove password dari error messages
- [ ] Add security.txt

---

## 📁 File Changes

### Modified Files
1. `mcp-unified/knowledge/admin/auth.py` - Password hashing
2. `mcp-unified/knowledge/admin/app.py` - Security headers & password change flow
3. `mcp-unified/knowledge/sharing/namespace_manager.py` - RBAC
4. `mcp-unified/knowledge/ingestion/document_processor.py` - Actual ingestion

### New Files
1. `mcp-unified/knowledge/admin/rbac.py` - RBAC manager
2. `mcp-unified/knowledge/admin/audit.py` - Audit logging
3. `mcp-unified/knowledge/admin/password_utils.py` - Password validation
4. `scripts/security_scan.py` - Hardcoded secrets scanner

---

## 🧪 Testing Plan

### Unit Tests
```python
# tests/knowledge/admin/test_auth.py
def test_password_hashing():
    """Test password hashing dengan bcrypt."""
    pass

def test_rbac_permissions():
    """Test RBAC permission matrix."""
    pass

def test_namespace_access_control():
    """Test namespace access dengan berbagai roles."""
    pass
```

### Security Tests
```bash
# Test brute force protection
for i in {1..10}; do
    curl -X POST http://localhost:8080/login -d "username=admin&password=wrong"
done
# Should be rate limited after 5 attempts

# Test RBAC
curl -H "Authorization: Bearer <viewer_token>" \
     -X POST http://localhost:8080/api/namespace \
     -d '{"name": "test"}'
# Should return 403 Forbidden
```

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Password Hashing | 100% | All passwords hashed dengan bcrypt |
| RBAC Enforcement | 100% | No bypass dalam access control |
| Ingestion Success Rate | >95% | Failed chunks < 5% |
| Audit Coverage | 100% | All access attempts logged |
| Security Scan | 0 issues | No hardcoded secrets found |

---

## 🚨 Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing login | High | Gradual migration, backward compatibility |
| Performance degradation | Medium | Connection pooling, async operations |
| False positives RBAC | Medium | Comprehensive testing, audit logs |

---

## ✅ Definition of Done

- [ ] All phases completed
- [ ] All tests passing
- [ ] Security scan clean (0 hardcoded secrets)
- [ ] RBAC fully enforced
- [ ] Password hashing active
- [ ] Audit logging operational
- [ ] Documentation updated
- [ ] Code reviewed

---

**Last Updated:** 2026-03-03  
**Next Review:** 2026-03-08

---

*Created from Inspection Report: INSPECTION_PLACEHOLDER_REPORT.md*
