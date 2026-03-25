#!/usr/bin/env python3
"""
Document Management System (DMS/ECM)
=====================================
Unified Document Index untuk OneDrive, Google Drive, dan Local files.
"""

__version__ = '1.0.0'
__author__ = 'MCP System'

from .core.database import get_db, DatabaseManager
from .core.config import setup_directories

__all__ = [
    'get_db',
    'DatabaseManager',
    'setup_directories',
]