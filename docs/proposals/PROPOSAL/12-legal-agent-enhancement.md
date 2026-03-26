# Proposal 12: Legal Agent Enhancement

**Versi**: 1.0  
**Tanggal**: 2 Maret 2026  
**Status**: Draft  
**Penulis**: MCP System Architect  
**Kategori**: Domain Agent Enhancement

---

## 1. Ringkasan Eksekutif

### 1.1 Latar Belakang
Agent Legal saat ini (`mcp-unified/agents/profiles/legal_agent.py`) memiliki implementasi yang masih bersifat **placeholder** dengan kemampuan terbatas:
- Fungsi `review_contract`: Return dummy data
- Fungsi `check_compliance`: Return dummy score
- Fungsi `legal_research`: Return dummy findings
- Tidak terintegrasi dengan LLM (Groq/Gemini)
- Tidak terintegrasi dengan knowledge base UU 23/2014

### 1.2 Tujuan
Mengembangkan Legal Agent menjadi **domain agent yang fully functional** untuk:
- Memproses klasifikasi bidang urusan SPM secara otomatis
- Melakukan legal research terhadap regulasi pemerintahan daerah
- Verifikasi kepatuhan (compliance checking) dokumen hukum
- Analisis dan ekstraksi informasi dari dokumen perundang-undangan
- **Berintegrasi dengan Research Agent untuk pengumpulan data regulasi terbaru dari internet**

### 1.3 Inter-Agent Collaboration
Legal Agent akan berkolaborasi dengan **Research Agent** untuk:
- Mengumpulkan data regulasi terbaru (UU, PP, Perpres, Permendagri) dari internet
- Sinkronisasi antara knowledge base lokal dengan data eksternal
- Validasi dan verifikasi informasi yang dikumpulkan Research Agent
- Collaborative analysis untuk legal research yang komprehensif

### 1.3 Manfaat
| Aspek | Manfaat |
|-------|---------|
| **Efisiensi** | Otomatisasi proses klasifikasi dan verifikasi dokumen hukum |
| **Akurasi** | Reduksi human error dalam ekstraksi informasi legal |
| **Skalabilitas** | Dapat memproses banyak dokumen secara bersamaan |
| **Integrasi** | Terhubung dengan knowledge base UU 23/2014 dan SPM |

---

## 2. Analisis Current State

### 2.1 Arsitektur Existing

```
mcp-unified/
├── agents/
│   └── profiles/
│       ├── legal_agent.py          # Current: Placeholder implementation
│       └── research_agent.py       # Research Agent (data collection)
├── knowledge/
│   ├── sharing/namespace_manager.py # shared_legal namespace exists
│   └── integrated_processor.py      # Document processing available
└── integrations/
    └── telegram/                    # Human-in-the-loop bridge available
```

### 2.1.1 Research Agent Integration
Research Agent bertanggung jawab untuk:
- **Web scraping** dari sumber resmi (jdih.kemenkeu.go.id, peraturan.go.id, dll)
- **Data collection** untuk regulasi terbaru (UU, PP, Perpres, Permendagri)
- **Change detection** untuk perubahan regulasi yang ada
- **Data validation** sebelum disimpan ke knowledge base

### 2.2 Data Source Tersedia

| Source | Lokasi | Status |
|--------|--------|--------|
| Klasifikasi SPM | `Bangda_PUU/lampiran UU 23/processed/klasifikasi_bidang_urusan_spm.json` | ✅ Ready |
| UU 23/2014 Isi | `docs/knowledge/UU_23_2014_knowledge_base.json` | ✅ Ready |
| UU 23/2014 Lampiran | `processed/UU_23_2014_lampiran.json` | ✅ Ready |
| OneDrive_PUU Files | `knowledge_base/onedrive_puu_2025/` | ✅ Ready |
| Regulasi Pendukung | External (Perpres, Permendagri, dll) | 🔄 Need ingestion via Research Agent |

### 2.3 AI Provider Tersedia

| Provider | Model | Status |
|----------|-------|--------|
| Groq | qwen/qwen3-32b | ✅ Active |
| Gemini | gemini-2.0-flash | ✅ Active (backup) |
| Ollama | llava, moondream2 | ✅ Local vision |

---

## 3. Rencana Pengembangan

### 3.1 Fase 1: Core Integration (Week 1-2)

#### 3.1.1 LLM Integration
```python
# Enhanced Legal Agent dengan LLM
class LegalAgent(BaseAgent):
    def __init__(self):
        self.llm_client = GroqClient()  # Primary
        self.backup_llm = GeminiClient()  # Fallback
        self.kb_connector = UU23KnowledgeBase()
```

**Deliverables:**
- [ ] Integrasi Groq API ke Legal Agent
- [ ] Fallback mechanism ke Gemini
- [ ] Prompt template untuk legal tasks
- [ ] Response parsing dan validation

#### 3.1.2 Knowledge Base Connection
```python
# Koneksi ke UU 23/2014 Knowledge Base
class LegalKnowledgeConnector:
    def query_spm_classification(self, bidang: str) -> Dict
    def query_regulasi(self, uu: str, pasal: str) -> Dict
    def verify_dasar_hukum(self, claim: str) -> VerificationResult
```

**Deliverables:**
- [ ] Connector ke `UU_23_2014_knowledge_base.json`
- [ ] Query interface untuk klasifikasi SPM
- [ ] Cross-reference engine untuk regulasi

### 3.2 Fase 2: Enhanced Capabilities (Week 3-4)

#### 3.2.1 SPM Classification Processor
```python
async def process_spm_classification(self, json_data: Dict) -> ProcessingResult:
    """
    Memproses dan memverifikasi klasifikasi bidang urusan SPM
    - Validasi struktur JSON
    - Verifikasi dasar hukum
    - Cross-check dengan regulasi pendukung
    - Generate verification report
    """
```

**Fitur:**
- Validasi struktur data klasifikasi SPM
- Verifikasi kecocokan dasar hukum dengan UU 23/2014
- Identifikasi regulasi pendukung yang relevan
- Generate laporan verifikasi otomatis

#### 3.2.2 Legal Research Engine
```python
async def legal_research(self, query: str, context: Dict) -> ResearchResult:
    """
    Riset hukum dengan kemampuan:
    - Query ke knowledge base lokal
    - Search ke eksternal sources (jika diperlukan)
    - Synthesize findings dengan citations
    - Generate legal opinion summary
    """
```

**Fitur:**
- Natural language query untuk regulasi
- Citation generation (Pasal X ayat Y UU Z)
- Cross-reference antar regulasi
- Summary generation dengan bahasa hukum yang tepat

#### 3.2.3 Compliance Checker
```python
async def check_compliance(self, document: str, regulation: str) -> ComplianceReport:
    """
    Memeriksa kepatuhan dokumen terhadap regulasi:
    - Extract requirements dari regulasi
    - Compare dengan dokumen input
    - Identify gaps dan violations
    - Generate remediation recommendations
    """
```

### 3.3 Fase 3: Workflow Integration (Week 5-6)

#### 3.3.1 Automated Pipeline
```
Input Dokumen/JSON
    ↓
Legal Agent Pre-processing
    ↓
[Parallel Processing]
    ├─> Structure Validation
    ├─> Legal Research (dasar hukum)
    ├─> Compliance Check
    └─> Cross-reference Verification
    ↓
Synthesis & Report Generation
    ↓
Human Review (via Telegram Bridge)
    ↓
Final Output + Knowledge Base Update
```

#### 3.3.2 Human-in-the-Loop Integration
- Notifikasi ke Telegram untuk review hasil
- Interactive confirmation untuk critical decisions
- Feedback loop untuk continuous improvement

#### 3.3.3 MCP Tool Integration
```python
# Legal tools yang tersedia untuk agents lain
@mcp.tool()
def verify_spm_classification(data: Dict) -> VerificationResult:
    """Tool untuk memverifikasi klasifikasi SPM"""

@mcp.tool()
def research_regulation(query: str) -> ResearchResult:
    """Tool untuk riset regulasi"""

@mcp.tool()
def check_document_compliance(doc: str, reg: str) -> ComplianceReport:
    """Tool untuk compliance checking"""
```

---

## 4. Spesifikasi Teknis

### 4.1 Enhanced Legal Agent Structure

```
mcp-unified/agents/profiles/
├── legal_agent.py                    # Main agent (enhanced)
├── legal/
│   ├── __init__.py
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── kb_connector.py          # Knowledge base connector
│   │   ├── llm_connector.py         # LLM integration
│   │   └── external_api.py          # External legal APIs
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── spm_processor.py         # SPM classification processor
│   │   ├── document_processor.py    # Document analysis
│   │   └── research_engine.py       # Legal research engine
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── structure_validator.py   # JSON/document structure
│   │   ├── legal_validator.py       # Legal compliance
│   │   └── citation_validator.py    # Citation verification
│   └── templates/
│       ├── prompts/                 # LLM prompts
│       └── reports/                 # Report templates
```

### 4.2 API Endpoints (MCP Tools)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/legal/spm/verify` | POST | Verifikasi klasifikasi SPM |
| `/legal/research` | POST | Legal research query |
| `/legal/compliance/check` | POST | Compliance checking |
| `/legal/document/analyze` | POST | Dokumen analysis |
| `/legal/citation/verify` | POST | Verifikasi citations |

### 4.3 Configuration

```json
{
  "legal_agent": {
    "llm": {
      "primary": "groq/qwen-32b",
      "fallback": "gemini-2.0-flash",
      "temperature": 0.3,
      "max_tokens": 4096
    },
    "knowledge_base": {
      "namespaces": ["UU_23_2014_Lampiran", "UU_23_2014_Isi", "UU_23_2014_SPM_Klasifikasi"],
      "refresh_interval": 3600
    },
    "processing": {
      "max_concurrent": 3,
      "timeout": 300,
      "retry_attempts": 3
    },
    "notifications": {
      "telegram_enabled": true,
      "human_review_threshold": 0.7
    }
  }
}
```

---

## 5. Use Cases

### 5.1 Use Case 1: Automated SPM Classification Verification

**Scenario**: User mengirimkan file `klasifikasi_bidang_urusan_spm.json`

**Flow**:
1. Legal Agent menerima file
2. Structure validation (JSON schema)
3. Verifikasi dasar hukum:
   - Cross-check Pasal 12 UU 23/2014
   - Verifikasi regulasi pendukung (PP 2/2018, Permendagri 59/2021)
4. Generate verification report
5. Notifikasi hasil ke user

**Output**: Verification report dengan status, findings, dan recommendations

### 5.2 Use Case 2: Legal Research Query

**Scenario**: User bertanya: "Apa dasar hukum SPM bidang kesehatan?"

**Flow**:
1. Query parsing
2. Search knowledge base (UU_23_2014_SPM_Klasifikasi)
3. Extract relevant information:
   - Pasal 12 ayat (1) huruf b
   - Sub-urusan kesehatan (12 items)
   - Regulasi pendukung
4. Synthesize response dengan proper citations
5. Return formatted answer

**Output**: Research result dengan citations dan summary

### 5.3 Use Case 3: Document Compliance Check

**Scenario**: Periksa apakah dokumen kebijakan daerah sesuai dengan UU 23/2014

**Flow**:
1. Document ingestion (PDF/DOCX)
2. Extract key provisions
3. Compare dengan UU 23/2014 requirements
4. Identify compliance gaps
5. Generate remediation plan

**Output**: Compliance report dengan gap analysis dan recommendations

---

## 6. Success Criteria

### 6.1 Functional Requirements

| ID | Requirement | Priority | Measurement |
|----|-------------|----------|-------------|
| FR-1 | LLM Integration (Groq/Gemini) | Must | Response time < 5s |
| FR-2 | KB Connector untuk UU 23/2014 | Must | 100% query success |
| FR-3 | SPM Classification Processor | Must | >90% accuracy |
| FR-4 | Legal Research Engine | Should | Relevant results >85% |
| FR-5 | Compliance Checker | Should | False positive <10% |
| FR-6 | Human-in-the-loop Integration | Should | Telegram notif <2s |

### 6.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Response Time | < 10s untuk simple queries |
| NFR-2 | Throughput | 10 concurrent requests |
| NFR-3 | Availability | 99.5% uptime |
| NFR-4 | Accuracy | > 90% untuk legal citations |
| NFR-5 | Scalability | Support 1000+ documents |

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] LLM integration (Groq + Gemini fallback)
- [ ] Knowledge base connector
- [ ] Basic prompt templates
- [ ] Unit tests

### Phase 2: Core Features (Week 3-4)
- [ ] SPM classification processor
- [ ] Legal research engine
- [ ] Compliance checker
- [ ] Integration tests

### Phase 3: Integration (Week 5-6)
- [ ] MCP tools registration
- [ ] Telegram bridge integration
- [ ] Workflow automation
- [ ] End-to-end tests

### Phase 4: Optimization (Week 7-8)
- [ ] Performance tuning
- [ ] Prompt optimization
- [ ] Error handling enhancement
- [ ] Documentation

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM hallucination | High | High | Human review, citation verification |
| API rate limits | Medium | Medium | Caching, rate limiting, fallback |
| KB data staleness | Medium | Medium | Regular refresh, version tracking |
| Complexity creep | Medium | Medium | Agile sprints, MVP first |

---

## 9. Dependencies

### 9.1 External Dependencies
- Groq API access (API key configured ✅)
- Gemini API access (API key configured ✅)
- Knowledge base data availability (✅)
- **Research Agent operational** (🔄 Phase 1 development)
- **Web scraping infrastructure** (🔄 To be implemented)
- **External data sources access**:
  - jdih.kemendagri.go.id
  - peraturan.go.id
  - Other government portals

### 9.2 Internal Dependencies
- MCP Server running
- Knowledge base modules
- Telegram bot integration (✅)

---

## 10. Appendix

### A. Reference Documents
- UU No. 23 Tahun 2014 tentang Pemerintahan Daerah
- PP No. 2 Tahun 2018 tentang Standar Pelayanan Minimal
- Permendagri No. 59 Tahun 2021 tentang Penerapan SPM
- `klasifikasi_bidang_urusan_spm.json`

### B. Related Proposals
- Proposal 06: Agents Layer
- Proposal 11: Autonomous Task Scheduler
- Proposal 04: Knowledge Layer

### C. Glossary
- **SPM**: Standar Pelayanan Minimal
- **KB**: Knowledge Base
- **LLM**: Large Language Model
- **MCP**: Model Context Protocol

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-02 | MCP System Architect | Initial draft |

**Approval**

- [ ] Technical Lead
- [ ] Legal Domain Expert
- [ ] Project Manager
