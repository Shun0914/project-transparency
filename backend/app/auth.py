from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

from .database import get_db
from .models import User
from .schemas import TokenData

# パスワードハッシュ化の設定
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# HTTPベアラートークン認証
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    パスワードを検証する
    """
    # 検証時も同様に72バイトに切り詰め
    password_bytes = plain_password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.verify(truncated_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    パスワードをハッシュ化する
    """
    # bcryptは72バイトまでしか処理できないため、明示的に制限
    # パスワードをバイト列に変換して72バイトに切り詰め
    password_bytes = password.encode('utf-8')[:72]

    # バイト列を文字列に戻す
    truncated_password = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.hash(truncated_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンを生成する
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"DEBUG: Created token with data: {data}")
    print(f"DEBUG: Token: {encoded_jwt[:50]}...")
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    JWTトークンをデコードする
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報を確認できませんでした",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"DEBUG: Decoded payload: {payload}")
        user_id = payload.get("sub")
        print(f"DEBUG: Extracted user_id: {user_id}, type: {type(user_id)}")
        if user_id is None:
            print("DEBUG: user_id is None, raising exception")
            raise credentials_exception
        # 整数に変換
        user_id = int(user_id)
        token_data = TokenData(user_id=user_id)
        print(f"DEBUG: TokenData created: {token_data}")
    except JWTError as e:
        print(f"DEBUG: JWTError occurred: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        raise credentials_exception

    return token_data


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    現在のログインユーザーを取得する（依存性注入用）
    """
    print(f"DEBUG: Received credentials: {credentials}")
    token = credentials.credentials
    print(f"DEBUG: Token received: {token[:50] if token else 'None'}...")
    token_data = decode_access_token(token)
    print(f"DEBUG: Decoded user_id: {token_data.user_id}")

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"DEBUG: Found user: {user.email}")
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    ユーザー認証を行う
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
