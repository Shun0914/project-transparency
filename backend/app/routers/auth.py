from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserLogin, UserResponse, Token
from ..auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user
)

router = APIRouter()


@router.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    新規ユーザー登録
    """
    # メールアドレスの重複チェック
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )

    # パスワードをハッシュ化してユーザーを作成
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # JWTトークンを生成して返す（subは文字列である必要がある）
    access_token = create_access_token(data={"sub": str(new_user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/auth/login", response_model=Token)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    ユーザーログイン
    """
    # 認証
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが間違っています",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWTトークンを生成して返す（subは文字列である必要がある）
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    現在のログインユーザー情報を取得
    """
    return current_user
