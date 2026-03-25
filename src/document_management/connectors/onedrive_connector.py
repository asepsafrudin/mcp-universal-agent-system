#!/usr/bin/env python3
"""
Document Management System - OneDrive Connector
===============================================
Connector untuk file lokal/symlink OneDrive_PUU.
"""

import os
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, Generator, Optional

from .base_connector import BaseConnector, FileInfo
from ..core.config import MIME_TYPES, ONEDRIVE_CONFIG


class OneDriveConnector(BaseConnector):
    """Connector for local OneDrive_PUU files (via symlink)"""
    
    def __init__(self, source_id: int, source_name: str, config: Dict = None):
        super().__init__(source_id, source_name, config or ONEDRIVE_CONFIG)
        self.base_path = Path(self.config.get('base_path', '/home/aseps/OneDrive_PUU'))
        self.categories = self.config.get('categories', ['PUU_2024', 'PUU_2025', 'PUU_2026'])
    
    def connect(self) -> bool:
        """Connect and validate base path"""
        if not self.base_path.exists():
            print(f"❌ OneDrive path not found: {self.base_path}")
            self._connected = False
            return False
        
        self._connected = True
        print(f"✅ Connected to OneDrive: {self.base_path}")
        return True
    
    def disconnect(self):
        """Disconnect (no-op for local files)"""
        self._connected = False
    
    def list_files(self, path: str = None, recursive: bool = True) -> Generator[FileInfo, None, None]:
        """List all files from OneDrive base path"""
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")
        
        base = self.base_path / path if path else self.base_path
        
        if not base.exists():
            return
        
        # Get iterator based on recursive flag
        if recursive:
            files_iter = base.rglob("*")
        else:
            files_iter = base.iterdir()
        
        for file_path in files_iter:
            if not file_path.is_file():
                continue
            
            try:
                stat = file_path.stat()
                rel_path = file_path.relative_to(self.base_path)
                
                # Determine category from path
                parts = rel_path.parts
                category = parts[0] if parts else 'uncategorized'
                subcategory = str(Path(*parts[1:-1])) if len(parts) > 2 else ''
                
                # Skip if not in allowed categories (unless listing all)
                if category not in self.categories and category != 'uncategorized':
                    continue
                
                yield FileInfo(
                    file_name=file_path.name,
                    file_path=str(rel_path),
                    file_size=stat.st_size,
                    mime_type=self._get_mime_type(file_path),
                    extension=file_path.suffix.lower(),
                    category=category,
                    subcategory=subcategory,
                    modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat()
                )
                
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
                continue
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file content as bytes"""
        full_path = self.base_path / file_path
        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
            return None
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        full_path = self.base_path / file_path
        return full_path.exists() and full_path.is_file()
    
    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of file"""
        full_path = self.base_path / file_path
        return self.calculate_hash_from_file(full_path)
    
    def get_full_path(self, file_path: str) -> Path:
        """Get full filesystem path"""
        return self.base_path / file_path
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file"""
        ext = file_path.suffix.lower()
        return MIME_TYPES.get(ext, mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream')
    
    def index_category(self, category: str, db_manager) -> Dict:
        """Index specific category"""
        cat_path = self.base_path / category
        
        if not cat_path.exists():
            return {'success': False, 'error': f'Category not found: {category}'}
        
        stats = {'total': 0, 'new': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        for file_info in self.list_files(str(category)):
            stats['total'] += 1
            
            try:
                # Check if exists
                existing = db_manager.get_document_by_path(
                    self.source_id, file_info.file_path
                )
                
                # Calculate hash
                file_info.file_hash = self.get_file_hash(file_info.file_path)
                
                # Determine action
                if existing:
                    if existing['file_hash'] == file_info.file_hash:
                        stats['skipped'] += 1
                        continue
                    else:
                        action = 'updated'
                else:
                    action = 'new'
                
                # Add/update
                db_manager.add_document(
                    source_id=self.source_id,
                    file_name=file_info.file_name,
                    file_path=file_info.file_path,
                    file_hash=file_info.file_hash,
                    file_size=file_info.file_size,
                    mime_type=file_info.mime_type,
                    extension=file_info.extension,
                    category=file_info.category,
                    subcategory=file_info.subcategory,
                    file_modified_at=file_info.modified_at
                )
                
                stats[action] += 1
                
            except Exception as e:
                stats['errors'] += 1
                print(f"❌ Error indexing {file_info.file_path}: {e}")
        
        return stats


def main():
    """Test the connector"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from core.database import get_db
    from core.config import setup_directories
    
    setup_directories()
    db = get_db()
    
    # Get or create source
    source = db.get_source_by_name('OneDrive_PUU')
    if not source:
        source_id = db.add_source(
            source_type='onedrive',
            source_name='OneDrive_PUU',
            display_name='OneDrive - Peraturan UU',
            enabled=True,
            config={'base_path': str(ONEDRIVE_CONFIG['base_path'])}
        )
    else:
        source_id = source['id']
    
    # Connect and sync
    connector = OneDriveConnector(source_id, 'OneDrive_PUU')
    
    print("\n📁 OneDrive Connector Test")
    print("=" * 60)
    
    if not connector.connect():
        print("❌ Failed to connect")
        return
    
    # List first 5 files
    print("\n📝 Sample files:")
    for i, file_info in enumerate(connector.list_files()):
        if i >= 5:
            break
        print(f"  - {file_info.file_path} ({file_info.file_size} bytes)")
    
    # Sync
    print("\n🔄 Running sync...")
    result = connector.sync(db)
    
    print(f"\n📊 Sync Results:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    connector.disconnect()


if __name__ == "__main__":
    main()