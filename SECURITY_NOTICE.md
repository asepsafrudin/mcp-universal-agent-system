# 🔒 Security Notice — MCP Unified Agent System

**Document Version:** 1.0  
**Date:** 2026-02-19  
**Status:** 🔴 ACTION REQUIRED

---

## Overview

This document provides an overview of known security risks in the MCP Unified Agent System and the current status of mitigation efforts.

---

## Risk Summary

| Risk Area | Severity | Status | Reference |
|-----------|----------|--------|-----------|
| Greyware Simulation Tools | 🔴 CRITICAL | Mitigated | [ISOLATION_REQUIRED.md](mcp-unified/simulation/greyware_op/ISOLATION_REQUIRED.md) |
| MeshCentral Server Bundle | 🟡 HIGH | Separation Planned | [docs/meshcentral_separation_plan.md](docs/meshcentral_separation_plan.md) |
| Hardcoded Credentials | 🔴 CRITICAL | ✅ RESOLVED | See below |
| Shell Command Whitelist | 🔴 CRITICAL | ✅ RESOLVED | See below |
| Memory Namespace Isolation | 🟡 HIGH | ✅ RESOLVED | See below |

---

## Greyware Simulation Tools — CRITICAL

### Risk Description
The folder `mcp-unified/simulation/greyware_op/` contains tools that can be classified as greyware or potentially malicious:

- **c2_bot.js** — Command & Control bot implementation
- **duckyscript.txt** — USB keystroke injection payloads
- **ai_nmap.py** — AI-powered network scanner
- **PowerShell deployment scripts** — Various remote execution tools

### Why This Is Dangerous
1. **Reputational Damage** — Code scanners and security tools will flag this repository
2. **Legal Liability** — Possession of C2 tools may violate laws in some jurisdictions
3. **Accidental Execution** — Risk of running dangerous code in production
4. **Supply Chain Risk** — Attackers could tamper with these files

### Current Status
- [x] Isolation notice created
- [x] .gitignore updated
- [ ] Repository separation completed
- [ ] Git history cleaned

### Required Actions
1. **Immediate:** Review [ISOLATION_REQUIRED.md](mcp-unified/simulation/greyware_op/ISOLATION_REQUIRED.md)
2. **Within 24 hours:** Move to separate private repository
3. **Within 48 hours:** Clean git history

---

## MeshCentral Server Bundle — HIGH

### Risk Description
`simulation/meshcentral_server/` contains a full MeshCentral remote device management platform bundled within the MCP server.

### Why This Is Concerning
- **Scope Creep** — Remote management is outside MCP server scope
- **Attack Surface** — Additional services increase vulnerability exposure
- **Certificate Management** — Contains SSL certificates and private keys
- **Confusion** — Blurs system boundaries

### Current Status
- [x] Separation plan created
- [ ] New repository prepared
- [ ] Data migrated
- [ ] Original location cleaned

See [docs/meshcentral_separation_plan.md](docs/meshcentral_separation_plan.md) for detailed separation plan.

### Required Actions
1. ✅ Create separation plan
2. ⬜ Assign migration owner
3. ⬜ Verify no hidden dependencies
4. ⬜ Execute migration (10-day timeline)
5. ⬜ Implement proper certificate rotation

---

## Hardcoded Credentials — RESOLVED ✅

### Issue
Passwords were hardcoded in several places:
- `mcp-unified/core/config.py`
- `README.md`
- `setup_distributed.sh` (RabbitMQ credentials)

### Resolution
- [x] All credentials moved to environment variables.
- [x] `.env.example` created and updated with placeholder values for all services.
- [x] `.gitignore` updated to exclude `.env` files.
- [x] Security comments added to `config.py`.
- [x] Scripts now validate for the presence of environment variables before running.

### Required Actions
1. Rotate the actual password if it was ever used in production
2. Audit for any other hardcoded secrets
3. Train team on secure credential management

---

## Shell Command Whitelist — RESOLVED ✅

### Issue
Original `run_shell` tool allowed ambiguous commands with potential for injection attacks.

### Resolution
- [x] Explicit `ALLOWED_COMMANDS` whitelist implemented
- [x] Input sanitization for dangerous characters (`;`, `&&`, `||`, `|`, `>`, `>>`, `` ` ``, `$()`)
- [x] Comprehensive logging of all shell command attempts

### Security Measures Implemented
```python
# Explicit whitelist — jangan tambahkan command tanpa review security
ALLOWED_COMMANDS = frozenset([...])

# Input sanitization
DANGEROUS_PATTERNS = [';', '&&', '||', '|', '>', '>>', '`', '$(']
```

---

## Memory Namespace Isolation — RESOLVED ✅

### Issue
Long-term memory system lacked namespace isolation, allowing cross-project memory contamination.

### Resolution
- [x] Added `namespace` field to memory schema
- [x] All memory operations support namespace parameter
- [x] Default namespace set to `"default"`
- [x] Search operations filtered by namespace

### Usage
```python
# Save to specific namespace
await memory_save(key="config", content="...", namespace="project_a")

# Search within namespace only
await memory_search(query="api", namespace="project_a")
```

---

## Recommendations

### Immediate (24-48 hours)
1. ⚠️ Complete greyware simulation tools isolation
2. ⚠️ Rotate any credentials that may have been exposed
3. ⚠️ Review access logs for unauthorized activity

### Short-term (1 week)
1. Implement automated secret scanning (GitGuardian, TruffleHog)
2. Set up dependency vulnerability scanning
3. Create security incident response plan

### Long-term (1 month)
1. Conduct full security audit
2. Implement code signing for releases
3. Establish security champions program
4. Regular penetration testing

---

## Security Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| Security Lead | [TBD] | Overall security posture |
| Incident Response | [TBD] | Security incident handling |
| Code Review | [TBD] | Security-focused code reviews |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-19 | Initial security notice |

---

**⚠️ If you discover a security vulnerability, please report it immediately. Do not open public issues for security concerns.**
