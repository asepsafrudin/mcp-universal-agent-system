#!/usr/bin/env python3
"""
Smart Knowledge Sync — Ingest symlink folders ke MCP Knowledge Base

Usage:
    python3 /home/aseps/MCP/scripts/smart_knowledge_sync.py --folder OneDrive_PUU/PUU_2026
    python3 /home/aseps/MCP/scripts/smart_knowledge_sync.py --folder OneDrive_PUU/PUU_2026 --dry-run

Features:
- Auto-detect file changes
- Filter dokumen penting (PDF, DOCX, TXT)
- Extract text dan ingest ke RAG
- Track progress di LTM
"""
import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add MCP to path
sys.path.insert(0, str(Path("/home/aseps/MCP")))

from shared.mcp_client import MCPClient

# Supported document types
SUPPORTED_EXT = {'.pdf', '.docx', '.doc', '.txt', '.md'}
SKIP_PATTERNS = ['.zip', '.apk', '.exe', '.jpg', '.png', '.mp4', '.mp3']


class SmartKnowledgeSync:
    """Sync folder content ke MCP Knowledge Base."""
    
    def __init__(self, folder_path: str, namespace: str = None, dry_run: bool = False):
        self.folder_path = Path(folder_path)
        self.dry_run = dry_run
        
        # Auto-generate namespace dari folder name
        if namespace:
            self.namespace = namespace
        else:
            folder_name = self.folder_path.name.replace(" ", "_")
            self.namespace = f"Bangda_PUU_{folder_name}"
        
        self.client = MCPClient(namespace=self.namespace)
        self.stats = {
            "total_files": 0,
            "supported_files": 0,
            "processed": 0,
            "skipped": 0,
            "errors": 0
        }
        self.file_index = {}
        
    def scan_folder(self) -> List[Path]:
        """Scan folder dan return list file yang didukung."""
        print(f"\n📂 Scanning: {self.folder_path}")
        print(f"   Namespace: {self.namespace}")
        print(f"   Mode: {'DRY-RUN (no changes)' if self.dry_run else 'LIVE'}")
        
        all_files = []
        supported_files = []
        
        for root, dirs, files in os.walk(self.folder_path):
            # Skip hidden folders
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)
                
                # Check if supported
                ext = file_path.suffix.lower()
                if ext in SUPPORTED_EXT:
                    supported_files.append(file_path)
                elif any(pattern in file.lower() for pattern in SKIP_PATTERNS):
                    self.stats["skipped"] += 1
        
        self.stats["total_files"] = len(all_files)
        self.stats["supported_files"] = len(supported_files)
        
        print(f"\n📊 Scan Results:")
        print(f"   Total files: {self.stats['total_files']}")
        print(f"   Supported (PDF/DOCX/TXT): {self.stats['supported_files']}")
        print(f"   Skipped (binaries): {self.stats['skipped']}")
        
        return supported_files
    
    def categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Kategorikan file berdasarkan tipe dan prioritas."""
        categories = {
            "pdf_undangan": [],
            "pdf_sk": [],
            "pdf_other": [],
            "docx_lapkin": [],
            "docx_surat": [],
            "docx_other": [],
            "txt_md": []
        }
        
        for f in files:
            name_lower = f.name.lower()
            ext = f.suffix.lower()
            
            if ext == '.pdf':
                if 'undangan' in name_lower or 'und' in name_lower:
                    categories["pdf_undangan"].append(f)
                elif 'sk' in name_lower or 'kep' in name_lower:
                    categories["pdf_sk"].append(f)
                else:
                    categories["pdf_other"].append(f)
            elif ext in ['.docx', '.doc']:
                if 'lapkin' in name_lower:
                    categories["docx_lapkin"].append(f)
                elif 'surat' in name_lower or 'nd' in name_lower:
                    categories["docx_surat"].append(f)
                else:
                    categories["docx_other"].append(f)
            else:
                categories["txt_md"].append(f)
        
        return categories
    
    async def extract_text(self, file_path: Path) -> str:
        """Extract text dari file menggunakan text_extractor."""
        from shared.text_extractor import extract_text, clean_text
        
        stat = file_path.stat()
        
        # Extract content
        raw_text = extract_text(file_path)
        
        # Build full content dengan metadata
        content = f"""FILE: {file_path.name}
PATH: {file_path}
SIZE: {stat.st_size} bytes
MODIFIED: {datetime.fromtimestamp(stat.st_mtime)}
TYPE: {file_path.suffix}

--- CONTENT ---

{raw_text}
"""
        
        # Clean dan limit length
        return clean_text(content, max_length=100000)
    
    async def ingest_file(self, file_path: Path) -> bool:
        """Ingest single file ke knowledge base."""
        try:
            print(f"   📝 Ingesting: {file_path.name[:50]}...")
            
            if self.dry_run:
                return True
            
            # Extract text
            content = await self.extract_text(file_path)
            
            # Create doc_id dari relative path
            doc_id = str(file_path.relative_to(self.folder_path)).replace("/", "_")
            
            # Save ke MCP memory (sementara pakai memory_save)
            # Nanti bisa pakai RAGEngine langsung
            result = await self.client.save_context(
                key=f"doc:{doc_id}",
                content=content,
                metadata={
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "file_type": file_path.suffix,
                    "ingested_at": datetime.now().isoformat(),
                    "source": "SmartKnowledgeSync"
                }
            )
            
            self.stats["processed"] += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.stats["errors"] += 1
            return False
    
    async def run(self):
        """Main execution."""
        print("=" * 60)
        print("🧠 Smart Knowledge Sync")
        print("=" * 60)
        
        if not self.client.is_available:
            print("\n❌ MCP Hub tidak tersedia!")
            print("   Jalankan: cd /home/aseps/MCP/mcp-unified && python3 mcp_server_sse.py")
            return False
        
        # Scan folder
        files = self.scan_folder()
        
        if not files:
            print("\n⚠️  No supported files found!")
            return False
        
        # Categorize
        categories = self.categorize_files(files)
        
        print("\n📁 Categories:")
        for cat, cat_files in categories.items():
            if cat_files:
                print(f"   {cat}: {len(cat_files)} files")
        
        # Ingest files (prioritas: undangan, SK, then others)
        print("\n🚀 Starting Ingestion...")
        
        priority_order = [
            "pdf_undangan",
            "pdf_sk", 
            "docx_lapkin",
            "docx_surat",
            "pdf_other",
            "docx_other",
            "txt_md"
        ]
        
        for category in priority_order:
            cat_files = categories.get(category, [])
            if not cat_files:
                continue
                
            print(f"\n📌 Category: {category} ({len(cat_files)} files)")
            
            for file_path in cat_files[:5]:  # Limit 5 per category untuk demo
                await self.ingest_file(file_path)
        
        # Save sync state ke LTM
        if not self.dry_run:
            await self.client.save_context(
                key="sync_state:last_run",
                content=json.dumps({
                    "folder": str(self.folder_path),
                    "timestamp": datetime.now().isoformat(),
                    "stats": self.stats
                }),
                metadata={"type": "sync_state", "namespace": self.namespace}
            )
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SYNC SUMMARY")
        print("=" * 60)
        print(f"   Folder: {self.folder_path}")
        print(f"   Namespace: {self.namespace}")
        print(f"   Total files: {self.stats['total_files']}")
        print(f"   Supported: {self.stats['supported_files']}")
        print(f"   Processed: {self.stats['processed']}")
        print(f"   Skipped: {self.stats['skipped']}")
        print(f"   Errors: {self.stats['errors']}")
        print("=" * 60)
        
        return True


async def main():
    parser = argparse.ArgumentParser(description="Smart Knowledge Sync")
    parser.add_argument("--folder", required=True, help="Folder path to sync")
    parser.add_argument("--namespace", help="Override namespace")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes")
    
    args = parser.parse_args()
    
    # Resolve path
    folder_path = Path(args.folder)
    if not folder_path.is_absolute():
        folder_path = Path("/home/aseps/MCP") / folder_path
    
    if not folder_path.exists():
        print(f"❌ Folder not found: {folder_path}")
        sys.exit(1)
    
    # Run sync
    sync = SmartKnowledgeSync(
        folder_path=str(folder_path),
        namespace=args.namespace,
        dry_run=args.dry_run
    )
    
    success = await sync.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
