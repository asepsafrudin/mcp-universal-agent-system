#!/usr/bin/env python3
"""
Get Chat ID from bot updates
"""

import asyncio
import os
from telegram import Bot

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

async def get_chat_id():
    """Get chat ID from recent bot updates"""
    try:
        if not BOT_TOKEN:
            print("❌ Set TELEGRAM_BOT_TOKEN terlebih dahulu.")
            return None
        bot = Bot(token=BOT_TOKEN)
        updates = await bot.get_updates()
        
        if not updates:
            print("❌ Tidak ada update ditemukan.")
            print("💡 Silakan kirim pesan ke bot @MCP_AI_Assistant_Bot terlebih dahulu.")
            print("   Buka Telegram dan kirim /start ke bot tersebut.")
            return None
        
        print(f"✅ Ditemukan {len(updates)} update:\n")
        
        chat_ids = set()
        for update in updates:
            if update.message:
                chat = update.message.chat
                user = update.message.from_user
                chat_ids.add(chat.id)
                print(f"  👤 User: {user.first_name} (@{user.username or 'no_username'})")
                print(f"  🆔 Chat ID: {chat.id}")
                print(f"  💬 Message: {update.message.text[:50] if update.message.text else '[no text]'}")
                print()
        
        if chat_ids:
            print(f"📋 Chat IDs yang tersedia: {list(chat_ids)}")
            return list(chat_ids)[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    chat_id = asyncio.run(get_chat_id())
    if chat_id:
        print(f"\n✅ Gunakan Chat ID: {chat_id}")
    else:
        print("\n⚠️  Pastikan Anda sudah chat dengan bot @MCP_AI_Assistant_Bot")
