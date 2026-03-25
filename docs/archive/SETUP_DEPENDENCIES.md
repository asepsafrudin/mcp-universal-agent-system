# 🚀 Setup Dependencies & Ready to Use

**Status:** Implementation COMPLETE ✅  
**Next Step:** Install dependencies  
**Estimated Time:** 2-3 minutes

---

## ✅ Apakah Bisa Langsung Digunakan?

**YA!** Setelah dependencies diinstall, semua fitur siap pakai:

### Security (TASK-030)
- ✅ Login dengan hashed passwords
- ✅ RBAC enforcement
- ✅ Audit logging

### Scheduler (TASK-001)
- ✅ Cron scheduling berjalan
- ✅ Self-healing aktif
- ✅ Telegram notifications

### Office Tools (TASK-004/005)
- ✅ 36 functions siap digunakan
- ✅ DOCX, XLSX, PDF, PPTX support

---

## 📦 Install Dependencies

### 1. Security & Scheduler (Wajib)
```bash
# Tidak perlu install baru - menggunakan library bawaan Python
# (hashlib, secrets, hmac, asyncio, dll)

# Hanya perlu set environment variables:
export MCP_ADMIN_PASSWORD="YourSecurePassword123!"
export MCP_REVIEWER_PASSWORD="YourSecurePassword123!"
export MCP_VIEWER_PASSWORD="YourSecurePassword123!"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 2. Cron Parsing (Opsional tapi Direkomendasikan)
```bash
pip install croniter
```
*Catatan: Jika tidak install, akan menggunakan simplified estimation*

### 3. Office Tools (Wajib untuk fitur lengkap)
```bash
# Core (sudah terinstall)
# pip install python-docx openpyxl

# P1 Features (perlu diinstall)
pip install python-pptx>=0.6.21
pip install docx2pdf>=0.1.8
pip install PyPDF2>=3.0.0
pip install pdfplumber>=0.9.0
```

---

## 🧪 Quick Test Setelah Install

### Test 1: Security
```bash
cd /home/aseps/MCP/mcp-unified
python3 -c "
from knowledge.admin.auth import get_auth_manager
auth = get_auth_manager()
print('✅ Security system ready')
print('Generated passwords displayed above' if True else '')
"
```

### Test 2: Scheduler Cron
```bash
python3 -c "
from scheduler.executor import executor
result = executor.get_next_run_time('0 2 * * *')
print(f'✅ Cron parsing ready. Next run: {result}')
"
```

### Test 3: Office Tools
```bash
python3 -c "
from tools.office import __all__
print(f'✅ Office Tools ready: {len(__all__)} functions')
print('Categories:', {
    'DOCX': len([f for f in __all__ if 'docx' in f]),
    'XLSX': len([f for f in __all__ if 'xlsx' in f]),
    'PDF': len([f for f in __all__ if 'pdf' in f]),
    'PPTX': len([f for f in __all__ if 'pptx' in f])
})
"
```

---

## 🎯 Usage Examples (Ready to Use!)

### 1. Security - Login
```python
from knowledge.admin.auth import get_auth_manager

auth = get_auth_manager()
token = auth.authenticate('admin', 'your_password')

if token:
    print(f"Login successful! Role: {token.role}")
else:
    print("Invalid credentials")
```

### 2. Scheduler - Create Job
```python
from scheduler.tools import scheduler_create_job

job = await scheduler_create_job(
    name="daily-backup",
    job_type="backup_full",
    schedule_type="cron",
    schedule_expr="0 2 * * *",
    task_config={"command": "./backup.sh"}
)
print(f"Job created: {job['job_id']}")
```

### 3. Office Tools - DOCX
```python
from tools.office import search_replace_docx, add_header_footer_docx

# Search and replace
result = search_replace_docx(
    file_path='document.docx',
    search_text='old_text',
    replace_text='new_text'
)
print(f"Replaced: {result['replacements_made']} instances")

# Add header/footer
result = add_header_footer_docx(
    file_path='document.docx',
    header_text='Confidential',
    footer_text='Page 1'
)
```

### 4. Office Tools - XLSX Chart
```python
from tools.office import add_chart_xlsx

result = add_chart_xlsx(
    file_path='sales.xlsx',
    sheet_name='Sheet1',
    chart_type='bar',
    data_range='A1:B10',
    title='Monthly Sales'
)
print(f"Chart added: {result['success']}")
```

### 5. Office Tools - PDF
```python
from tools.office import convert_to_pdf, extract_text_pdf

# Convert DOCX to PDF
result = convert_to_pdf(
    input_path='report.docx',
    output_path='report.pdf'
)

# Extract text from PDF
result = extract_text_pdf(
    file_path='document.pdf',
    page_range=(1, 5)
)
print(f"Extracted {len(result['text'])} characters")
```

---

## ⚠️ Catatan Penting

### 1. Environment Variables WAJIB Di-set
```bash
# Untuk Security (WAJIB)
export MCP_ADMIN_PASSWORD="..."
export MCP_REVIEWER_PASSWORD="..."
export MCP_VIEWER_PASSWORD="..."

# Untuk Telegram (Opsional - hanya jika pakai notifikasi)
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
```

### 2. PDF Conversion di Linux
- `docx2pdf` mungkin tidak work di Linux
- Alternative: Gunakan LibreOffice CLI:
```bash
libreoffice --headless --convert-to pdf input.docx
```

### 3. Formula Calculation
- openpyxl tidak menghitung formulas
- File perlu dibuka di Excel untuk kalkulasi
- Atau gunakan library `xlwings` (requires Excel installed)

---

## ✅ Checklist Sebelum Produksi

- [ ] Install dependencies
- [ ] Set environment variables
- [ ] Test login ke Knowledge Admin
- [ ] Test create scheduled job
- [ ] Test office tools functions
- [ ] Backup database
- [ ] Monitor logs

---

## 🚀 Status

| Komponen | Status | Ready? |
|----------|--------|--------|
| Security | ✅ Implemented | Set env vars → Ready |
| Scheduler | ✅ Implemented | Install croniter → Ready |
| Office Tools | ✅ 36 functions | Install deps → Ready |

**Kesimpulan: Setelah `pip install` dan set env vars, sistem 100% READY!**

---

*Generated by MCP Setup Guide*  
*Date: 2026-03-03*
