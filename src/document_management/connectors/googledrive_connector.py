#!/usr/bin/env python3
"""
Document Management System - Google Drive Connector
===================================================
Connector untuk Google Drive API.
Menggunakan Google Drive API v3 untuk mengakses file.
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Generator, Optional, List

from .base_connector import BaseConnector, FileInfo
from ..core.config import MIME_TYPES, GOOGLE_DRIVE_CONFIG


class GoogleDriveConnector(BaseConnector):
    """Connector for Google Drive via API"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, source_id: int, source_name: str, config: Dict = None):
        super().__init__(source_id, source_name, config or GOOGLE_DRIVE_CONFIG)
        self.credentials_path = Path(self.config.get('credentials_path'))
        self.token_path = Path(self.config.get('token_path'))
        self.sync_folder_id = self.config.get('sync_folder_id', '')
        self.service = None
        self._mime_mapping = {
            'application/vnd.google-apps.document': '.docx',
            'application/vnd.google-apps.spreadsheet': '.xlsx',
            'application/vnd.google-apps.presentation': '.pptx',
            'application/pdf': '.pdf',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'text/plain': '.txt',
        }
    
    def connect(self) -> bool:
        """Connect to Google Drive API"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            creds = None
            
            # Load existing token
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif self.credentials_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print(f"❌ Credentials not found: {self.credentials_path}")
                    return False
                
                # Save token
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build service
            self.service = build('drive', 'v3', credentials=creds)
            self._connected = True
            print(f"✅ Connected to Google Drive")
            return True
            
        except ImportError as e:
            print(f"❌ Google API libraries not installed: {e}")
            print("   Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return False
        except Exception as e:
            print(f"❌ Failed to connect to Google Drive: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Google Drive"""
        self.service = None
        self._connected = False
    
    def list_files(self, folder_id: str = None, recursive: bool = True) -> Generator[FileInfo, None, None]:
        """List files from Google Drive"""
        if not self._connected or not self.service:
            raise ConnectionError("Not connected. Call connect() first.")
        
        folder_id = folder_id or self.sync_folder_id
        
        if not folder_id:
            # List all files
            query = "trashed = false"
        else:
            # List files in specific folder
            query = f"'{folder_id}' in parents and trashed = false"
        
        page_token = None
        
        while True:
            try:
                results = self.service.files().list(
                    q=query,
                    pageSize=1000,
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, parents)"
                ).execute()
                
                items = results.get('files', [])
                
                for item in items:
                    file_info = self._convert_to_file_info(item)
                    if file_info:
                        yield file_info
                        
                        # Recursive: if folder, list its contents
                        if recursive and item['mimeType'] == 'application/vnd.google-apps.folder':
                            yield from self.list_files(item['id'], recursive=True)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except Exception as e:
                print(f"❌ Error listing files: {e}")
                break
    
    def get_file(self, file_id: str) -> Optional[bytes]:
        """Download file content from Google Drive"""
        if not self._connected or not self.service:
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            from googleapiclient.http import MediaIoBaseDownload
            import io
            
            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType', '')
            
            request = None
            
            # Handle Google Workspace files (export to Office format)
            if mime_type == 'application/vnd.google-apps.document':
                request = self.service.files().export_media(
                    fileId=file_id, 
                    mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            elif mime_type == 'application/vnd.google-apps.presentation':
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'
                )
            elif mime_type == 'application/vnd.google-apps.folder':
                return None  # Can't download folders
            else:
                # Regular file
                request = self.service.files().get_media(fileId=file_id)
            
            if not request:
                return None
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return fh.getvalue()
            
        except Exception as e:
            print(f"❌ Error downloading file {file_id}: {e}")
            return None
    
    def file_exists(self, file_id: str) -> bool:
        """Check if file exists in Google Drive"""
        if not self._connected or not self.service:
            return False
        
        try:
            self.service.files().get(fileId=file_id).execute()
            return True
        except:
            return False
    
    def get_file_hash(self, file_id: str) -> Optional[str]:
        """Get file hash (use md5Checksum from Google Drive)"""
        if not self._connected or not self.service:
            return None
        
        try:
            file_metadata = self.service.files().get(
                fileId=file_id, 
                fields='md5Checksum'
            ).execute()
            return file_metadata.get('md5Checksum')
        except:
            return None
    
    def _convert_to_file_info(self, item: Dict) -> Optional[FileInfo]:
        """Convert Google Drive item to FileInfo"""
        mime_type = item.get('mimeType', '')
        
        # Skip folders (handled separately)
        if mime_type == 'application/vnd.google-apps.folder':
            return None
        
        # Determine extension
        if mime_type in self._mime_mapping:
            extension = self._mime_mapping[mime_type]
        else:
            name = item.get('name', '')
            extension = Path(name).suffix.lower()
        
        # Parse timestamps
        modified_at = item.get('modifiedTime')
        created_at = item.get('createdTime')
        
        return FileInfo(
            file_name=item.get('name', ''),
            file_path=item.get('id'),  # Use ID as path
            external_id=item.get('id'),
            file_size=int(item.get('size', 0)) if 'size' in item else None,
            mime_type=mime_type,
            extension=extension,
            modified_at=modified_at,
            created_at=created_at
        )
    
    def get_folder_structure(self, folder_id: str = None) -> Dict:
        """Get folder structure for display"""
        if not self._connected or not self.service:
            return {}
        
        folder_id = folder_id or self.sync_folder_id or 'root'
        
        try:
            # Get folder name
            folder = self.service.files().get(fileId=folder_id).execute()
            
            structure = {
                'id': folder_id,
                'name': folder.get('name', 'Root'),
                'type': 'folder',
                'children': []
            }
            
            # Get children
            results = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="files(id, name, mimeType)"
            ).execute()
            
            for item in results.get('files', []):
                child = {
                    'id': item['id'],
                    'name': item['name'],
                    'type': 'folder' if item['mimeType'] == 'application/vnd.google-apps.folder' else 'file'
                }
                structure['children'].append(child)
            
            return structure
            
        except Exception as e:
            print(f"❌ Error getting folder structure: {e}")
            return {}
    
    def setup_folder(self, folder_name: str = "Document Management") -> str:
        """Create or select folder for sync"""
        if not self._connected or not self.service:
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            # Search for existing folder
            results = self.service.files().list(
                q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed = false",
                fields="files(id, name)"
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                print(f"✅ Found existing folder: {folder_name} (ID: {folder_id})")
                return folder_id
            
            # Create new folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"✅ Created new folder: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except Exception as e:
            print(f"❌ Error setting up folder: {e}")
            return None


def main():
    """Test the connector"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from core.database import get_db
    from core.config import setup_directories
    
    setup_directories()
    db = get_db()
    
    # Get or create source
    source = db.get_source_by_name('Google_Drive')
    if not source:
        source_id = db.add_source(
            source_type='googledrive',
            source_name='Google_Drive',
            display_name='Google Drive Documents',
            enabled=False,
            config={}
        )
    else:
        source_id = source['id']
    
    # Connect
    connector = GoogleDriveConnector(source_id, 'Google_Drive')
    
    print("\n📁 Google Drive Connector Test")
    print("=" * 60)
    
    if not connector.connect():
        print("❌ Failed to connect")
        print("   Make sure you have:")
        print("   1. Created credentials in Google Cloud Console")
        print("   2. Downloaded credentials.json")
        print("   3. Installed required libraries:")
        print("      pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return
    
    # Setup folder
    folder_id = connector.setup_folder("MCP Documents")
    if folder_id:
        connector.sync_folder_id = folder_id
    
    # List first 10 files
    print("\n📝 Sample files:")
    for i, file_info in enumerate(connector.list_files()):
        if i >= 10:
            break
        print(f"  - {file_info.file_name} ({file_info.mime_type})")
    
    connector.disconnect()


if __name__ == "__main__":
    main()