#!/usr/bin/env python3
"""
Monitor Chat Telegram - Mode Pull (Cek Berkala)
Tidak konflik dengan MCP Server yang sedang berjalan
"""

import asyncio
import json
import time
from datetime import datetime
from telegram import Bot

# Bot configuration
BOT_TOKEN = '8242627733:AAF04tGvAB51kRxcJ4CES-QMa6yU_w1hPEw'
CHAT_ID = 1223948041

async def check_updates(bot: Bot, last_update_id: int = 0):
    """Cek update dari Telegram"""
    try:
        updates = await bot.get_updates(offset=last_update_id, limit=10)
        
        new_messages = []
        max_id = last_update_id
        
        for update in updates:
            if update.update_id > max_id:
                max_id = update.update_id
            
            if update.message:
                chat = update.message.chat
                user = update.message.from_user
                
                msg_data = {
                    'update_id': update.update_id,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'chat_id': chat.id,
                    'chat_type': chat.type,
                    'text': update.message.text,
                    'entities': [e.type for e in update.message.entities] if update.message.entities else []
                }
                new_messages.append(msg_data)
                
                # Print real-time
                print(f"\n{'='*60}")
                print(f"📨 PESAN #{update.update_id} - {msg_data['timestamp']}")
                print(f"{'='*60}")
                print(f"👤 {user.first_name} (@{user.username or 'no_username'})")
                print(f"🆔 User ID: {user.id} | 💬 Chat ID: {chat.id}")
                print(f"📝 {update.message.text or '[non-text]'}")
                print(f"{'='*60}\n")
        
        return new_messages, max_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], last_update_id

async def monitor_loop():
    """Loop monitoring"""
    bot = Bot(token=BOT_TOKEN)
    last_update_id = 0
    message_count = 0
    
    print("🚀 Monitor Telegram Chat (Mode Pull)")
    print(f"🤖 Bot: @Asep_mcp_bot")
    print(f"📊 Cek setiap 5 detik...")
    print(f"💡 Tekan Ctrl+C untuk berhenti\n")
    
    # Cek info bot
    me = await bot.get_me()
    print(f"✅ Bot aktif: @{me.username}")
    print(f"📝 Log: telegram_chat_log.jsonl\n")
    
    try:
        while True:
            messages, last_update_id = await check_updates(bot, last_update_id)
            message_count += len(messages)
            
            # Simpan ke log
            if messages:
                with open('telegram_chat_log.jsonl', 'a') as f:
                    for msg in messages:
                        f.write(json.dumps(msg, ensure_ascii=False) + '\n')
                
                print(f"📦 Total pesan: {message_count} | Last Update: {last_update_id}")
            
            # Tunggu 5 detik
            await asyncio.sleep(5)
            print(f"⏱️  {datetime.now().strftime('%H:%M:%S')} - Menunggu pesan...", end='\r')
            
    except KeyboardInterrupt:
        print(f"\n\n✅ Monitor dihentikan")
        print(f"📊 Total pesan tercatat: {message_count}")
        print(f"📝 Log tersimpan di: telegram_chat_log.jsonl")

if __name__ == "__main__":
    asyncio.run(monitor_loop())
