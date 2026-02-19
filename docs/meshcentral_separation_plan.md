# MeshCentral Separation Plan

**Date:** 2026-02-19  
**Status:** 🔴 CRITICAL - Separation Required  
**Priority:** HIGH  
**Owner:** TBD

---

## Executive Summary

MeshCentral is a full-featured remote device management platform bundled within the MCP Unified Agent repository. This creates significant scope creep, increases attack surface, and blurs system boundaries. This document outlines the technical rationale for separation and provides a step-by-step migration plan.

---

## What is MeshCentral?

MeshCentral is an open-source remote management platform that provides:
- Remote desktop access (RDP/VNC alternative)
- File transfer capabilities
- Terminal access to managed devices
- Device monitoring and management
- User/group management
- Full web-based management interface

**Current Version:** 1.1.56  
**Location:** `mcp-unified/simulation/meshcentral_server/`

---

## Why Separation is Necessary

### 1. Scope Creep

| Aspect | MCP Server Scope | MeshCentral Scope |
|--------|-----------------|-------------------|
| Primary Function | AI agent context/memory | Remote device management |
| Protocol | Model Context Protocol | Custom Web/Agent protocol |
| Dependencies | Python, PostgreSQL | Node.js, MongoDB/NeDB |
| Target Users | AI agents, developers | IT administrators |

**Problem:** Remote device management is entirely outside the scope of an MCP (Model Context Protocol) server.

### 2. Attack Surface Expansion

**MeshCentral introduces:**
- Additional network ports (80, 443, 4433 by default)
- Web interface with authentication
- Agent software that runs on managed devices
- Certificate management infrastructure
- File transfer capabilities

**Risk:** Each of these is a potential attack vector that doesn't serve the MCP server's core purpose.

### 3. Certificate Management Issues

The `meshcentral-data/` directory contains:
- SSL/TLS certificates
- Private keys (`*-private.key`)
- Signed agent binaries
- Database files with sensitive data

**Risk:** These are high-value targets for attackers and complicate the MCP server's security posture.

### 4. Dependency Complexity

**Current MCP Dependencies:**
- Python 3.9+
- PostgreSQL with pgvector
- Redis (optional)

**MeshCentral Additional Dependencies:**
- Node.js runtime
- MongoDB or NeDB
- Separate update/upgrade lifecycle

**Problem:** MeshCentral's Node.js dependency creates a completely separate runtime environment within the Python-based MCP server.

### 5. Operational Confusion

New developers/operators may:
- Assume MeshCentral is required for MCP functionality
- Misconfigure security settings due to complexity
- Have difficulty debugging (which system is causing issues?)
- Make incorrect assumptions about the system boundary

---

## Current Integration Analysis

### Dependency Check

Let's determine if MCP actually depends on MeshCentral:

```bash
# Search for MeshCentral references in MCP code
grep -r "meshcentral" --include="*.py" mcp-unified/
grep -r "meshcentral" --include="*.sh" .
grep -r "meshcentral" --include="*.json" .
```

**Expected Result:** No direct code dependencies found.

### Indirect Dependencies

Potential indirect dependencies to check:
- [ ] Does any MCP documentation reference MeshCentral?
- [ ] Are there shared configuration files?
- [ ] Does any automation/script use MeshCentral?
- [ ] Is MeshCentral used for remote debugging of MCP?

**Initial Assessment:** No critical dependencies identified.

---

## Separation Strategy

### Recommended Approach: **Full Separation**

Move MeshCentral to a completely separate repository and infrastructure.

**Rationale:**
- No code-level dependencies exist
- Different technology stacks (Python vs Node.js)
- Different operational requirements
- Different security boundaries
- Different update lifecycles

### Alternative: **Documentation Only**

If there are undocumented dependencies:
- Keep MeshCentral in place temporarily
- Create comprehensive dependency mapping
- Gradual migration with compatibility layer
- **Not recommended** - only if full separation is blocked

---

## Migration Steps

### Phase 1: Preparation (Day 1-2)

#### 1.1 Create New Repository

```bash
# Create new repository for MeshCentral
git init mcp-meshcentral-remote-mgmt
cd mcp-meshcentral-remote-mgmt

# Create basic structure
mkdir -p config/
mkdir -p docs/
mkdir -p backups/
```

#### 1.2 Copy Configuration

```bash
# Copy current MeshCentral configuration
cp -r /home/aseps/MCP/mcp-unified/simulation/meshcentral_server/meshcentral-data/ ./config/
cp /home/aseps/MCP/mcp-unified/simulation/meshcentral_server/package.json ./
```

#### 1.3 Create Documentation

```bash
# Create comprehensive README
cat > README.md << 'EOF'
# MCP MeshCentral Remote Management

This repository contains the MeshCentral remote device management 
installation that was previously bundled with MCP Unified Agent.

## ⚠️ IMPORTANT

This is **NOT** required for MCP server functionality.
This is a separate system for IT device management only.

## Quick Start

```bash
npm install
node node_modules/meshcentral
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Security Configuration](docs/security.md)
- [MCP Integration Notes](docs/mcp-notes.md)
EOF
```

### Phase 2: Migration (Day 3-4)

#### 2.1 Move Data

```bash
# Backup current MeshCentral data
tar -czf meshcentral-backup-$(date +%Y%m%d).tar.gz \
  /home/aseps/MCP/mcp-unified/simulation/meshcentral_server/

# Copy to new location
cp -r /home/aseps/MCP/mcp-unified/simulation/meshcentral_server/* \
  /path/to/new/mcp-meshcentral-remote-mgmt/
```

#### 2.2 Update Network Configuration

If MeshCentral was accessed via:
- `https://mcp-server/meshcentral/` → Update to new URL
- `https://meshcentral.example.com/` → Already separate, just move

### Phase 3: Cleanup (Day 5-7)

#### 3.1 Remove from Original Repository

```bash
cd /home/aseps/MCP

# Add to .gitignore (already done in TASK-001-A)
echo "simulation/meshcentral_server/" >> .gitignore

# Remove from repository
git rm -r mcp-unified/simulation/meshcentral_server/

# Commit changes
git commit -m "Remove MeshCentral - moved to separate repository

MeshCentral remote device management has been separated from the
MCP Unified Agent repository. It is now maintained at:
[NEW_REPOSITORY_URL]

This separation:
- Reduces attack surface
- Clarifies system boundaries  
- Eliminates scope creep
- Simplifies deployment"
```

#### 3.2 Clean Git History (Optional but Recommended)

```bash
# Remove from git history to reduce repo size
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch -r mcp-unified/simulation/meshcentral_server/' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team)
git push origin --force --all
```

### Phase 4: Validation (Day 8-10)

#### 4.1 Verify MCP Functionality

```bash
cd /home/aseps/MCP/mcp-unified

# Test without MeshCentral
python3 -c "from core.config import settings; print('Config OK')"
python3 tests/test_capabilities.py

# Verify no import errors
grep -r "meshcentral" --include="*.py" .
# Should return no results
```

#### 4.2 Verify MeshCentral Independence

```bash
cd /path/to/mcp-meshcentral-remote-mgmt

# Start MeshCentral
npm install
node node_modules/meshcentral

# Verify it works independently
curl http://localhost:443/
```

---

## Impact Assessment

### Impact on MCP System

| Component | Impact | Mitigation |
|-----------|--------|------------|
| Core Server | None | N/A |
| Memory System | None | N/A |
| Shell Tools | None | N/A |
| Documentation | Minor | Update references |
| Build Scripts | None | N/A |

### Impact on Operations

| Activity | Impact | Action Required |
|----------|--------|-----------------|
| Deployment | Positive | Simpler deployment |
| Monitoring | Neutral | Separate monitoring for MeshCentral |
| Backups | Neutral | Separate backup strategy needed |
| Security | Positive | Reduced attack surface |

---

## Timeline

| Phase | Duration | Owner | Deliverable |
|-------|----------|-------|-------------|
| Preparation | 2 days | TBD | New repository ready |
| Migration | 2 days | TBD | Data migrated |
| Cleanup | 3 days | TBD | Original repo cleaned |
| Validation | 3 days | TBD | Both systems verified |
| **Total** | **10 days** | | |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Undiscovered dependencies | Medium | High | Thorough testing before cleanup |
| Data loss during migration | Low | High | Multiple backups |
| Network connectivity issues | Medium | Medium | Update DNS/firewall rules |
| User confusion | Medium | Low | Clear documentation |

---

## Rollback Plan

If critical issues are discovered:

1. **Immediate:** Stop migration, restore from backup
2. **Within 24 hours:** Restore MeshCentral to original location
3. **Within 48 hours:** Document blocking issues
4. **Replan:** Address issues and retry

```bash
# Emergency rollback
cd /home/aseps/MCP

# Restore from backup
tar -xzf meshcentral-backup-YYYYMMDD.tar.gz \
  -C mcp-unified/simulation/

# Commit restoration
git add mcp-unified/simulation/meshcentral_server/
git commit -m "Emergency rollback: Restore MeshCentral"
```

---

## Post-Separation Maintenance

### MCP Repository
- No MeshCentral-related maintenance
- Reduced security scanning surface
- Smaller repository size

### New MeshCentral Repository
- Independent update cycle
- Separate security monitoring
- Dedicated documentation

---

## Recommendations

### Immediate Actions
1. ✅ Create separation plan (this document)
2. ⬜ Identify and assign owner
3. ⬜ Verify no hidden dependencies
4. ⬜ Begin Phase 1 (Preparation)

### Short-term (1 week)
1. ⬜ Complete migration
2. ⬜ Update all documentation
3. ⬜ Train team on new structure

### Long-term (1 month)
1. ⬜ Implement separate monitoring
2. ⬜ Establish backup procedures
3. ⬜ Regular security reviews

---

## Appendix

### A. MeshCentral Data Directory Contents

```
meshcentral-data/
├── agentserver-cert-private.key      # Agent server private key
├── agentserver-cert-public.crt       # Agent server certificate
├── codesign-cert-private.key         # Code signing private key
├── codesign-cert-public.crt          # Code signing certificate
├── mpsserver-cert-private.key        # MPS server private key
├── mpsserver-cert-public.crt         # MPS server certificate
├── root-cert-private.key             # Root CA private key
├── root-cert-public.crt              # Root CA certificate
├── webserver-cert-private.key        # Web server private key
├── webserver-cert-public.crt         # Web server certificate
├── meshcentral.db                    # Main database
├── meshcentral-events.db             # Events database
├── meshcentral-power.db              # Power events database
├── meshcentral-stats.db              # Statistics database
├── serverstate.txt                   # Server state
└── signedagents/                     # Signed agent binaries
    ├── MeshCmd*.exe
    └── MeshService*.exe
```

**All of these are sensitive and require secure handling.**

### B. References

- [MeshCentral Official Documentation](https://ylianst.github.io/MeshCentral/)
- [MeshCentral GitHub](https://github.com/Ylianst/MeshCentral)
- [MCP Security Notice](../SECURITY_NOTICE.md)
- [Greyware Isolation Plan](../mcp-unified/simulation/greyware_op/ISOLATION_REQUIRED.md)

---

**Document Owner:** TBD  
**Last Updated:** 2026-02-19  
**Next Review:** Upon migration completion
