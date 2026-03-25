# TASK-002: Legal Agent Enhancement

**Status:** ACTIVE
**Priority**: HIGH  
**Assignee**: TBD  
**Created**: 2026-03-02  
**Due**: 2026-04-27 (8 weeks)  
**Labels**: `enhancement`, `legal`, `agent`, `mcp`, `uu-23-2014`

---

## 📋 Ringkasan

Memaksimalkan kemampuan **Legal Agent** dalam memproses tugas-tugas legal seperti:
- Klasifikasi bidang urusan SPM (Standar Pelayanan Minimal)
- Legal research terhadap regulasi pemerintahan daerah
- Verifikasi dan compliance checking dokumen hukum
- Analisis perundang-undangan (UU 23/2014 dan regulasi terkait)

## 🎯 Tujuan

Mengubah Legal Agent dari **placeholder implementation** menjadi **fully functional domain agent** yang terintegrasi dengan:
- LLM (Groq/Gemini) untuk intelligent processing
- Knowledge Base UU 23/2014 untuk data retrieval
- **Research Agent untuk pengumpulan data regulasi terbaru dari internet**
- MCP Tools untuk akses dari agents lain
- Telegram Bridge untuk human-in-the-loop

### Inter-Agent Collaboration
Legal Agent ↔ Research Agent untuk:
- **Data Collection**: Research Agent scraping regulasi terbaru
- **Gap Analysis**: Legal Agent identifikasi kekurangan data lokal
- **Validation**: Legal Agent memvalidasi data yang dikumpulkan Research Agent
- **Synthesis**: Kombinasi hasil analisis dari kedua agents

## 📊 Current State vs Target

| Aspek | Current | Target |
|-------|---------|--------|
| LLM Integration | ❌ Placeholder | ✅ Groq + Gemini fallback |
| Knowledge Base | ❌ Not connected | ✅ UU 23/2014 + SPM connected |
| SPM Processing | ❌ Manual | ✅ Automated verification |
| Legal Research | ❌ Dummy data | ✅ Real research with citations |
| Compliance Check | ❌ Not implemented | ✅ Full compliance checking |
| MCP Tools | ❌ Not exposed | ✅ 5+ legal tools available |

---

## 🏗️ Arsitektur

### Komponen Utama dengan Research Agent Integration

```
┌──────────────────────────────────────────────────────────────────┐
│              COLLABORATIVE AGENT ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────┐      ┌─────────────────────────┐   │
│  │     LEGAL AGENT v2.0    │◄────►│    RESEARCH AGENT       │   │
│  │                         │      │                         │   │
│  │  ┌───────────────────┐  │      │  ┌───────────────────┐  │   │
│  │  │   LLM Layer       │  │      │  │ Web Scraping      │  │   │
│  │  │  (Groq/Gemini)    │  │      │  │ Engine            │  │   │
│  │  └───────────────────┘  │      │  └───────────────────┘  │   │
│  │                         │      │                         │   │
│  │  ┌───────────────────┐  │      │  ┌───────────────────┐  │   │
│  │  │ Knowledge Base    │  │◄────►│  │ Data Collection   │  │   │
│  │  │ Connector         │  │ Sync │  │ & Validation      │  │   │
│  │  └───────────────────┘  │      │  └───────────────────┘  │   │
│  │                         │      │                         │   │
│  │  ┌───────────────────┐  │      │  ┌───────────────────┐  │   │
│  │  │ Legal Processors  │  │      │  │ Change Detection  │  │   │
│  │  │ (SPM/Research)    │  │      │  │ & Notification    │  │   │
│  │  └───────────────────┘  │      │  └───────────────────┘  │   │
│  │                         │      │                         │   │
│  │  ┌───────────────────┐  │      │  ┌───────────────────┐  │   │
│  │  │ MCP Tools         │  │      │  │ External APIs     │  │   │
│  │  │ (5+ legal tools)  │  │      │  │ (jdih, peraturan) │  │   │
│  │  └───────────────────┘  │      │  └───────────────────┘  │   │
│  └─────────────────────────┘      └─────────────────────────┘   │
│              │                               │                   │
│              └───────────────┬───────────────┘                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           KNOWLEDGE BASE (Synchronized)                  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│  │  │UU_23_2014│ │ SPM JSON │ │External  │ │ Metadata │  │    │
│  │  │  Local   │ │Local     │ │Regulation│ │  & Sync  │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              TELEGRAM BRIDGE (Human Review)              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📅 Implementation Roadmap

### Phase 0: Research Agent Setup (Week 0-1) 🔍
**Goal**: Establish Research Agent for data collection

#### Tasks:
- [ ] **0.1** Develop/Enhance Research Agent
  - [ ] Web scraping engine (`scrapers/`)
  - [ ] Data collection scheduler
  - [ ] Change detection system
  - [ ] Data validation pipeline

- [ ] **0.2** Configure Data Sources
  - [ ] jdih.kemendagri.go.id scraper
  - [ ] peraturan.go.id scraper
  - [ ] Other government portals
  - [ ] RSS/Atom feed monitoring

- [ ] **0.3** Inter-Agent Communication
  - [ ] Message queue between Legal ↔ Research
  - [ ] Data sync protocol
  - [ ] Conflict resolution mechanism

**Deliverables**:
- Research Agent operational with 3+ data sources
- Legal-Research Agent communication established
- Automated data collection running

### Phase 1: Foundation (Week 1-2) 🏗️
**Goal**: Core infrastructure and LLM integration

#### Tasks:
- [ ] **1.1** Create `legal/` module structure under `agents/profiles/`
  - [ ] `connectors/` - KB and LLM connectors
  - [ ] `processors/` - SPM and document processors
  - [ ] `validators/` - Structure and legal validators
  - [ ] `templates/` - Prompts and report templates

- [ ] **1.2** Implement LLM Connector
  - [ ] Groq integration (`llm_connector.py`)
  - [ ] Gemini fallback mechanism
  - [ ] Prompt template system
  - [ ] Response parsing and validation

- [ ] **1.3** Implement Knowledge Base Connector (with Research Agent)
  - [ ] KB connector for UU 23/2014
  - [ ] **Research Agent integration point**
  - [ ] Query interface for SPM classification
  - [ ] **Live sync mechanism**
  - [ ] Cross-reference engine
  - [ ] Caching mechanism

- [ ] **1.4** Unit Tests
  - [ ] LLM connector tests
  - [ ] KB connector tests
  - [ ] **Research Agent mock tests**
  - [ ] Integration tests

**Deliverables**:
- Working LLM integration with Groq + Gemini fallback
- KB connector with Research Agent integration ready
- 80%+ unit test coverage

---

### Phase 2: Core Features (Week 3-4) ⚙️
**Goal**: SPM and legal processing with live data

#### Tasks:
- [ ] **2.1** SPM Classification Processor (with Live Data)
  - [ ] JSON structure validation
  - [ ] Dasar hukum verification
  - [ ] **Research Agent: Regulasi pendukung sync**
  - [ ] **Cross-check dengan data terbaru dari internet**
  - [ ] Verification report generation

- [ ] **2.2** Legal Research Engine (Collaborative)
  - [ ] Natural language query processing
  - [ ] Knowledge base search (local)
  - [ ] **Delegate ke Research Agent untuk data eksternal**
  - [ ] **Gap analysis: local vs external data**
  - [ ] Citation generation (Pasal X ayat Y)
  - [ ] Summary generation

- [ ] **2.3** Compliance Checker
  - [ ] Document ingestion (PDF/DOCX)
  - [ ] Requirement extraction
  - [ ] **Live regulation lookup via Research Agent**
  - [ ] Gap analysis
  - [ ] Remediation recommendations

- [ ] **2.4** Enhanced Legal Agent
  - [ ] Refactor `legal_agent.py`
  - [ ] Integrate all processors
  - [ ] **Integrate Research Agent client**
  - [ ] Add error handling
  - [ ] Performance optimization

**Deliverables**:
- SPM classification processor dengan live data sync
- Collaborative legal research engine
- Working compliance checker

---

### Phase 3: Integration (Week 5-6) 🔌
**Goal**: Full integration dengan Research Agent

#### Tasks:
- [ ] **3.1** MCP Tools Registration (with Research Agent)
  - [ ] `verify_spm_classification()` tool
  - [ ] `research_regulation()` tool (with live data option)
  - [ ] `check_document_compliance()` tool
  - [ ] `analyze_legal_document()` tool
  - [ ] `verify_citations()` tool
  - [ ] **`sync_regulations()` tool** (trigger Research Agent)

- [ ] **3.2** Telegram Bridge Integration
  - [ ] Notification system for results
  - [ ] **Research Agent status notifications**
  - [ ] Interactive confirmation flow
  - [ ] Error notifications
  - [ ] Human review requests
  - [ ] **Data sync approval workflow**

- [ ] **3.3** Workflow Automation
  - [ ] Automated pipeline for SPM processing
  - [ ] **Research Agent scheduled sync workflow**
  - [ ] Document processing workflow
  - [ ] Batch processing capability
  - [ ] Progress tracking (Legal + Research)

- [ ] **3.4** End-to-End Testing
  - [ ] Full workflow tests (with Research Agent)
  - [ ] **Inter-agent communication tests**
  - [ ] Load testing
  - [ ] Integration tests with other agents

**Deliverables**:
- 6 MCP tools registered (including sync)
- Telegram notifications with Research Agent status
- Collaborative workflows operational

---

### Phase 4: Optimization (Week 7-8) 🚀
**Goal**: Performance tuning and documentation

#### Tasks:
- [ ] **4.1** Performance Tuning
  - [ ] Response time optimization (< 10s)
  - [ ] Caching improvements
  - [ ] Concurrent processing optimization
  - [ ] Memory usage optimization

- [ ] **4.2** Prompt Optimization
  - [ ] Legal-specific prompt engineering
  - [ ] Few-shot examples
  - [ ] Chain-of-thought prompting
  - [ ] Output format refinement

- [ ] **4.3** Error Handling & Logging
  - [ ] Comprehensive error handling
  - [ ] Structured logging
  - [ ] Error recovery mechanisms
  - [ ] Monitoring and alerts

- [ ] **4.4** Documentation
  - [ ] API documentation
  - [ ] User guide
  - [ ] Developer documentation
  - [ ] Training materials

**Deliverables**:
- Optimized performance metrics achieved
- Complete documentation
- Production-ready system

---

## 📁 File Structure

```
mcp-unified/agents/profiles/
├── legal_agent.py                          # Main enhanced agent
└── legal/                                  # Legal agent module
    ├── __init__.py
    ├── connectors/
    │   ├── __init__.py
    │   ├── llm_connector.py               # Groq/Gemini integration
    │   ├── kb_connector.py                # Knowledge base connector
    │   └── external_api.py                # External legal APIs
    ├── processors/
    │   ├── __init__.py
    │   ├── spm_processor.py               # SPM classification
    │   ├── document_processor.py          # Document analysis
    │   └── research_engine.py             # Legal research
    ├── validators/
    │   ├── __init__.py
    │   ├── structure_validator.py         # JSON/doc structure
    │   ├── legal_validator.py             # Legal compliance
    │   └── citation_validator.py          # Citation verification
    ├── templates/
    │   ├── prompts/
    │   │   ├── spm_verification.txt       # SPM verification prompt
    │   │   ├── legal_research.txt         # Legal research prompt
    │   │   └── compliance_check.txt       # Compliance prompt
    │   └── reports/
    │       ├── spm_report.md              # SPM report template
    │       └── compliance_report.md       # Compliance template
    └── utils/
        ├── __init__.py
        ├── citation_parser.py             # Parse legal citations
        └── text_extractor.py              # Extract text from docs
```

---

## 🛠️ MCP Tools

| Tool Name | Input | Output | Description |
|-----------|-------|--------|-------------|
| `legal_verify_spm` | SPM JSON data | VerificationResult | Verifikasi klasifikasi SPM |
| `legal_research` | Query string | ResearchResult | Riset regulasi |
| `legal_check_compliance` | Document + Regulation | ComplianceReport | Compliance checking |
| `legal_analyze_document` | Document path | AnalysisResult | Analisis dokumen hukum |
| `legal_verify_citations` | Citations list | VerificationResult | Verifikasi citations |

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/agents/legal/test_llm_connector.py
# tests/agents/legal/test_kb_connector.py
# tests/agents/legal/test_spm_processor.py
# tests/agents/legal/test_validators.py
```

### Integration Tests
```python
# tests/agents/legal/test_end_to_end.py
# tests/agents/legal/test_mcp_tools.py
# tests/agents/legal/test_telegram_bridge.py
```

### Test Data
- Sample SPM JSON files
- Sample legal documents (PDF/DOCX)
- Test queries for legal research
- Mock KB data

---

## 📊 Success Metrics

### Functional Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| SPM Classification Accuracy | > 90% | Manual verification of 50 samples |
| Legal Research Relevance | > 85% | User feedback on 30 queries |
| Compliance Check Precision | > 90% | Expert review of 20 documents |
| Citation Accuracy | > 95% | Automated + manual verification |
| Response Time (simple) | < 10s | Average of 100 requests |
| Response Time (complex) | < 30s | Average of 50 requests |

### Non-Functional Metrics

| Metric | Target |
|--------|--------|
| System Uptime | 99.5% |
| Concurrent Requests | 10+ |
| Error Rate | < 2% |
| Test Coverage | > 80% |

---

## 🔗 Dependencies

### External
- [x] Groq API key configured
- [x] Gemini API key configured
- [ ] External legal API (optional)
- [ ] **Research Agent: Web scraping infrastructure**
- [ ] **Government portal access (jdih, peraturan.go.id)**

### Internal
- [x] MCP Server operational
- [x] Knowledge Base UU 23/2014 ready
- [x] Telegram bot integration
- [ ] **Research Agent operational**
- [ ] **Inter-agent communication protocol**
- [ ] Task scheduler (optional)

### Blocking Tasks
- None - Ready to start

---

## 🚨 Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM Hallucination | High | High | Citation verification, human review |
| API Rate Limits | Medium | Medium | Caching, rate limiting, fallback |
| **Research Agent Unavailable** | Medium | High | **Fallback ke local KB, queue untuk retry** |
| **Web Scraping Blocked** | Medium | Medium | **Rotating proxies, respectful scraping, rate limiting** |
| **Data Source Changed** | Medium | Medium | **Adaptive scrapers, change detection** |
| KB Data Incomplete | Medium | Medium | Data validation, user notification |
| Scope Creep | Medium | Medium | Strict MVP definition, agile sprints |
| Integration Issues | Low | High | Early integration testing |

---

## 📚 References

### Documents
- [Proposal 12: Legal Agent Enhancement](../../PROPOSAL/12-legal-agent-enhancement.md)
- [UU 23/2014 Knowledge Base](../../Bangda_PUU/lampiran%20UU%2023/docs/knowledge/UU_23_2014_knowledge_base.json)
- [SPM Classification](../../Bangda_PUU/lampiran%20UU%2023/processed/klasifikasi_bidang_urusan_spm.json)
- [Sync Report](../../Bangda_PUU/lampiran%20UU%2023/docs/SYNC_REPORT_20260302.md)

### Code
- [Current Legal Agent](../../mcp-unified/agents/profiles/legal_agent.py)
- [Base Agent](../../mcp-unified/agents/base.py)
- [KB Connector](../../mcp-unified/knowledge/integrated_processor.py)
- **[Research Agent](../../mcp-unified/agents/profiles/research_agent.py)** (existing or to be created)

### Inter-Agent Communication
```
Legal Agent ──► Request Data ──► Research Agent
     ▲                              │
     └──────── Validated Data ──────┘
              (with metadata)
```

---

## 📝 Notes

### Design Decisions
1. **Groq as Primary LLM**: Faster response, cost-effective
2. **Gemini as Fallback**: Reliable backup, good for long context
3. **Modular Architecture**: Easy to extend and maintain
4. **Human-in-the-Loop**: Critical decisions require human confirmation

### Open Questions
- [ ] Should we integrate with external legal databases?
- [ ] What is the priority for document types (PDF vs DOCX vs TXT)?
- [ ] Should we implement batch processing UI?
- [ ] **How often should Research Agent sync dengan data sources?** (hourly/daily/weekly)
- [ ] **Should Research Agent work independently atau hanya on-demand dari Legal Agent?**
- [ ] **How to handle conflicting data antara local KB dan external sources?**

---

## ✅ Definition of Done

- [ ] All Phase 1-4 tasks completed
- [ ] All success metrics achieved
- [ ] Documentation complete
- [ ] Code reviewed and approved
- [ ] Tests passing (unit + integration)
- [ ] Deployed to production
- [ ] User acceptance testing passed
- [ ] Handover documentation complete

---

## 🔄 Status Updates

| Date | Status | Notes |
|------|--------|-------|
| 2026-03-02 | 🔵 BACKLOG | Task created, proposal approved |
| 2026-03-03 | 🟡 IN PROGRESS | 50% MVP Complete - Phase 0-1 compressed |
| | | |

### 📊 Progress 50% Hari Ini (2026-03-03)

#### ✅ Selesai Hari Ini:

1. **Module Structure** (100%)
   - ✅ `legal/` module dengan struktur lengkap
   - ✅ `connectors/`, `processors/`, `validators/`, `templates/`

2. **LLM Connector** (100%)
   - ✅ Groq primary (mixtral-8x7b-32768)
   - ✅ Gemini fallback (gemini-pro)
   - ✅ Async implementation dengan timeout

3. **KB Connector** (100%)
   - ✅ UU 23/2014 integration
   - ✅ SPM classification loader
   - ✅ Search & verification functions

4. **SPM Processor** (100%)
   - ✅ Classification dengan LLM
   - ✅ Verification engine (KB + LLM)

5. **Research Agent Enhancement** (100%)
   - ✅ JDIH Scraper (jdih.kemendagri.go.id)
   - ✅ Peraturan Scraper (peraturan.go.id)
   - ✅ Integration ke Research Agent

6. **MCP Tools** (100%)
   - ✅ `legal_verify_spm`
   - ✅ `legal_research`
   - ✅ `legal_check_compliance`

7. **Inter-Agent Communication** (100%)
   - ✅ Message bus system
   - ✅ Legal-Research bridge
   - ✅ Request/response pattern

8. **Enhanced Legal Agent** (100%)
   - ✅ Refactored dengan connectors
   - ✅ New actions: verify_spm, classify_spm, research_regulation
   - ✅ TaskResult integration

#### 📁 Files Created Hari Ini:
```
mcp-unified/agents/profiles/legal/
├── __init__.py
├── connectors/
│   ├── __init__.py
│   ├── llm_connector.py
│   └── kb_connector.py
├── processors/
│   ├── __init__.py
│   └── spm_processor.py
└── inter_agent.py

mcp-unified/agents/profiles/research/
└── scrapers/
    ├── __init__.py
    ├── jdih_scraper.py
    └── peraturan_scraper.py

mcp-unified/tools/
└── legal_tools.py

mcp-unified/agents/profiles/
├── legal_agent.py (updated)
└── research_agent.py (updated)
```

#### ⏳ Sisa 50% (Week 2-8):
- Phase 2: Advanced compliance, batch processing
- Phase 3: Full 5 MCP tools, Telegram integration
- Phase 4: Optimization, documentation, testing

---

**Next Review**: 2026-03-09

**Stakeholders**:
- Technical Lead
- Legal Domain Expert
- Project Manager
- End Users (Bangda_PUU Team)

---

*Generated by MCP Task Manager*
*Template: task-enhancement-legal*
