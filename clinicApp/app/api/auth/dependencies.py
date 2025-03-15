import hashlib
import hmac
import base64
import json
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, status, Depends
from clinicApp.app.api.auth.dao import UsersDAO
from clinicApp.app.core.config import get_auth_data
from clinicApp.app.models.models import Users


def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token


def decode_token(token: str):
    auth_data = get_auth_data()
    secret_key = auth_data['secret_key'].encode()
    header, payload, signature = token.split('.')

    # Проверка подписи
    message = f"{header}.{payload}".encode()
    expected_signature = base64.urlsafe_b64encode(hmac.new(secret_key, message, hashlib.sha256).digest()).rstrip(b'=')

    if expected_signature.decode() != signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен не валидный!')

    payload_json = base64.urlsafe_b64decode(payload + "==").decode()
    return json.loads(payload_json)


async def get_current_user(token: str = Depends(get_token)):
    payload = decode_token(token)

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен истек')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не найден ID пользователя')

    user = await UsersDAO.find_one_or_none_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')

    return user

async def get_current_admin_user(current_user: Users = Depends(get_current_user)):
    if current_user.role_id == 3:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав!')
