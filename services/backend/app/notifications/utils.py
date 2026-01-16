from typing import Optional, Any
import binascii
import struct
import time
import hmac
import hashlib
import base64
from django.conf import settings

# Structure: User ID (Unsigned Int, 4 bytes) + Timestamp (Unsigned Int, 4 bytes)
PACK_FORMAT = ">II"
PACK_SIZE = struct.calcsize(PACK_FORMAT)  # 8 bytes


def generate_telegram_link(user: Any) -> str:
    """
    Creates a compact, signed, time-sensitive token.
    Format: [User ID (4b)[Time (4b)][Signature (20b)]] -> Base64
    """
    secret = settings.SECRET_KEY.encode()
    now = int(time.time())

    # 1. Pack the data into binary
    # We enforece I (Integer) for user_id.
    payload = struct.pack(PACK_FORMAT, user.id, now)

    signature = hmac.new(secret, payload, hashlib.sha256).digest()

    signature_truncated = signature[:20]

    final_binary = payload + signature_truncated

    token = base64.urlsafe_b64encode(final_binary).decode().rstrip("=")

    bot_name = settings.TELEGRAM_BOT_NAME
    return f"https://t.me/{bot_name}?start={token}"


def verify_telegram_token(token: str, max_age: int = 600) -> Optional[int]:
    """
    Decodes the token, verifies signature, and checks expiration.
    Returns user_id or None.
    """
    try:
        secret = settings.SECRET_KEY.encode()

        # 1. Decode Base64 (Add back padding if needed)
        padding = "=" * (4 - len(token) % 4)
        binary_data = base64.urlsafe_b64decode(token + padding)

        # 2. Length Check (Must be at least 8 bytes data + 1 byte sig)
        if len(binary_data) < PACK_SIZE + 1:
            return None

        # 3. Split Data and Signature
        payload = binary_data[:PACK_SIZE]
        received_sig = binary_data[PACK_SIZE:]

        # 4. Unpack Data
        user_id, timestamp = struct.unpack(PACK_FORMAT, payload)

        # 5. Check Expiration FIRST (Save CPU on crypto if expired)
        if int(time.time()) - timestamp > max_age:
            print(f"Token expired. Age: {int(time.time()) - timestamp}s")
            return None

        # 6. Verify Signature
        expected_sig = hmac.new(secret, payload, hashlib.sha256).digest()[:20]

        # compare_digest prevents timing attacks
        if not hmac.compare_digest(received_sig, expected_sig):
            return None

        return user_id

    except (binascii.Error, struct.error, Exception):
        return None
