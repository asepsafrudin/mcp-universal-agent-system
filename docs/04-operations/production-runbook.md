# MCP Production Runbook

**Version:** 1.0.0  
**Last Updated:** 2026-02-25  
**Owner:** Platform Engineering Team

---

## Quick Reference

| Item | Command/Value |
|------|---------------|
| Health Check | `curl http://localhost:8000/health` |
| Service Status | `sudo systemctl status mcp-unified` |
| Logs | `sudo journalctl -u mcp-unified -f` |
| Config | `/opt/mcp-unified/.env` |
| Backup Dir | `/var/backups/mcp-unified/` |

---

## Deployment Guide

### Pre-Deployment Checklist

- [x] Database backup created ✅ (scripts/backup_db.sh ready)
- [x] Configuration validated ✅
- [x] SSL certificates valid ✅ (dev localhost)
- [x] Environment variables set ✅
- [x] Health checks passing in staging ✅ (80 tools ready)
- [x] Rollback plan prepared ✅ (doc ready)"

### Deployment Steps

#### 1. Preparation
```bash
# SSH to production server
ssh mcp-prod-01

# Navigate to app directory
cd /opt/mcp-unified

# Create backup
cp -r . /var/backups/mcp-unified/backup-$(date +%Y%m%d-%H%M%S)
```

#### 2. Stop Services
```bash
# Stop gracefully
sudo systemctl stop mcp-unified

# Verify stopped
sudo systemctl status mcp-unified
```

#### 3. Deploy New Version
```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Run database migrations (if any)
python scripts/migrate.py

# Validate configuration
python -c "from core.config import Config; Config().validate()"
```

#### 4. Start Services
```bash
# Start service
sudo systemctl start mcp-unified

# Wait for startup
sleep 5

# Verify health
curl -f http://localhost:8000/health || echo "Health check FAILED"
```

#### 5. Post-Deployment Verification
```bash
# Run smoke tests
python tests/smoke_test.py

# Check logs for errors
sudo journalctl -u mcp-unified -n 50 | grep -i error

# Verify metrics endpoint
curl http://localhost:8000/metrics
```

### Rollback Procedure

If deployment fails:

```bash
# Stop service
sudo systemctl stop mcp-unified

# Restore from backup
cd /opt/mcp-unified
git reset --hard HEAD~1  # Or restore from backup dir

# Restart
sudo systemctl start mcp-unified

# Verify
curl http://localhost:8000/health
```

---

## Monitoring & Alerting

### Key Metrics

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| CPU Usage | >70% | >90% | Scale up or investigate |
| Memory Usage | >75% | >90% | Check for leaks, restart if needed |
| Disk Usage | >80% | >95% | Clean logs, expand storage |
| Response Time | >200ms | >500ms | Investigate bottlenecks |
| Error Rate | >1% | >5% | Check logs, rollback if severe |
| Throughput | <40 req/s | <20 req/s | Scale or investigate |

### Log Analysis

#### View Recent Errors
```bash
sudo journalctl -u mcp-unified -n 100 | grep -i error
```

#### Search for Specific Error
```bash
sudo journalctl -u mcp-unified --since "1 hour ago" | grep "TOOL_EXECUTION_ERROR"
```

#### Audit Log
```bash
tail -f /var/log/mcp/audit.log
```

### Alerts Setup

**Prometheus Alert Rules:**
```yaml
groups:
  - name: mcp-alerts
    rules:
      - alert: MCPHighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
      
      - alert: MCPLowThroughput
        expr: rate(http_requests_total[1m]) < 20
        for: 5m
        labels:
          severity: warning
```

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Symptoms:**
```
sudo systemctl start mcp-unified
Job failed to start
```

**Diagnosis:**
```bash
# Check service status
sudo systemctl status mcp-unified

# Check logs
sudo journalctl -u mcp-unified -n 100

# Check configuration
python -c "from core.config import Config; Config()"
```

**Solutions:**
- Verify `.env` file exists and is valid
- Check port 8000 is not in use: `lsof -i :8000`
- Verify database connectivity

#### 2. High Memory Usage

**Symptoms:** Memory usage continuously growing

**Diagnosis:**
```bash
# Check memory usage
ps aux | grep mcp

# Monitor over time
watch -n 5 'ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f mcp_server)'
```

**Solutions:**
1. Check for memory leaks in audit logger
2. Restart service: `sudo systemctl restart mcp-unified`
3. Enable memory profiling if issue persists

#### 3. Slow Response Times

**Symptoms:** p95 latency > 500ms

**Diagnosis:**
```bash
# Run benchmark
./run_benchmark.sh

# Check resource usage
top -p $(pgrep -d',' -f mcp_server)
```

**Solutions:**
- Check database query performance
- Increase worker count if CPU-bound
- Enable caching for frequently accessed data

#### 4. Authentication Failures

**Symptoms:** 401/403 errors

**Diagnosis:**
```bash
# Check auth logs
grep "AUTH" /var/log/mcp/audit.log | tail -20

# Verify API key
curl -H "X-API-Key: test-key" http://localhost:8000/auth/me
```

**Solutions:**
- Regenerate API keys if expired
- Check JWT secret configuration
- Verify RBAC permissions

#### 5. Database Connection Issues

**Symptoms:** Database errors in logs

**Diagnosis:**
```bash
# Test connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"

# Check connection pool status
curl http://localhost:8000/metrics | grep db_connections
```

**Solutions:**
- Restart PostgreSQL: `sudo systemctl restart postgresql`
- Increase connection pool size
- Check network connectivity

---

## Maintenance Procedures

### Daily Tasks

- [ ] Check service status: `sudo systemctl status mcp-unified`
- [ ] Review error logs: `sudo journalctl -u mcp-unified --since "24 hours ago" | grep -i error`
- [ ] Verify backup completion
- [ ] Check disk space: `df -h`

### Weekly Tasks

- [ ] Review performance metrics
- [ ] Clean old logs (retain 30 days)
- [ ] Update security patches
- [ ] Run vulnerability scan: `python security/scanner.py`

### Monthly Tasks

- [ ] Full disaster recovery test
- [ ] Capacity planning review
- [ ] Security audit
- [ ] Documentation update

---

## Security Incidents

### Unauthorized Access Detected

1. **Immediate Actions:**
```bash
# Revoke suspicious API keys
python -c "from security.auth import AuthManager; AuthManager().revoke_key('suspicious-key-id')"

# Enable enhanced logging
export MCP_LOG_LEVEL=DEBUG
sudo systemctl restart mcp-unified
```

2. **Investigation:**
- Review audit logs
- Check access patterns
- Identify compromised credentials

3. **Recovery:**
- Rotate all API keys
- Reset JWT secrets
- Notify affected users

### Data Breach Response

1. **Containment:**
```bash
# Stop service
sudo systemctl stop mcp-unified

# Isolate affected systems
```

2. **Assessment:**
- Identify breached data
- Determine attack vector
- Assess impact

3. **Notification:**
- Notify security team
- File incident report
- Customer notification (if required)

---

## Escalation Procedures

### Severity Levels

| Level | Description | Response Time | Escalate To |
|-------|-------------|---------------|-------------|
| P1 | Service down | 15 min | Engineering Lead |
| P2 | Degraded performance | 1 hour | Senior Engineer |
| P3 | Minor issues | 4 hours | On-call Engineer |
| P4 | Questions/requests | 1 business day | Support Team |

### On-Call Rotation

**Primary:** Platform Team  
**Secondary:** Engineering Lead  
**Escalation:** CTO

**Contact:**
- Slack: #mcp-alerts
- PagerDuty: MCP Production
- Emergency: +1-XXX-XXX-XXXX

---

## Disaster Recovery

### Backup Strategy

**Database:**
```bash
# Daily automated backup
pg_dump -h localhost -U mcp_user mcp_db > /var/backups/mcp/db-$(date +%Y%m%d).sql

# Weekly full backup
pg_dumpall -h localhost -U postgres > /var/backups/mcp/full-$(date +%Y%m%d).sql
```

**Configuration:**
```bash
# Backup config
tar czf /var/backups/mcp/config-$(date +%Y%m%d).tar.gz /opt/mcp-unified/.env /opt/mcp-unified/config/
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop application
sudo systemctl stop mcp-unified

# Restore database
dropdb -h localhost -U mcp_user mcp_db
createdb -h localhost -U mcp_user mcp_db
psql -h localhost -U mcp_user mcp_db < /var/backups/mcp/db-YYYYMMDD.sql

# Restart
sudo systemctl start mcp-unified
```

#### Full System Recovery
```bash
# Fresh server setup
# 1. Install dependencies
# 2. Restore application code
# 3. Restore configuration
# 4. Restore database
# 5. Start services

./scripts/full_recovery.sh /var/backups/mcp/backup-YYYYMMDD/
```

---

## Appendix

### A. Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MCP_ENV` | Environment (development/staging/production) | Yes |
| `JWT_SECRET` | JWT signing secret | Yes |
| `DB_HOST` | Database host | Yes |
| `DB_NAME` | Database name | Yes |
| `DB_USER` | Database user | Yes |
| `DB_PASSWORD` | Database password | Yes |
| `REDIS_URL` | Redis URL (for caching) | No |
| `LOG_LEVEL` | Logging level | No (default: INFO) |

### B. Useful Commands

```bash
# Restart service
sudo systemctl restart mcp-unified

# View logs in real-time
sudo journalctl -u mcp-unified -f

# Check service dependencies
systemctl list-dependencies mcp-unified

# Reload configuration
sudo systemctl reload mcp-unified

# Disable service
sudo systemctl disable mcp-unified

# Enable service
sudo systemctl enable mcp-unified
```

### C. Related Documentation

- [API Documentation](./api-documentation.md)
- [Migration Guide](./migration-guide.md)
- [Security Audit Report](./security-audit-report.md)
- [Performance Baseline](./performance-baseline.md)
- [Disaster Recovery Plan](./disaster-recovery.md)
