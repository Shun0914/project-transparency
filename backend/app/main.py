from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import projects, members, scores, dashboard

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

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
