# api/utils/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from api.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    # truncate to 72 bytes for bcrypt
    safe_password = password.encode("utf-8")[:72]
    return pwd_context.hash(safe_password)

def verify_password(plain: str, hashed: str) -> bool:
    safe_plain = plain.encode("utf-8")[:72]
    return pwd_context.verify(safe_plain, hashed)

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload  # contains "sub" and "exp"
    except JWTError:
        return None
