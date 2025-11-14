from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import projects, members, scores, dashboard, auth
import os

# データベーステーブルの作成
# RESET_DB=trueの場合、既存テーブルを削除して再作成（マイグレーション用）
if os.getenv("RESET_DB", "false").lower() == "true":
    print("⚠️  RESET_DB=true detected. Dropping all tables and recreating...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped.")

Base.metadata.create_all(bind=engine)
print("✅ Database tables created/verified.")

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Project Transparency API",
    description="プロジェクトの透明性を可視化する%スコアリングシステム",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(members.router, prefix="/api", tags=["members"])
app.include_router(scores.router, prefix="/api", tags=["scores"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])

# ヘルスチェック
@app.get("/")
def read_root():
    return {
        "message": "Project Transparency API",
        "status": "running",
        "docs": "/docs"
    }
