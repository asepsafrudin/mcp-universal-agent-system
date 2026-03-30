#!/usr/bin/env python3
"""
Monitor Lalu Lintas Chat Telegram Real-Time
Mengawasi pesan masuk ke bot @Asep_mcp_bot
"""

import asyncio
import json
import os
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

async def monitor_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor setiap pesan yang masuk"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if update.message:
        chat = update.message.chat
        user = update.message.from_user
        
        # Format output
        print(f"\n{'='*60}")
        print(f"📨 PESAN MASUK - {timestamp}")
        print(f"{'='*60}")
        print(f"👤 User: {user.first_name} {user.last_name or ''} (@{user.username or 'no_username'})")
        print(f"🆔 User ID: {user.id}")
        print(f"💬 Chat ID: {chat.id}")
        print(f"📍 Chat Type: {chat.type}")
        print(f"📝 Pesan: {update.message.text or '[non-text]'}")
        
        if update.message.entities:
            print(f"🔗 Entities: {[e.type for e in update.message.entities]}")
        
        print(f"{'='*60}\n")
        
        # Simpan ke log file
        log_entry = {
            'timestamp': timestamp,
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'chat_id': chat.id,
            'chat_type': chat.type,
            'message': update.message.text
        }
        
        with open('telegram_chat_log.jsonl', 'a') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

async def monitor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor callback queries (button clicks)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if update.callback_query:
        user = update.callback_query.from_user
        
        print(f"\n{'='*60}")
        print(f"🔘 CALLBACK QUERY - {timestamp}")
        print(f"{'='*60}")
        print(f"👤 User: {user.first_name} (@{user.username or 'no_username'})")
        print(f"🆔 User ID: {user.id}")
        print(f"📊 Data: {update.callback_query.data}")
        print(f"{'='*60}\n")

def main():
    """Main monitoring loop"""
    if not BOT_TOKEN:
        print("❌ Set TELEGRAM_BOT_TOKEN terlebih dahulu.")
        return

    print("🚀 Memulai monitor chat Telegram...")
    print(f"🤖 Bot: @Asep_mcp_bot")
    print(f"⏰ Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📝 Log: telegram_chat_log.jsonl")
    print(f"\n💡 Tekan Ctrl+C untuk berhenti\n")
    
    # Buat application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Tambahkan handlers
    application.add_handler(MessageHandler(filters.ALL, monitor_message))
    application.add_handler(MessageHandler(filters.COMMAND, monitor_message))
    
    # Jalankan polling
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query', 'edited_message']
    )

if __name__ == "__main__":
    main()
