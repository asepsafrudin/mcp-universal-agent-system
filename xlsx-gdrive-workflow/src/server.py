#!/usr/bin/env python3
"""
XLSX GDrive Workflow MCP Server - Shared Env Edition
Uses pandas + Google Drive API for XLSX processing workflow
Includes OCR, NLP, and LLM-enhanced context extraction tools
"""
import asyncio
import os
import json
import io
import tempfile
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load .env if available (shared env)
from dotenv import load_dotenv
load_dotenv()

# Add MCP root directory to path for mcp-unified imports
_MCP_ROOT = str(Path(__file__).parent.parent.parent)
_MCP_UNIFIED = str(Path(__file__).parent.parent.parent / "mcp-unified")
sys.path.insert(0, _MCP_UNIFIED)

# OCR imports (lazy loading)
try:
    from services.ocr.service import OCREngine
    from services.ocr.nlp_processor import get_nlp_processor, normalize_ocr_text, extract_entities
    from services.ocr.context_refiner import get_context_refiner
    from services.ocr.learning_store import get_learning_store
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# LLM Configuration
LLM_ENABLED = os.getenv("OCR_USE_LLM", "false").lower() == "true"
LLM_PROVIDER = os.getenv("OCR_LLM_PROVIDER", "none")
LLM_MODEL = os.getenv("OCR_LLM_MODEL", "qwen/qwen3-32b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Initialize OCR engine (lazy)
_ocr_engine = None
_nlp_processor = None
_context_refiner = None
_learning_store = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None and OCR_AVAILABLE:
        _ocr_engine = OCREngine()
    return _ocr_engine

def get_nlp():
    global _nlp_processor
    if _nlp_processor is None and OCR_AVAILABLE:
        _nlp_processor = get_nlp_processor()
    return _nlp_processor

def get_refiner():
    global _context_refiner
    if _context_refiner is None and OCR_AVAILABLE:
        _context_refiner = get_context_refiner()
    return _context_refiner

def get_store():
    global _learning_store
    if _learning_store is None and OCR_AVAILABLE:
        _learning_store = get_learning_store()
    return _learning_store

mcp_server = Server({
    "name": "xlsx-gdrive-workflow",
    "version": "0.1.0",
    "capabilities": {"tools": {}}
})

TOOLS = [
    {
        "name": "process_xlsx_folder",
        "description": "Scan GDrive folder, process semua XLSX: download → extract → structured JSON → upload hasil",
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder_id": {"type": "string", "description": "GDrive folder ID"},
                "output_format": {"type": "string", "enum": ["json", "csv"], "default": "json"}
            },
            "required": ["folder_id"]
        }
    },
    {
        "name": "extract_single_xlsx",
        "description": "Extract structured data dari 1 XLSX file (return pandas DataFrame as JSON)",
        "inputSchema": {
            "type": "object",
            "properties": {"file_id": {"type": "string"}},
            "required": ["file_id"]
        }
    },
    {
        "name": "ocr_extract_text",
        "description": "Ekstrak teks dari gambar menggunakan PaddleOCR (mendukung dokumen pemerintah Indonesia)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path ke file gambar (PNG/JPG)"},
                "use_llm": {"type": "boolean", "default": true, "description": "Gunakan LLM untuk context refinement"}
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "nlp_process_text",
        "description": "Proses teks OCR dengan NLP: normalisasi, koreksi typo, ekstraksi entity, quality scoring",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Teks hasil OCR"},
                "track_changes": {"type": "boolean", "default": false, "description": "Track perubahan yang dilakukan"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "extract_spm_document",
        "description": "Ekstraksi dokumen SPM (Surat Pernyataan Tanggung Jawab Belanja) menggunakan LLM dengan konteks khusus",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ocr_text": {"type": "string", "description": "Teks hasil OCR dari dokumen SPM"},
                "use_llm": {"type": "boolean", "default": true, "description": "Gunakan LLM untuk ekstraksi"}
            },
            "required": ["ocr_text"]
        }
    },
    {
        "name": "extract_document_context",
        "description": "Ekstrak konteks dokumen: jenis dokumen, instansi, periode, tujuan, bahasa formalitas",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Teks dokumen"},
                "use_llm": {"type": "boolean", "default": true, "description": "Gunakan LLM untuk konteks"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "validate_document_field",
        "description": "Validasi field dokumen menggunakan LLM (cek kesesuaian dengan konteks field)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "field_name": {"type": "string", "description": "Nama field (nomor_surat, kode_satuan_kerja, dll)"},
                "value": {"type": "string", "description": "Nilai field yang divalidasi"}
            },
            "required": ["field_name", "value"]
        }
    }
]

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [Tool(name=t["name"], description=t["description"], inputSchema=t["inputSchema"]) for t in TOOLS]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    try:
        if name == "process_xlsx_folder":
            folder_id = arguments["folder_id"]
            result = await process_folder(folder_id, arguments.get("output_format", "json"))
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "extract_single_xlsx":
            file_id = arguments["file_id"]
            df_json = extract_xlsx_to_json(file_id)
            return [TextContent(type="text", text=json.dumps(df_json, indent=2))]
        elif name == "ocr_extract_text":
            image_path = arguments["image_path"]
            use_llm = arguments.get("use_llm", True)
            result = ocr_extract_text(image_path, use_llm)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        elif name == "nlp_process_text":
            text = arguments["text"]
            track_changes = arguments.get("track_changes", False)
            result = nlp_process_text(text, track_changes)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        elif name == "extract_spm_document":
            ocr_text = arguments["ocr_text"]
            use_llm = arguments.get("use_llm", True)
            result = extract_spm_document(ocr_text, use_llm)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        elif name == "extract_document_context":
            text = arguments["text"]
            use_llm = arguments.get("use_llm", True)
            result = extract_document_context(text, use_llm)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        elif name == "validate_document_field":
            field_name = arguments["field_name"]
            value = arguments["value"]
            result = validate_document_field(field_name, value)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        else:
            return [TextContent(type="text", text=f"❌ Tool '{name}' tidak ditemukan")]
    except Exception as e:
        return [TextContent(type="text", text=f"💥 Error: {str(e)}")]

def ocr_extract_text(image_path: str, use_llm: bool = True) -> Dict:
    """Ekstrak teks dari gambar menggunakan PaddleOCR."""
    if not OCR_AVAILABLE:
        return {"error": "OCR module tidak tersedia. Pastikan mcp-unified/services/ocr tersedia."}
    
    engine = get_ocr_engine()
    if engine is None:
        return {"error": "Gagal menginisialisasi OCR engine"}
    
    try:
        result = engine.extract_text(image_path, use_llm=use_llm)
        return {
            "status": "success",
            "image_path": image_path,
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0),
            "llm_used": use_llm and LLM_ENABLED
        }
    except Exception as e:
        return {"error": f"OCR extraction failed: {str(e)}"}

def nlp_process_text(text: str, track_changes: bool = False) -> Dict:
    """Proses teks OCR dengan NLP."""
    if not OCR_AVAILABLE:
        return {"error": "NLP module tidak tersedia."}
    
    nlp = get_nlp()
    if nlp is None:
        return {"error": "Gagal menginisialisasi NLP processor"}
    
    try:
        if track_changes:
            normalized, changes = nlp.normalize(text, track_changes=True)
            entities = nlp.extract_entities(text)
            return {
                "status": "success",
                "original": text,
                "normalized": normalized,
                "changes": changes,
                "entities": entities
            }
        else:
            normalized = nlp.normalize(text)
            entities = nlp.extract_entities(text)
            return {
                "status": "success",
                "original": text,
                "normalized": normalized,
                "entities": entities
            }
    except Exception as e:
        return {"error": f"NLP processing failed: {str(e)}"}

def extract_spm_document(ocr_text: str, use_llm: bool = True) -> Dict:
    """Ekstraksi dokumen SPM menggunakan LLM dengan konteks khusus."""
    if not OCR_AVAILABLE:
        return {"error": "Context refiner module tidak tersedia."}
    
    refiner = get_refiner()
    if refiner is None:
        return {"error": "Gagal menginisialisasi context refiner"}
    
    try:
        result = refiner.extract_spm_document(ocr_text)
        return {
            "status": "success",
            "llm_used": use_llm and LLM_ENABLED,
            "provider": LLM_PROVIDER,
            "model": LLM_MODEL,
            "spm_data": result
        }
    except Exception as e:
        return {"error": f"SPM extraction failed: {str(e)}"}

def extract_document_context(text: str, use_llm: bool = True) -> Dict:
    """Ekstrak konteks dokumen: jenis dokumen, instansi, periode, tujuan, bahasa formalitas."""
    if not OCR_AVAILABLE:
        return {"error": "Context refiner module tidak tersedia."}
    
    refiner = get_refiner()
    if refiner is None:
        return {"error": "Gagal menginisialisasi context refiner"}
    
    try:
        if use_llm and LLM_ENABLED:
            result = refiner.extract_context(text)
        else:
            result = refiner._rule_based_context(text)
        return {
            "status": "success",
            "llm_used": use_llm and LLM_ENABLED,
            "provider": LLM_PROVIDER if (use_llm and LLM_ENABLED) else "rule-based",
            "context": result
        }
    except Exception as e:
        return {"error": f"Context extraction failed: {str(e)}"}

def validate_document_field(field_name: str, value: str) -> Dict:
    """Validasi field dokumen menggunakan LLM."""
    if not OCR_AVAILABLE:
        return {"error": "Context refiner module tidak tersedia."}
    
    refiner = get_refiner()
    if refiner is None:
        return {"error": "Gagal menginisialisasi context refiner"}
    
    try:
        result = refiner.validate_field(field_name, value)
        return {
            "status": "success",
            "field_name": field_name,
            "value": value,
            "validation": result
        }
    except Exception as e:
        return {"error": f"Field validation failed: {str(e)}"}

async def process_folder(folder_id: str, output_format: str = "json") -> Dict:
    """[TODO] Full workflow: list XLSX → process each → upload result"""
    # Placeholder - integrate gdrive tools
    return {
        "status": "stub",
        "folder_id": folder_id,
        "output_format": output_format,
        "next": "Implement gdrive_list_files + download + pandas + upload"
    }

def extract_xlsx_to_json(file_id: str) -> Dict:
    """[TODO] Download XLSX → pandas.read_excel → to_json"""
    # Placeholder logic
    return {
        "status": "stub",
        "file_id": file_id,
        "extracted_sheets": ["Sheet1", "Sheet2"],
        "next": "Implement real GDrive download + pandas processing"
    }

async def main():
    print("🚀 XLSX GDrive Workflow Server started (Shared Env Mode)", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())

