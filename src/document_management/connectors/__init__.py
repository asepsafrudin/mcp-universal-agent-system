#!/usr/bin/env python3
"""
Document Management System - Connectors
========================================
Connectors untuk berbagai sumber dokumen.
"""

from .base_connector import BaseConnector, FileInfo
from .onedrive_connector import OneDriveConnector

# Google Drive connector (optional - requires additional dependencies)
try:
    from .googledrive_connector import GoogleDriveConnector
except ImportError:
    GoogleDriveConnector = None

__all__ = [
    'BaseConnector',
    'FileInfo',
    'OneDriveConnector',
    'GoogleDriveConnector',
]

# Connector registry
CONNECTOR_REGISTRY = {
    'onedrive': OneDriveConnector,
    'googledrive': GoogleDriveConnector,
}

import json

def get_connector(source_type: str, source_id: int, source_name: str, config: dict):
    """Get connector instance by type"""
    connector_class = CONNECTOR_REGISTRY.get(source_type)
    if not connector_class:
        raise ValueError(f"Unknown connector type: {source_type}")
    
    # Parse config_json if it's a string
    if isinstance(config, str):
        try:
            config = json.loads(config) if config else {}
        except json.JSONDecodeError:
            config = {}
    
    return connector_class(source_id, source_name, config)
