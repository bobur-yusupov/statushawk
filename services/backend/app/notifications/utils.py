from django.core import signing
from django.conf import settings

def generate_telegram_link(user):
    signed_str = signing.dumps(user.id, salt="telegram-connect")
    
    safe_token = signed_str.replace(":", "_")
    
    bot_name = settings.TELEGRAM_BOT_NAME
    return f"https://t.me/{bot_name}?start={safe_token}"

def verify_telegram_token(safe_token):
    try:
        signed_str = safe_token.replace("_", ":")
        
        # 2. Verify Signature
        user_id = signing.loads(signed_str, salt="telegram-connect", max_age=600)
        return user_id
    except signing.BadSignature:
        return None