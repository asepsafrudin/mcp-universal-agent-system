# 07 - Domain Examples

**Legal Assistant, Office Assistant, Mailroom Manager**

---

## 1. Legal Assistant

```python
# agents/profiles/legal_assistant.py

legal_agent = Agent.create(
    name="legal-assistant-id",
    description="Asisten hukum perdata Indonesia",
    talents=[
        "skills.legal.researcher",
        "skills.legal.analyzer",
        "skills.legal.drafter",
        "skills.communication.presenter"
    ],
    tools=[
        "tools.legal.jdih_search",
        "tools.legal.putusan_lookup",
        "tools.web.search"
    ],
    knowledge=[
        "knowledge://hukum-perdata",
        "knowledge://putusan-pengadilan"
    ]
)
```

**Use Case:** "Sewa rumah atap bocor, pemilik ogak perbaiki"

```
User Input
    ↓
SKILL: legal.researcher
    → Query: "kewajiban pemilik perbaiki sewa"
    → KNOWLEDGE: Retrieve Pasal 1552, 1571, 1600 BW
    ↓
SKILL: legal.analyzer
    → Interpretasi hak penyewa
    → TOOL: Generate PDF analisis
    ↓
SKILL: legal.drafter
    → Draft surat peringatan
    → TOOL: email.sender
    ↓
Output ke User
```

---

## 2. Office Assistant

```python
# agents/profiles/office_assistant.py

office_agent = Agent.create(
    name="office-assistant",
    description="Asisten administrasi kantor",
    talents=[
        "skills.admin.correspondence",
        "skills.admin.scheduler",
        "skills.admin.document_prep"
    ],
    tools=[
        "tools.admin.email_drafter",
        "tools.calendar.scheduler",
        "tools.document.pdf"
    ],
    knowledge=[
        "knowledge://admin-kantor",
        "knowledge://template-surat"
    ]
)
```

---

## 3. Mailroom Manager

```python
# agents/profiles/mailroom_manager.py

mailroom_agent = Agent.create(
    name="mailroom-manager",
    description="Manager surat menyurat",
    talents=[
        "skills.admin.mailroom.classifier",
        "skills.admin.mailroom.router",
        "skills.admin.mailroom.tracker"
    ],
    tools=[
        "tools.admin.spreadsheet_parser",
        "tools.admin.disposisi_generator"
    ],
    knowledge=[
        "knowledge://struktur-organisasi"
    ]
)
```

---

**Prev:** [06-agents-layer.md](06-agents-layer.md)  
**Next:** [08-security-audit.md](08-security-audit.md)
