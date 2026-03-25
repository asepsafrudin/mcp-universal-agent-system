# 04-operations — Operasional & Maintenance

Dokumentasi operasional mencakup deployment, disaster recovery, testing, dan maintenance.

## 📋 Konten

| File | Deskripsi |
|------|-----------|
| [`production-readiness.md`](./production-readiness.md) | Checklist production readiness |
| [`disaster-recovery.md`](./disaster-recovery.md) | Disaster recovery plan |
| [`persistent-service.md`](./persistent-service.md) | Setup persistent service dengan systemd |
| [`session-workflow.md`](./session-workflow.md) | Session workflow dan context |
| [`testing.md`](./testing.md) | Testing guide dan strategies |
| [`mcp-fix-summary.md`](./mcp-fix-summary.md) | Ringkasan perbaikan MCP Unified |

## 🚀 Deployment

### Production Checklist

Lihat detail lengkap di [`production-readiness.md`](./production-readiness.md):

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Logging configured
- [ ] Monitoring enabled
- [ ] Backup strategy implemented
- [ ] Security hardening applied

### Persistent Service

Setup MCP Unified sebagai systemd service:

```bash
# Copy service file
sudo cp mcp-unified/mcp-unified.service /etc/systemd/system/

# Enable dan start
sudo systemctl enable mcp-unified
sudo systemctl start mcp-unified

# Check status
sudo systemctl status mcp-unified
```

📄 Detail: [`persistent-service.md`](./persistent-service.md)

## 🛡️ Disaster Recovery

### Backup Strategy

| Komponen | Backup Method | Frequency |
|----------|---------------|-----------|
| PostgreSQL | `pg_dump` | Daily |
| Redis | `redis-cli SAVE` | Hourly |
| Config | Git + .env | On change |
| Code | Git | Continuous |

📄 Detail: [`disaster-recovery.md`](./disaster-recovery.md)

## 🧪 Testing

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **E2E Tests**: Full workflow testing
- **Security Tests**: Hardening validation

📄 Detail: [`testing.md`](./testing.md)

## 🔧 Maintenance & Fixes

### Ringkasan Perbaikan

Dokumentasi perbaikan dan maintenance yang telah dilakukan:

- **MCP SDK Installation**: Penambahan mcp>=1.0.0 ke requirements
- **Root Cleanup**: Pembersihan file liar di root directory
- **Path Fixes**: Perbaikan path di init_session.sh
- **Setup Script**: Pembuatan setup.sh dan QUICKSTART.md
- **Agent Rules**: Update .agent dengan rule baru

📄 Detail: [`mcp-fix-summary.md`](./mcp-fix-summary.md)

## 📖 Related Documentation

- **Getting Started** → [`../01-getting-started/`](../01-getting-started/)
- **Database** → [`../06-database/`](../06-database/)
- **Architecture** → [`../02-architecture/`](../02-architecture/)
