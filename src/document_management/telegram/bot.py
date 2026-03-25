#!/usr/bin/env python3
"""
Document Management System - Telegram Bot
==========================================
Telegram bot untuk query dan upload dokumen.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from document_management.core.database import get_db
from document_management.core.config import TELEGRAM_CONFIG, ONEDRIVE_CONFIG
from document_management.connectors.onedrive_connector import OneDriveConnector
from document_management.processors.ocr_engine import process_document


# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class DocumentBot:
    """Telegram bot for document management"""
    
    def __init__(self):
        self.db = get_db()
        self.token = TELEGRAM_CONFIG.get('bot_token')
        self.admin_ids = [int(x) for x in TELEGRAM_CONFIG.get('admin_chat_ids', []) if x]
    
    def run(self):
        """Run the bot"""
        if not self.token:
            print("❌ TELEGRAM_BOT_TOKEN not set")
            return
        
        application = Application.builder().token(self.token).build()
        
        # Command handlers
        application.add_handler(CommandHandler("start", self.cmd_start))
        application.add_handler(CommandHandler("help", self.cmd_help))
        application.add_handler(CommandHandler("search", self.cmd_search))
        application.add_handler(CommandHandler("find", self.cmd_find))
        application.add_handler(CommandHandler("stats", self.cmd_stats))
        application.add_handler(CommandHandler("recent", self.cmd_recent))
        application.add_handler(CommandHandler("sync", self.cmd_sync))
        application.add_handler(CommandHandler("status", self.cmd_status))
        
        # Callback handlers
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # File upload handler
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # Error handler
        application.add_error_handler(self.error_handler)
        
        print("🤖 Bot is running...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user = update.effective_user
        
        welcome_text = f"""
👋 Halo {user.first_name}!

🤖 *Document Management Bot*

Bot ini membantu Anda mengelola dan mencari dokumen.

📋 *Perintah yang tersedia:*
/search <keyword> - Cari dokumen
/find <jenis> <tahun> - Cari berdasarkan filter
/recent - Dokumen terbaru
/stats - Statistik database
/status - Status sistem
/help - Bantuan lengkap

📁 *Upload dokumen:*
Kirim file langsung ke bot untuk diindex.
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = """
📖 *Panduan Penggunaan*

🔍 *Pencarian:*
/search UU Kepolisian
/search "peraturan pemerintah"
/find jenis=UU tahun=2023
/find instansi=KEMENKUMHAM

📊 *Informasi:*
/stats - Statistik dokumen
/recent - 10 dokumen terbaru
/status - Status sync & processing

📤 *Upload:*
Kirim file PDF, DOCX, XLSX, atau gambar.
Bot akan otomatis mengextract text dan melabeli.

📁 *Kategori:*
• UU - Undang-Undang
• PP - Peraturan Pemerintah
• PERPRES - Peraturan Presiden
• PERMEN - Peraturan Menteri
• PERDA - Peraturan Daerah
• dll
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search documents using FTS"""
        query = ' '.join(context.args)
        
        if not query:
            await update.message.reply_text(
                "❌ Gunakan: /search <keyword>\n"
                "Contoh: /search UU Kepolisian"
            )
            return
        
        await update.message.reply_text(f"🔍 Mencari: *{query}*...", parse_mode='Markdown')
        
        try:
            results = self.db.search_documents(query, limit=10)
            
            if not results:
                await update.message.reply_text("❌ Tidak ditemukan dokumen.")
                return
            
            response = f"📊 Ditemukan {len(results)} dokumen:\n\n"
            
            for i, doc in enumerate(results, 1):
                source = doc.get('source_name', 'Unknown')
                category = doc.get('category', 'Uncategorized')
                name = doc.get('file_name', 'Unknown')[:50]
                
                response += f"{i}. *{name}*\n"
                response += f"   📁 {category} | 📍 {source}\n\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("❌ Error saat mencari.")
    
    async def cmd_find(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Find documents with filters"""
        args = ' '.join(context.args)
        
        if not args:
            await update.message.reply_text(
                "❌ Gunakan: /find <filter>\n"
                "Contoh: /find jenis=UU tahun=2023"
            )
            return
        
        # Parse filters
        filters = {}
        for part in args.split():
            if '=' in part:
                key, value = part.split('=', 1)
                filters[key] = value
        
        if not filters:
            await update.message.reply_text("❌ Format filter salah. Gunakan: key=value")
            return
        
        await update.message.reply_text(f"🔍 Mencari dengan filter...")
        
        try:
            # Build query based on filters
            results = self._find_with_filters(filters)
            
            if not results:
                await update.message.reply_text("❌ Tidak ditemukan dokumen.")
                return
            
            response = f"📊 Ditemukan {len(results)} dokumen:\n\n"
            
            for i, doc in enumerate(results[:10], 1):
                name = doc.get('file_name', 'Unknown')[:40]
                jenis = doc.get('jenis_dokumen', '-')
                tahun = doc.get('tahun', '-')
                
                response += f"{i}. *{name}*\n"
                response += f"   🏷️ {jenis} | 📅 {tahun}\n\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Find error: {e}")
            await update.message.reply_text("❌ Error saat mencari.")
    
    def _find_with_filters(self, filters: Dict) -> List[Dict]:
        """Find documents with filters"""
        import sqlite3
        
        conn = sqlite3.connect(str(self.db.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        conditions = ["1=1"]
        params = []
        
        if 'jenis' in filters:
            conditions.append("d.id IN (SELECT document_id FROM document_labels WHERE label_type='jenis_dokumen' AND label_value LIKE ?)")
            params.append(f"%{filters['jenis']}%")
        
        if 'tahun' in filters:
            conditions.append("d.id IN (SELECT document_id FROM document_labels WHERE label_type='tahun' AND label_value = ?)")
            params.append(filters['tahun'])
        
        if 'instansi' in filters:
            conditions.append("d.id IN (SELECT document_id FROM document_labels WHERE label_type='instansi' AND label_value LIKE ?)")
            params.append(f"%{filters['instansi']}%")
        
        if 'category' in filters:
            conditions.append("d.category LIKE ?")
            params.append(f"%{filters['category']}%")
        
        sql = f"""
            SELECT d.*, 
                   (SELECT label_value FROM document_labels WHERE document_id=d.id AND label_type='jenis_dokumen' LIMIT 1) as jenis_dokumen,
                   (SELECT label_value FROM document_labels WHERE document_id=d.id AND label_type='tahun' LIMIT 1) as tahun
            FROM file_documents d
            WHERE {' AND '.join(conditions)}
            ORDER BY d.indexed_at DESC
            LIMIT 20
        """
        
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show statistics"""
        try:
            stats = self.db.get_stats()
            
            response = "📊 *Statistik Dokumen*\n\n"
            response += f"📁 Total: {stats.get('total_documents', 0)}\n"
            response += f"📝 Dengan Konten: {stats.get('with_content', 0)}\n"
            response += f"👁️ Dengan OCR: {stats.get('with_ocr', 0)}\n"
            response += f"🏷️ Total Label: {stats.get('total_labels', 0)}\n\n"
            
            response += "📈 *Berdasarkan Status:*\n"
            for status, count in stats.get('by_status', {}).items():
                response += f"  • {status}: {count}\n"
            
            response += "\n🏛️ *Jenis Dokumen Teratas:*\n"
            for jenis, count in list(stats.get('top_jenis_dokumen', {}).items())[:5]:
                response += f"  • {jenis}: {count}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            await update.message.reply_text("❌ Error saat mengambil statistik.")
    
    async def cmd_recent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent documents"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT d.*, s.source_name
                    FROM file_documents d
                    JOIN file_sources s ON d.source_id = s.id
                    ORDER BY d.indexed_at DESC
                    LIMIT 10
                """)
                results = [dict(row) for row in cursor.fetchall()]
            
            if not results:
                await update.message.reply_text("📭 Belum ada dokumen.")
                return
            
            response = "🕐 *10 Dokumen Terbaru:*\n\n"
            
            for i, doc in enumerate(results, 1):
                name = doc.get('file_name', 'Unknown')[:40]
                category = doc.get('category', '-')
                source = doc.get('source_name', '-')
                
                response += f"{i}. *{name}*\n"
                response += f"   📁 {category} | 📍 {source}\n\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Recent error: {e}")
            await update.message.reply_text("❌ Error saat mengambil dokumen terbaru.")
    
    async def cmd_sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Trigger sync (admin only)"""
        user_id = update.effective_user.id
        
        if self.admin_ids and user_id not in self.admin_ids:
            await update.message.reply_text("❌ Anda tidak memiliki akses.")
            return
        
        await update.message.reply_text("🔄 Memulai sinkronisasi...")
        
        try:
            from document_management.indexer import DocumentIndexer
            
            indexer = DocumentIndexer()
            results = indexer.sync_source()
            
            response = "✅ *Sinkronisasi Selesai*\n\n"
            for source, result in results.items():
                status = "✅" if result.get('success') else "❌"
                response += f"{status} {source}:\n"
                response += f"   🆕 {result.get('new', 0)} baru\n"
                response += f"   🔄 {result.get('updated', 0)} update\n\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            await update.message.reply_text(f"❌ Error saat sinkronisasi: {e}")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system status"""
        try:
            # Get sync history
            sync_history = self.db.get_sync_history(limit=3)
            
            response = "📊 *Status Sistem*\n\n"
            
            response += "🕐 *Sinkronisasi Terakhir:*\n"
            if sync_history:
                for sync in sync_history:
                    source = sync.get('source_name', 'Unknown')
                    status = sync.get('status', 'unknown')
                    started = sync.get('started_at', '-')[:16]
                    
                    icon = "✅" if status == 'completed' else "❌"
                    response += f"{icon} {source}: {status}\n"
                    response += f"   🕐 {started}\n"
            else:
                response += "   Belum ada sinkronisasi\n"
            
            # Get pending documents
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM file_documents WHERE status = 'indexed'")
                pending = cursor.fetchone()[0]
            
            response += f"\n⏳ Dokumen Menunggu: {pending}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            await update.message.reply_text("❌ Error saat mengambil status.")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document upload"""
        document = update.message.document
        user = update.effective_user
        
        # Check file size (max 20MB)
        if document.file_size > 20 * 1024 * 1024:
            await update.message.reply_text("❌ File terlalu besar (max 20MB)")
            return
        
        # Check file type
        allowed_extensions = ['.pdf', '.docx', '.xlsx', '.txt', '.png', '.jpg', '.jpeg']
        file_name = document.file_name.lower()
        
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            await update.message.reply_text(
                "❌ Tipe file tidak didukung.\n"
                "✅ Yang didukung: PDF, DOCX, XLSX, TXT, PNG, JPG"
            )
            return
        
        await update.message.reply_text(f"📥 Menerima: {document.file_name}...")
        
        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # Process document
            ext = Path(file_name).suffix
            result = process_document_from_bytes(bytes(file_bytes), ext)
            
            if result:
                # Save to database
                doc_id = self.db.add_document(
                    source_id=1,  # Telegram uploads source
                    file_name=document.file_name,
                    file_path=f"telegram/{document.file_name}",
                    file_size=document.file_size,
                    mime_type=document.mime_type,
                    extension=ext
                )
                
                # Save content
                self.db.add_document_content(
                    document_id=doc_id,
                    extracted_text=result.text[:5000],  # Limit for now
                    extraction_method=result.engine,
                    ocr_confidence=result.confidence
                )
                
                response = f"✅ *Dokumen Berhasil Diupload*\n\n"
                response += f"📄 {document.file_name}\n"
                response += f"📝 Engine: {result.engine}\n"
                response += f"👁️ Confidence: {result.confidence}\n"
                response += f"📊 Pages: {result.page_count}\n\n"
                response += f"📝 *Preview:*\n{result.text[:300]}..."
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Gagal memproses dokumen.")
                
        except Exception as e:
            logger.error(f"Upload error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        # Handle different callback data
        if query.data.startswith("doc_"):
            doc_id = query.data.split("_")[1]
            await self.show_document_details(query, doc_id)
    
    async def show_document_details(self, query, doc_id: str):
        """Show document details"""
        try:
            doc = self.db.get_document_by_id(int(doc_id))
            if not doc:
                await query.edit_message_text("❌ Dokumen tidak ditemukan.")
                return
            
            content = self.db.get_document_content(int(doc_id))
            labels = self.db.get_document_labels(int(doc_id))
            
            response = f"📄 *{doc['file_name']}*\n\n"
            response += f"📁 Kategori: {doc.get('category', '-')}\n"
            response += f"📍 Source: {doc.get('source_id', '-')}\n"
            response += f"📅 Indexed: {doc['indexed_at'][:10]}\n\n"
            
            if labels:
                response += "🏷️ *Label:*\n"
                for label in labels:
                    response += f"  • {label['label_type']}: {label['label_value']}\n"
            
            if content:
                text = content.get('extracted_text', '')
                response += f"\n📝 *Konten (preview):*\n{text[:500]}..."
            
            await query.edit_message_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Detail error: {e}")
            await query.edit_message_text("❌ Error.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ""Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")


def process_document_from_bytes(file_bytes: bytes, ext: str):
    """Process document from bytes"""
    import tempfile
    from document_management.processors.ocr_engine import OCREngine, TextExtractor
    
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
    
    try:
        from document_management.processors.ocr_engine import process_document
        return process_document(tmp_path, use_ocr=True)
    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    """Run the bot"""
    bot = DocumentBot()
    
    if not bot.token:
        print("❌ Please set TELEGRAM_BOT_TOKEN environment variable")
        print("   Example: export TELEGRAM_BOT_TOKEN='your_token_here'")
        sys.exit(1)
    
    print("🚀 Starting Document Management Bot...")
    bot.run()


if __name__ == "__main__":
    main()