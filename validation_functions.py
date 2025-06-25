import hashlib
import os

import bcrypt
import re
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException
from dotenv import load_dotenv


load_dotenv()
key = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def create_token(agent_name: str, expire_hour: int = 48):
    from tutor import user
    try:
        expire = datetime.utcnow() + timedelta(hours=expire_hour)
        payload = {
            "sub": user["name"],
            "exp": int(expire.timestamp()),
            "id": user["_id"]
        }
        return jwt.encode(payload, key, algorithm=ALGORITHM)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token creation failed: {str(e)}")

def validate_token(token: str):
    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        return payload["sub"], payload["id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# === HELPERS ===
def hash_text(text: str) -> bytes:
    return bcrypt.hashpw(text.encode(), bcrypt.gensalt())

def is_valid_password(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must include at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must include at least one number."
    if not re.search(r"[^a-zA-Z0-9]", password):
        return False, "Password must include at least one special character."
    return True, "Password is strong."

def is_valid_email(email: str) -> tuple[bool, str]:
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(pattern, email):
        return True, "Email is valid."
    return False, "Invalid Email"

def is_valid_phone(number: str) -> tuple[bool, str]:
    if not number.isdigit():
        return False, "Phone number must be digits only."
    if len(number) < 10 or len(number) > 15:
        return False, "Phone number must be between 10 and 15 digits."
    return True, "Phone number is valid."
