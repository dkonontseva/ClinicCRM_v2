from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response

from clinicApp.app.api.auth.auth import authenticate_user, get_password_hash, create_access_token
from clinicApp.app.api.auth.dao import UsersDAO
from clinicApp.app.api.auth.dependencies import get_current_user, get_current_admin_user
from clinicApp.app.models.models import Users
from clinicApp.app.schemas.schemas import UserSchema, UserAuthSchema

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post("/register/")
async def register_user(user_data: UserSchema) -> dict:
    user = await UsersDAO.find_one_or_none(login=user_data.login)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь уже существует'
        )
    user_dict = user_data.dict()
    user_dict['password'] = get_password_hash(user_data.password)
    await UsersDAO.add(**user_dict)
    return {'message': 'Вы успешно зарегистрированы!'}

@router.post("/login/")
async def auth_user(response: Response, user_data: UserAuthSchema):
    check = await authenticate_user(login=user_data.login, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверная почта или пароль')
    access_token = create_access_token({"sub": str(check._id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': None}

# @router.get("/me/")
# async def get_me(user_data: Users = Depends(get_current_user)):
#     return user_data

@router.get("/all_users/")
async def get_all_users(user_data: Users = Depends(get_current_admin_user)):
    return await UsersDAO.find_all()

@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}