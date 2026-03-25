#!/usr/bin/env python3
"""
Document Management System - Main Indexer
==========================================
Main entry point untuk indexing dan processing dokumen.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from document_management.core.database import get_db
from document_management.core.config import setup_directories
from document_management.connectors import get_connector
from document_management.processors import DocumentClassifier


class DocumentIndexer:
    """Main indexer for document management system"""
    
    def __init__(self):
        self.db = get_db()
        self.classifier = DocumentClassifier()
    
    def sync_source(self, source_name: str = None, source_type: str = None) -> Dict:
        """Sync documents from source"""
        if source_name:
            source = self.db.get_source_by_name(source_name)
            if not source:
                return {'success': False, 'error': f'Source not found: {source_name}'}
            sources = [source]
        elif source_type:
            all_sources = self.db.get_sources(enabled_only=True)
            sources = [s for s in all_sources if s['source_type'] == source_type]
        else:
            sources = self.db.get_sources(enabled_only=True)
        
        results = {}
        for source in sources:
            print(f"\n🔄 Syncing {source['source_name']} ({source['source_type']})...")
            
            try:
                connector = get_connector(
                    source['source_type'],
                    source['id'],
                    source['source_name'],
                    source.get('config_json', {})
                )
                result = connector.sync(self.db)
                results[source['source_name']] = result
                
                if result.get('success'):
                    print(f"✅ Synced: {result.get('new', 0)} new, {result.get('updated', 0)} updated")
                else:
                    print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error syncing {source['source_name']}: {e}")
                results[source['source_name']] = {'success': False, 'error': str(e)}
        
        return results
    
    def classify_pending(self, limit: int = None) -> Dict:
        """Classify pending documents"""
        print("\n🏷️  Classifying pending documents...")
        
        # Get documents without labels
        pending = self.db.get_pending_documents(limit)
        
        if not pending:
            print("✅ No documents to classify")
            return {'classified': 0}
        
        classified = 0
        for doc in pending:
            try:
                # Get content if available
                content = self.db.get_document_content(doc['id'])
                if content:
                    doc['extracted_text'] = content.get('extracted_text', '')
                
                # Classify
                labels = self.classifier.classify_document(doc)
                
                # Save labels
                for label in labels:
                    self.db.add_label(
                        document_id=doc['id'],
                        label_type=label.label_type,
                        label_value=label.label_value,
                        confidence=label.confidence,
                        source=label.source
                    )
                
                # Save government metadata
                metadata = self.classifier.extract_government_metadata(doc)
                if metadata:
                    self.db.add_government_metadata(doc['id'], **metadata)
                
                classified += 1
                print(f"  ✅ {doc['file_name'][:50]}... ({len(labels)} labels)")
                
            except Exception as e:
                print(f"  ❌ Error classifying {doc['file_name']}: {e}")
        
        print(f"\n📊 Classified {classified} documents")
        return {'classified': classified}
    
    def show_stats(self):
        """Show database statistics"""
        stats = self.db.get_stats()
        
        print("\n📊 Document Management Statistics")
        print("=" * 60)
        print(f"Total Documents: {stats.get('total_documents', 0)}")
        print(f"With Content: {stats.get('with_content', 0)}")
        print(f"With OCR: {stats.get('with_ocr', 0)}")
        print(f"Total Labels: {stats.get('total_labels', 0)}")
        
        print("\nBy Status:")
        for status, count in stats.get('by_status', {}).items():
            print(f"  {status}: {count}")
        
        print("\nBy Source:")
        for source, count in stats.get('by_source', {}).items():
            print(f"  {source}: {count}")
        
        print("\nBy Category:")
        for cat, count in stats.get('by_category', {}).items():
            print(f"  {cat}: {count}")
        
        print("\nTop Document Types:")
        for jenis, count in stats.get('top_jenis_dokumen', {}).items():
            print(f"  {jenis}: {count}")
    
    def reset_database(self):
        """Reset database"""
        confirm = input("⚠️  This will delete ALL data. Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            self.db.reset_database()
            print("✅ Database reset complete")
        else:
            print("❌ Cancelled")


def main():
    parser = argparse.ArgumentParser(
        description='Document Management System - Indexer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python indexer.py --sync                    # Sync all enabled sources
  python indexer.py --sync --source OneDrive  # Sync specific source
  python indexer.py --classify                # Classify pending documents
  python indexer.py --stats                   # Show statistics
  python indexer.py --reset                   # Reset database
        """
    )
    
    parser.add_argument('--sync', action='store_true',
                       help='Sync documents from sources')
    parser.add_argument('--source', type=str,
                       help='Sync specific source by name')
    parser.add_argument('--type', type=str, choices=['onedrive', 'googledrive', 'local'],
                       help='Sync sources by type')
    parser.add_argument('--classify', action='store_true',
                       help='Classify pending documents')
    parser.add_argument('--limit', type=int,
                       help='Limit number of documents to process')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics')
    parser.add_argument('--reset', action='store_true',
                       help='Reset database (dangerous!)')
    
    args = parser.parse_args()
    
    # Setup
    setup_directories()
    indexer = DocumentIndexer()
    
    # Execute commands
    if args.reset:
        indexer.reset_database()
    
    elif args.sync:
        results = indexer.sync_source(args.source, args.type)
        
        print("\n" + "=" * 60)
        print("📊 Sync Summary")
        print("=" * 60)
        for source, result in results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {source}: {result.get('new', 0)} new, "
                  f"{result.get('updated', 0)} updated")
    
    elif args.classify:
        result = indexer.classify_pending(args.limit)
        print(f"\n✅ Classified {result['classified']} documents")
    
    elif args.stats:
        indexer.show_stats()
    
    else:
        # Default: show stats
        indexer.show_stats()
        print("\n💡 Use --help for available commands")


if __name__ == "__main__":
    main()