import hashlib, hmac, os, time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET = os.getenv("SECRET_KEY", "change-me-in-production")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    return salt.hex() + ":" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000).hex()


def verify_password(pw: str, stored: str) -> bool:
    salt, digest = stored.split(":")
    check = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()
    return hmac.compare_digest(check, digest)


def make_token(user: User) -> str:
    return jwt.encode({"sub": str(user.id), "exp": time.time() + 8 * 3600}, SECRET, "HS256")


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        uid = int(jwt.decode(token, SECRET, ["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user


def require(*roles):
    def dep(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Not allowed for your role")
        return user
    return dep
