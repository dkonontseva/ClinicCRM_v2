import hashlib
import hmac

import jwt
from pydantic import EmailStr
from clinicApp.app.api.auth.dao import UsersDAO
from datetime import datetime, timezone, timedelta

from clinicApp.app.core.config import get_auth_data


SALT = get_auth_data()['salt']


def get_password_hash(password: str) -> str:
    salted_password = password.encode() + SALT.encode()
    return hashlib.sha256(salted_password).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(get_password_hash(plain_password), hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    token = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return token

async def authenticate_user(login: EmailStr, password: str):
    user = await UsersDAO.find_one_or_none(login=login)
    if not user or not verify_password(password, user.password):
        return None
    return user