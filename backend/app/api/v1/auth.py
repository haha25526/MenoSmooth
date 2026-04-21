"""
Auth Routes - Phone verification code login/register
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas import SendCodeRequest, SendCodeResponse, PhoneAuthRequest, AuthResponse, UserResponse
from app.core.security import create_access_token, create_refresh_token
from app.core.exceptions import ValidationException
from app.db.repositories.user import user_repository
from app.redis import redis_client
from app.services.sms import sms_service, TEST_ACCOUNTS

router = APIRouter()

@router.post("/send-code", response_model=SendCodeResponse)
async def send_code(request: SendCodeRequest):
    """Send SMS verification code. 测试账号：13712345678 / 1234"""
    if request.phone in TEST_ACCOUNTS:
        code = TEST_ACCOUNTS[request.phone]
    else:
        code = sms_service.generate_code(4)

    redis_key = f"sms:code:{request.phone}"
    await redis_client.setex(redis_key, 300, code)

    try:
        await sms_service.send_verification_code(request.phone, code)
    except Exception as e:
        print(f"SMS failed: {e}")

    print(f"[DEV] 验证码: {code}, 手机号: {request.phone}")
    return SendCodeResponse()

@router.post("/register/phone", response_model=AuthResponse)
async def phone_register(request: PhoneAuthRequest, db: AsyncSession = Depends(get_db)):
    """Register with phone + code"""
    is_test = request.phone in TEST_ACCOUNTS and request.code == TEST_ACCOUNTS[request.phone]
    if not is_test:
        stored = await redis_client.get(f"sms:code:{request.phone}")
        if not stored or stored != request.code:
            raise ValidationException("验证码错误或已过期")

    existing = await user_repository.get_by_phone(db, request.phone)
    if existing:
        raise ValidationException("该手机号已注册，请直接登录")

    user = await user_repository.create(db, {
        "phone": request.phone,
        "nickname": f"更年期姐妹{request.phone[-4:]}",
    })
    if not is_test:
        await redis_client.delete(f"sms:code:{request.phone}")

    return _auth_response(user)

@router.post("/login/phone", response_model=AuthResponse)
async def phone_login(request: PhoneAuthRequest, db: AsyncSession = Depends(get_db)):
    """Login with phone + code. 测试账号 13712345678/1234 自动注册"""
    is_test = request.phone in TEST_ACCOUNTS and request.code == TEST_ACCOUNTS[request.phone]
    if not is_test:
        stored = await redis_client.get(f"sms:code:{request.phone}")
        if not stored or stored != request.code:
            raise ValidationException("验证码错误或已过期")

    user = await user_repository.get_by_phone(db, request.phone)
    if not user:
        if is_test:
            user = await user_repository.create(db, {
                "phone": request.phone,
                "nickname": f"更年期姐妹{request.phone[-4:]}",
            })
        else:
            raise ValidationException("用户不存在，请先注册")

    if not is_test:
        await redis_client.delete(f"sms:code:{request.phone}")

    return _auth_response(user)

def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id), "ver": 1}),
        user=UserResponse.model_validate(user),
    )
