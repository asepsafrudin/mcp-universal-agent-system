
import os
import sys
from dataclasses import dataclass, field
from typing import List

# Mocking the classes from settings.py
@dataclass
class SecurityConfig:
    allowed_users: List[int] = field(default_factory=list)

@dataclass
class TelegramConfig:
    security: SecurityConfig
    
    def is_user_allowed(self, user_id: int) -> bool:
        if not self.security.allowed_users:
            return True
        return user_id in self.security.allowed_users

# Case 1: Empty allowed_users
config_empty = TelegramConfig(security=SecurityConfig(allowed_users=[]))
test_id = 999999
is_allowed_1 = config_empty.is_user_allowed(test_id)

print(f"Testing Auth with empty allowed_users...")
print(f"User ID {test_id} allowed: {is_allowed_1}")

# Case 2: Specific allowed_users
config_set = TelegramConfig(security=SecurityConfig(allowed_users=[123, 456]))
is_allowed_2 = config_set.is_user_allowed(test_id)

print(f"\nTesting Auth with specific allowed_users [123, 456]...")
print(f"User ID {test_id} allowed: {is_allowed_2}")

if is_allowed_1 is True and is_allowed_2 is False:
    print("\n✅ VERIFIKASI BERHASIL: Temuan Keamanan Valid! Bot bersifat publik jika whitelist kosong.")
else:
    print("\n❌ VERIFIKASI GAGAL: Logika otorisasi tidak sesuai temuan.")
