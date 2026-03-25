#!/usr/bin/env python3
"""
Document Management System - Base Connector
===========================================
Abstract base class untuk semua document source connectors.
"""

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Generator, Tuple
from dataclasses import dataclass


@dataclass
class FileInfo:
    """File information dataclass"""
    file_name: str
    file_path: str  # Relative path or URL
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    extension: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    external_id: Optional[str] = None
    modified_at: Optional[str] = None
    created_at: Optional[str] = None


class BaseConnector(ABC):
    """Abstract base class for document source connectors"""
    
    def __init__(self, source_id: int, source_name: str, config: Dict):
        self.source_id = source_id
        self.source_name = source_name
        self.config = config
        self._connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to source and validate access"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from source"""
        pass
    
    @abstractmethod
    def list_files(self, path: str = None, recursive: bool = True) -> Generator[FileInfo, None, None]:
        """List all files from source"""
        pass
    
    @abstractmethod
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file content as bytes"""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        pass
    
    @abstractmethod
    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate file hash"""
        pass
    
    def is_connected(self) -> bool:
        """Check if connector is connected"""
        return self._connected
    
    def sync(self, db_manager, incremental: bool = True) -> Dict:
        """Sync files to database"""
        stats = {'total': 0, 'new': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        if not self.connect():
            return {**stats, 'success': False, 'error': 'Connection failed'}
        
        try:
            # Start sync log
            log_id = db_manager.start_sync_log(self.source_id, 
                                               'incremental' if incremental else 'full')
            
            # Iterate files
            for file_info in self.list_files():
                stats['total'] += 1
                
                try:
                    # Check if exists
                    existing = db_manager.get_document_by_path(
                        self.source_id, file_info.file_path
                    )
                    
                    # Calculate hash if needed
                    if not file_info.file_hash:
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
                    
                    # Add/update document
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
                        external_id=file_info.external_id,
                        file_modified_at=file_info.modified_at
                    )
                    
                    stats[action] += 1
                    
                except Exception as e:
                    stats['errors'] += 1
                    print(f"❌ Error processing {file_info.file_path}: {e}")
            
            # Update source sync time
            db_manager.update_source_sync_time(self.source_id)
            
            # Complete sync log
            db_manager.complete_sync_log(
                log_id=log_id,
                status='completed' if stats['errors'] == 0 else 'partial',
                files_total=stats['total'],
                files_new=stats['new'],
                files_updated=stats['updated'],
                files_failed=stats['errors']
            )
            
            return {**stats, 'success': stats['errors'] == 0}
            
        except Exception as e:
            db_manager.complete_sync_log(
                log_id=log_id,
                status='failed',
                error_message=str(e)
            )
            return {**stats, 'success': False, 'error': str(e)}
        
        finally:
            self.disconnect()
    
    @staticmethod
    def calculate_hash(content: bytes) -> str:
        """Calculate MD5 hash of content"""
        return hashlib.md5(content).hexdigest()
    
    @staticmethod
    def calculate_hash_from_file(file_path: Path) -> Optional[str]:
        """Calculate MD5 hash from file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False