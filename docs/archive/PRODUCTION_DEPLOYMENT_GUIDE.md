# 🚀 Extractor System - Production Deployment Guide

**Complete guide untuk deploy Extractor System ke production**

---

## 📋 Overview

Sistem ini menyediakan:
1. ✅ **Real Website Extraction** - Extract dari 11+ website legal Indonesia
2. ✅ **Knowledge Base Storage** - Auto-save ke PostgreSQL
3. ✅ **Production Deployment** - Systemd service + cron job

---

## 🏗️ Architecture Production

```
┌─────────────────────────────────────────────────────────────────┐
│                       PRODUCTION SETUP                          │
├─────────────────────────────────────────────────────────────────┤
│  CRON (6 AM Daily)                                              │
│  └── run_production_extraction.py --all --save                  │
├─────────────────────────────────────────────────────────────────┤
│  SYSTEMD SERVICE                                                │
│  └── extractor-scheduler.service (on-demand)                    │
├─────────────────────────────────────────────────────────────────┤
│  EXTRACTOR SYSTEM                                               │
│  ├── 11 Specialized Extractors                                  │
│  ├── Extractor Chain (fallback)                                 │
│  └── Quality Scoring                                            │
├─────────────────────────────────────────────────────────────────┤
│  KNOWLEDGE BASE                                                 │
│  └── PostgreSQL (pgvector)                                      │
│      └── Namespace: legal_regulations                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Deploy

### **1. Deploy to Production**

```bash
cd /home/aseps/MCP
chmod +x deploy_extractor_system.sh
./deploy_extractor_system.sh
```

**What this does:**
- ✅ Check dependencies (Python, Playwright, PostgreSQL)
- ✅ Create necessary directories
- ✅ Install systemd service
- ✅ Setup cron job (daily at 6 AM)
- ✅ Test extraction

---

## 📁 File Structure

```
/home/aseps/MCP/
├── run_production_extraction.py      # Main extraction script
├── deploy_extractor_system.sh        # Deployment script
├── PRODUCTION_DEPLOYMENT_GUIDE.md    # This guide
│
├── mcp-unified/integrations/agentic_ai/
│   ├── extractors/                   # 11 extractors
│   ├── extractor_registry.py         # Plugin manager
│   ├── extractor_chain.py            # Chain + ML selection
│   ├── knowledge_bridge_integration.py  # KB connector
│   └── README.md                     # Documentation
│
└── ~/logs/extractor/                 # Log files (created)
    ├── scheduler.log
    └── scheduler-error.log
```

---

## 🎯 Usage

### **Manual Extraction**

```bash
# Extract single source
cd /home/aseps/MCP
python3 run_production_extraction.py --source hukumonline --save

# Extract all sources
python3 run_production_extraction.py --all --save

# Dry run (no save)
python3 run_production_extraction.py --source hukumonline
```

### **Systemd Service**

```bash
# Start extraction service
sudo systemctl start extractor-scheduler

# Check status
sudo systemctl status extractor-scheduler

# View logs
sudo journalctl -u extractor-scheduler -f

# Stop service
sudo systemctl stop extractor-scheduler
```

### **Cron Job**

```bash
# Check cron job
crontab -l | grep extractor

# Edit cron
crontab -e
```

Default: `0 6 * * *` (Daily at 6 AM)

---

## 📊 Monitoring

### **Check Extraction Results**

```bash
# View latest extraction
cat extraction_hukumonline_*.json | jq '.count'

# View logs
tail -f ~/logs/extractor/scheduler.log

# Check KB stats (via Python)
python3 -c "
from mcp-unified.integrations.agentic_ai.knowledge_bridge_integration import ExtractorKnowledgeBridge
import asyncio

async def main():
    kb = ExtractorKnowledgeBridge()
    stats = await kb.get_stats('legal_regulations')
    print(f'Total documents: {stats[\"total_documents\"]}')
    print(f'By source: {stats[\"by_source\"]}')

asyncio.run(main())
"
```

---

## 🔧 Configuration

### **Add New Source**

Edit `run_production_extraction.py`:

```python
SOURCES = {
    "hukumonline": {...},
    "jdih": {...},
    "my_new_source": {           # Add here
        "url": "https://example.com",
        "extractor": MyExtractor,
        "name": "my_source"
    }
}
```

### **Change Schedule**

```bash
# Edit crontab
crontab -e

# Change to every 3 hours
0 */3 * * * cd /home/aseps/MCP && python3 run_production_extraction.py --all --save
```

---

## 🗄️ Knowledge Base Schema

**Table:** `documents` (dibuat oleh AgentKnowledgeBridge)

```sql
- doc_id: VARCHAR (primary key)
- content: TEXT
- metadata: JSONB
  - source: TEXT
  - url: TEXT
  - extracted_at: TIMESTAMP
  - type: TEXT (regulation/news)
  - regulation_type: TEXT (PP/Perpres/etc)
  - number: TEXT
  - date: TEXT
- namespace: VARCHAR (legal_regulations)
- embedding: VECTOR(1536)
```

---

## 🛠️ Troubleshooting

### **Issue: Playwright not found**
```bash
pip3 install playwright
python3 -m playwright install chromium
```

### **Issue: PostgreSQL connection failed**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U your_user -d your_db -c "SELECT 1"
```

### **Issue: Extraction returns 0 items**
```bash
# Check website accessibility
curl -I https://www.hukumonline.com/berita

# Run with debug
python3 run_production_extraction.py --source hukumonline 2>&1 | tee debug.log
```

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| **Extraction Time** | 5-15 seconds per source |
| **Quality Score Threshold** | 0.6 |
| **Daily Schedule** | 6 AM WIB |
| **Log Rotation** | Manual (setelah 100MB) |
| **KB Namespace** | legal_regulations |

---

## 🔒 Security Notes

1. **Database Credentials**: Stored in environment variables
2. **Log Files**: Contains URLs only (no sensitive data)
3. **Systemd Service**: Runs as user (not root)
4. **Cron Job**: User-level crontab

---

## 📝 Maintenance Checklist

**Weekly:**
- [ ] Check logs: `tail ~/logs/extractor/scheduler.log`
- [ ] Verify KB: Check document count
- [ ] Review failed extractions

**Monthly:**
- [ ] Update extractors (jika website berubah)
- [ ] Clean old log files
- [ ] Backup knowledge base
- [ ] Review extraction quality

**Quarterly:**
- [ ] Add new sources
- [ ] Optimize selectors
- [ ] Review ML selection performance

---

## 🎓 Advanced Usage

### **Custom Extraction Pipeline**

```python
from mcp-unified.integrations.agentic_ai import (
    ExtractorRegistry, ExtractorChain,
    ExtractorKnowledgeBridge
)

# Create custom chain
registry = get_registry()
extractors = [
    registry.get_extractor('hukumonline'),
    registry.get_extractor('detik'),
    GenericExtractor()
]

chain = ExtractorChain(extractors)

# Extract dengan ML selection
selector = MLExtractorSelector(extractors)
extractor = selector.select_extractor(url)
```

### **Batch Processing**

```bash
# Process multiple URLs
for url in $(cat urls.txt); do
    python3 -c "
from cline_interface import scrape_with_cline
import asyncio
result = asyncio.run(scrape_with_cline('$url'))
print(result)
"
done
```

---

## 📞 Support

**Documentation:** `mcp-unified/integrations/agentic_ai/README.md`

**Logs:** `~/logs/extractor/`

**Data:** `~/data/extractions/`

---

## ✅ Pre-Deployment Checklist

- [ ] PostgreSQL running
- [ ] Playwright installed
- [ ] Python dependencies OK
- [ ] Test extraction passed
- [ ] Knowledge Bridge connected
- [ ] Systemd service enabled
- [ ] Cron job configured
- [ ] Log directories created

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2026-03-06
