
import sys
import os

# Mock dependencies
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

logger = MockLogger()

def translate_disposisi(dispo_raw, sender=None):
    return {"priority": "NORMAL", "forwarded_from": "A", "forwarded_to_list": ["B"]}

def indent_hal(text, indent="     "):
    if not text: return "-"
    lines = [l.strip() for l in str(text).splitlines() if l.strip()]
    return ("\n" + indent).join(lines)

# The function to test (copied from correspondence_dashboard.py)
def format_search_results(results, query):
    if not results:
        return f"🔍 Tidak ditemukan hasil untuk: *{query}*"
    output = f"🔍 *HASIL PENCARIAN*\nInput: `{query}` ({len(results)} temuan)\n\n"
    for res in results[:10]:
        no = res.get('nomor_nd', 'N/A')
        dari = res.get('dari', 'N/A')
        hal = res.get('hal', 'N/A')
        pos = res.get('posisi', '-')
        tgl = res.get('tanggal', '?')
        badge = "📝 " if 'has_code' not in res or not res['has_code'] else "🏷️ "
        output += f"{badge}*{dari}*\n  🔢 `{no}` | 📅 `{tgl}`\n"
        output += f"📄 Hal: {indent_hal(str(hal)[:100])}\n"
        if pos and pos != '-': output += f"📍 Posisi: `{pos}`\n"
        # Decode disposisi
        dispo_raw = res.get('disposisi')
        if dispo_raw:
            info = translate_disposisi(dispo_raw, sender=dari)
            if info["priority"] != "NORMAL": output += f"🚨 *{info['priority']}*\n"
            if info["forwarded_to_list"]:
                output += f"↪️ Forwarded: {info['forwarded_from']} → {', '.join(info['forwarded_to_list'])}\n"
            output += f"📥 Arahan: _{dispo_raw}_\n"
        return output # <--- BUG: returning inside the loop

# Test data
test_results = [
    {"nomor_nd": "ND-1", "dari": "User 1", "hal": "Hal 1", "posisi": "Posisi 1", "tanggal": "2026-04-17"},
    {"nomor_nd": "ND-2", "dari": "User 2", "hal": "Hal 2", "posisi": "Posisi 2", "tanggal": "2026-04-17"},
    {"nomor_nd": "ND-3", "dari": "User 3", "hal": "Hal 3", "posisi": "Posisi 3", "tanggal": "2026-04-17"},
]

print("Testing format_search_results with 3 results...")
formatted = format_search_results(test_results, "test query")
print("--- OUTPUT START ---")
print(formatted)
print("--- OUTPUT END ---")

result_count = formatted.count("🔢")
print(f"\nJumlah item yang ditampilkan: {result_count}")

if result_count == 1 and len(test_results) > 1:
    print("\n✅ VERIFIKASI BERHASIL: Temuan Bug Valid! Fungsi berhenti setelah item pertama.")
else:
    print("\n❌ VERIFIKASI GAGAL: Fungsi menampilkan lebih dari 1 item.")
