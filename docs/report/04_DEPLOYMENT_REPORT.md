# Project Transparency API - Render PostgreSQL移行レポート

**作成日**: 2025-11-08
**作業者**: Claude Code
**プロジェクト**: Project Transparency MVP

---

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [実施した作業](#実施した作業)
3. [発生した問題と解決策](#発生した問題と解決策)
4. [技術的な学び](#技術的な学び)
5. [システムアーキテクチャ](#システムアーキテクチャ)
6. [データベース設計](#データベース設計)
7. [環境構築手順](#環境構築手順)
8. [今後の課題](#今後の課題)

---

## プロジェクト概要

### 目的
- RenderにデプロイされたProject Transparency APIをSQLiteからPostgreSQLに移行
- 永続的なデータストレージの実現
- デモデータの投入

### 初期状態
- **デプロイ環境**: Render Web Service (Free tier)
- **データベース**: SQLite（一時ファイルシステム）
- **問題**: サーバー再起動時にデータが消失

### 最終状態
- **デプロイ環境**: Render Web Service (Free tier)
- **データベース**: Render PostgreSQL (Free tier)
- **状態**: 正常稼働中
- **URL**: https://project-transparency-api.onrender.com

---

## 実施した作業

### 1. Render PostgreSQLデータベースの作成

```bash
データベース名: project-transparency-db
プラン: free
リージョン: oregon
バージョン: PostgreSQL 16
データベースID: dpg-d47qe6chg0os73fsd11g-a
```

**作成コマンド（MCP経由）**:
```python
mcp__render__create_postgres(
    name="project-transparency-db",
    plan="free",
    region="oregon",
    version=16
)
```

### 2. アプリケーションコードの修正

#### 2.1 database.pyの更新

**変更前** (`backend/app/database.py`):
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./project_transparency.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
```

**変更後**:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 環境変数からDATABASE_URLを取得、なければSQLiteを使用
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./project_transparency.db"
)

# PostgreSQL用のURLを調整（Renderは"postgres://"を返すが、SQLAlchemyは"postgresql://"が必要）
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# エンジンの作成
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
)
```

**重要なポイント**:
- 環境変数`DATABASE_URL`でデータベースを切り替え可能に
- ローカル開発ではSQLite、本番環境ではPostgreSQLを使用
- RenderのURL形式(`postgres://`)をSQLAlchemy形式(`postgresql://`)に変換

#### 2.2 requirements.txtの更新

**追加した依存関係**:
```txt
psycopg2-binary==2.9.9
```

`psycopg2-binary`はPostgreSQLへの接続に必要なPythonドライバです。

#### 2.3 Pythonバージョンの指定

**作成ファイル** (`backend/.python-version`):
```
3.12.0
```

**理由**: Python 3.13はpsycopg2-binary 2.9.9と互換性がないため、Python 3.12を明示的に指定。

### 3. Render環境変数の設定

```bash
環境変数名: DATABASE_URL
値: postgresql://project_transparency_db_user:2sS5qmRRbQEXO5L2M4UnzPR0fYYv4bfs@dpg-d47qe6chg0os73fsd11g-a.oregon-postgres.render.com/project_transparency_db
```

**設定方法**:
```python
mcp__render__update_environment_variables(
    serviceId="srv-d47puoidbo4c73fc7kr0",
    envVars=[{"key": "DATABASE_URL", "value": "..."}]
)
```

### 4. デプロイとテスト

**Git操作**:
```bash
git add backend/app/database.py backend/requirements.txt backend/.python-version backend/insert_demo_data.py
git commit -m "Add PostgreSQL support for Render deployment"
git push origin main
```

**デプロイ履歴**:
1. `421d0ec` - PostgreSQL対応コードの追加 → 失敗（Python 3.13互換性問題）
2. `bf8f5d4` - Python 3.12指定 → 失敗（パスワード認証エラー）
3. 環境変数修正 → 成功 ✅

---

## 発生した問題と解決策

### 問題1: データの永続化

**問題**:
```
Renderの一時ファイルシステムにSQLiteデータベースを保存
→ サーバー再起動時にデータが全て消失
```

**根本原因**:
- Render Free tierは一時的なファイルシステムを使用
- コンテナの再起動やデプロイ時にファイルが削除される

**解決策**:
- PostgreSQLデータベースへの移行
- Renderが提供する永続的なPostgreSQLストレージを使用

**学び**:
- クラウド環境では、アプリケーションとデータストレージを分離する設計が重要
- ステートレスなアプリケーション設計の必要性

---

### 問題2: Python 3.13とpsycopg2の互換性

**エラーログ**:
```
ImportError: /opt/render/project/src/.venv/lib/python3.13/site-packages/psycopg2/_psycopg.cpython-313-x86_64-linux-gnu.so: undefined symbol: _PyInterpreterState_Get
```

**根本原因**:
- Renderはデフォルトで最新のPython 3.13.4を使用
- psycopg2-binary 2.9.9はPython 3.13をサポートしていない
- C拡張モジュールのABI（Application Binary Interface）の非互換性

**解決策**:
`.python-version`ファイルを作成してPython 3.12を指定:
```
3.12.0
```

**技術的背景**:
- Python 3.13では内部APIが変更され、古いC拡張が動作しなくなった
- psycopg2-binaryは事前コンパイル済みバイナリを含むため、特定のPythonバージョンに依存
- 最新版のpsycopg2-binary（2.9.10以降）ではPython 3.13がサポートされる予定

**学び**:
- パッケージのバージョン互換性を事前に確認する重要性
- 本番環境のPythonバージョンを明示的に管理する必要性
- C拡張を含むパッケージは特に互換性に注意

---

### 問題3: PostgreSQL接続認証エラー

**エラーログ**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
connection to server at "dpg-d47qe6chg0os73fsd11g-a" (10.215.182.241), port 5432 failed:
FATAL: password authentication failed for user "project_transparency_db_user"
```

**根本原因**:
初回の環境変数設定時、プレースホルダーのパスワードを使用:
```python
"postgresql://project_transparency_db_user:password@dpg-d47qe6chg0os73fsd11g-a/project_transparency_db"
```

**解決策**:
Renderダッシュボードから正しいInternal Database URLを取得:
```
postgresql://project_transparency_db_user:2sS5qmRRbQEXO5L2M4UnzPR0fYYv4bfs@dpg-d47qe6chg0os73fsd11g-a.oregon-postgres.render.com/project_transparency_db
```

**学び**:
- データベース接続情報は機密情報として適切に管理
- Renderのダッシュボードから提供される接続情報を正確に使用
- 環境変数の値は慎重に設定し、テスト実行で検証

---

### 問題4: 外部からのPostgreSQL接続制限

**エラーログ**:
```
psycopg2.OperationalError: connection to server at "dpg-d47qe6chg0os73fsd11g-a.oregon-postgres.render.com" (35.227.164.209), port 5432 failed:
SSL connection has been closed unexpectedly
```

**根本原因**:
- Render Free tierのPostgreSQLは外部からの直接接続を制限
- セキュリティのため、同一リージョン内のRenderサービスからのみ接続可能

**試みた解決策**:
ローカルからデモデータ投入スクリプトを実行 → 失敗

**代替アプローチ**（実装途中）:
1. デモデータ投入用のAPIエンドポイントを作成
2. デプロイ後にAPIを呼び出してデータを投入

```python
# backend/app/routers/admin.py
@router.post("/seed-demo-data")
def seed_demo_data(db: Session = Depends(get_db)):
    # デモデータを投入
    ...
```

**学び**:
- クラウドデータベースのネットワークセキュリティポリシーを理解
- Free tierの制限事項を事前に確認
- データ投入方法を柔軟に設計（CLI、API、管理画面など）

---

## 技術的な学び

### 1. SQLAlchemyのデータベース抽象化

**利点**:
```python
# 同じコードで複数のデータベースをサポート
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
```

- SQLite、PostgreSQL、MySQLなど異なるデータベースを同じコードで扱える
- データベース固有の設定は`connect_args`で管理
- ORMレイヤーでSQL方言の違いを吸収

**実装パターン**:
```python
# SQLite固有の設定
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}
```

### 2. 環境変数による設定管理

**12-Factor App原則**:
- コードと設定を分離
- 環境ごとに異なる設定をコードの変更なしで適用

**実装例**:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./project_transparency.db")
```

**利点**:
- 開発環境: SQLite（軽量、セットアップ不要）
- 本番環境: PostgreSQL（永続化、スケーラビリティ）
- 機密情報（パスワード）をコードに含めない

### 3. RenderのURL形式とSQLAlchemyの互換性

**問題**:
Renderは`postgres://`プロトコルを使用するが、SQLAlchemy 1.4+は`postgresql://`を要求

**解決**:
```python
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

**背景**:
- PostgreSQLの公式URLスキームは`postgres://`
- SQLAlchemy 1.4以降、より明示的な`postgresql://`を推奨
- Heroku、Renderなどのプラットフォームは古い形式を使用
- psycopg2ドライバを明示するため`postgresql://`が必要

### 4. Pythonパッケージの依存関係管理

**psycopg2 vs psycopg2-binary**:

| 項目 | psycopg2 | psycopg2-binary |
|------|----------|-----------------|
| インストール | 要PostgreSQLクライアント | 不要（バンドル済み） |
| サイズ | 小 | 大 |
| 推奨環境 | 本番環境 | 開発環境 |
| Python互換性 | 高 | バージョン依存 |

**選択理由**:
- Render環境でビルドツールのセットアップを回避
- デプロイ時間の短縮
- Free tierのリソース制約を考慮

### 5. データベーステーブルの自動作成

```python
# app/main.py
Base.metadata.create_all(bind=engine)
```

**動作**:
- アプリケーション起動時にテーブルを自動作成
- `models.py`で定義されたモデルからDDLを生成
- 既存テーブルは変更しない（べき等性）

**利点**:
- マイグレーションスクリプト不要（初期段階）
- 開発環境のセットアップが簡単

**制限**:
- スキーマ変更の履歴管理不可
- 本格的な運用ではAlembicなどのマイグレーションツールが必要

---

## システムアーキテクチャ

### アプリケーション構成

```
┌─────────────────────────────────────────────┐
│         Vercel (Frontend)                   │
│  Next.js Application                        │
│  https://project-transparency.vercel.app    │
└─────────────────┬───────────────────────────┘
                  │ HTTPS API Calls
                  ↓
┌────────────────────────────────────────────┐
│      Render Web Service (Backend)          │
│  FastAPI Application                       │
│  https://project-transparency-api.         │
│  onrender.com                              │
│                                            │
│  ┌─────────────────────────────────┐       │
│  │  app/                           │       │
│  │  ├── main.py      (Entry)       │       │
│  │  ├── database.py  (DB Config)   │       │
│  │  ├── models.py    (ORM Models)  │       │
│  │  ├── schemas.py   (Pydantic)    │       │
│  │  └── routers/                   │       │
│  │      ├── projects.py            │       │
│  │      ├── members.py             │       │
│  │      ├── scores.py              │       │
│  │      └── dashboard.py           │       │
│  └─────────────────────────────────┘       │
└─────────────────┬──────────────────────────┘
                  │ PostgreSQL Wire Protocol
                  │ (Internal Network)
                  ↓
┌────────────────────────────────────────────┐
│   Render PostgreSQL Database               │
│   project-transparency-db                  │
│                                            │
│   ┌─────────────────────────────────┐      │
│   │  Tables:                        │      │
│   │  - projects                     │      │
│   │  - members                      │      │
│   │  - scores                       │      │
│   └─────────────────────────────────┘      │
└────────────────────────────────────────────┘
```

### デプロイフロー

```
┌──────────────┐
│   GitHub     │
│  Repository  │
└──────┬───────┘
       │ git push
       ↓
┌──────────────────────────────────────┐
│   Render Auto-Deploy                 │
│   1. Clone repository                │
│   2. Install Python 3.12             │
│   3. pip install -r requirements.txt │
│   4. Build application               │
│   5. Start: uvicorn app.main:app     │
└──────┬───────────────────────────────┘
       │ Health Check
       ↓
┌──────────────────────────────────────┐
│   Live Service                       │
│   https://project-transparency-api   │
│   .onrender.com                      │
└──────────────────────────────────────┘
```

### ネットワーク構成

```
Internet
   │
   ↓
[Render Load Balancer]
   │
   ├→ [Web Service Instance] ←─┐
   │   (Oregon Region)          │
   │                            │ Internal Network
   └→ [PostgreSQL Instance] ←──┘ (Private)
      (Oregon Region)
```

**重要なポイント**:
- Web ServiceとPostgreSQLは同一リージョン（Oregon）に配置
- Internal Database URLで内部ネットワーク経由で接続
- External Database URLは外部からの接続用（Free tierでは制限あり）

---

## データベース設計

### ERD (Entity Relationship Diagram)

```
┌─────────────────────┐
│      projects       │
│─────────────────────│
│ id (PK)             │
│ name                │
│ document_url        │
│ created_at          │
└──────────┬──────────┘
           │
           │ 1
           │
           │ N
┌──────────┴──────────┐
│      members        │
│─────────────────────│
│ id (PK)             │
│ project_id (FK)     │───→ projects.id
│ name                │
│ role                │
│ email               │
│ created_at          │
└──────────┬──────────┘
           │
           │ 1
           │
           │ N
┌──────────┴──────────┐
│      scores         │
│─────────────────────│
│ id (PK)             │
│ member_id (FK)      │───→ members.id
│ score               │
│ comment             │
│ created_at          │
└─────────────────────┘
```

### テーブル定義

#### projects テーブル

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    document_url VARCHAR NOT NULL,
    created_at VARCHAR DEFAULT (datetime('now'))
);
CREATE INDEX idx_projects_id ON projects(id);
```

**カラム説明**:
- `id`: 主キー（自動採番）
- `name`: プロジェクト名
- `document_url`: プロジェクト関連ドキュメントのURL
- `created_at`: 作成日時（ISO 8601形式の文字列）

#### members テーブル

```sql
CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    email VARCHAR,
    created_at VARCHAR DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CHECK (role IN ('Member', 'PM', 'PL'))
);
CREATE INDEX idx_members_project_id ON members(project_id);
```

**カラム説明**:
- `id`: 主キー（自動採番）
- `project_id`: 外部キー → projects.id
- `name`: メンバー名
- `role`: 役割（Member / PM / PL）
- `email`: メールアドレス（オプション）
- `created_at`: 作成日時

**制約**:
- `ON DELETE CASCADE`: プロジェクト削除時に関連メンバーも削除
- `CHECK`: roleは3つの値のいずれかのみ

#### scores テーブル

```sql
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    comment TEXT,
    created_at VARCHAR DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    CHECK (score >= 0 AND score <= 100)
);
CREATE INDEX idx_scores_member_id ON scores(member_id);
CREATE INDEX idx_scores_created_at ON scores(created_at);
```

**カラム説明**:
- `id`: 主キー（自動採番）
- `member_id`: 外部キー → members.id
- `score`: スコア（0-100）
- `comment`: コメント（オプション）
- `created_at`: 評価日時

**制約**:
- `ON DELETE CASCADE`: メンバー削除時に関連スコアも削除
- `CHECK`: スコアは0-100の範囲

### インデックス戦略

**検索性能の最適化**:
```python
# models.py内のインデックス定義
__table_args__ = (
    Index("idx_members_project_id", "project_id"),
    Index("idx_scores_member_id", "member_id"),
    Index("idx_scores_created_at", "created_at"),
)
```

**効果**:
- プロジェクトごとのメンバー一覧取得が高速化
- メンバーごとのスコア履歴取得が高速化
- 時系列でのスコア検索が高速化

---

## 環境構築手順

### ローカル開発環境のセットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/Shun0914/project-transparency.git
cd project-transparency/backend

# 2. 仮想環境の作成と有効化
python3.12 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 3. 依存関係のインストール
pip install -r requirements.txt

# 4. ローカルサーバーの起動（SQLite使用）
uvicorn app.main:app --reload --port 8000

# 5. API動作確認
curl http://localhost:8000/
curl http://localhost:8000/docs  # Swagger UI
```

### Renderへのデプロイ手順

#### 1. PostgreSQLデータベースの作成

1. Renderダッシュボードにアクセス
2. "New +" → "PostgreSQL"を選択
3. 以下の情報を入力:
   - Name: `project-transparency-db`
   - Database: `project_transparency_db`
   - User: `project_transparency_db_user`
   - Region: `Oregon (US West)`
   - PostgreSQL Version: `16`
   - Plan: `Free`
4. "Create Database"をクリック
5. "Info"タブから"Internal Database URL"をコピー

#### 2. Web Serviceの環境変数設定

1. Renderダッシュボードで該当のWeb Serviceを選択
2. "Environment"タブを開く
3. 環境変数を追加:
   ```
   Key: DATABASE_URL
   Value: <コピーしたInternal Database URL>
   ```
4. "Save Changes"をクリック

#### 3. Pythonバージョンの指定

**backend/.python-version**ファイルを作成:
```
3.12.0
```

#### 4. コードのデプロイ

```bash
git add backend/app/database.py backend/requirements.txt backend/.python-version
git commit -m "Add PostgreSQL support"
git push origin main
```

Renderが自動的にデプロイを開始します。

#### 5. デプロイの確認

```bash
# ヘルスチェック
curl https://project-transparency-api.onrender.com/

# レスポンス例:
# {
#   "message": "Project Transparency API",
#   "status": "running",
#   "docs": "/docs"
# }
```

---

## 今後の課題

### 1. デモデータの投入

**現状**:
- 外部からのPostgreSQL接続制限により、ローカルスクリプトが使用不可

**解決策の選択肢**:

#### Option A: APIエンドポイント経由（推奨）
```python
# backend/app/routers/admin.py
@router.post("/api/admin/seed-demo-data")
def seed_demo_data(db: Session = Depends(get_db)):
    # デモデータを投入
    ...
```

**手順**:
1. admin.pyルーターをmain.pyに登録
2. デプロイ
3. curlでエンドポイントを呼び出し

```bash
curl -X POST https://project-transparency-api.onrender.com/api/admin/seed-demo-data
```

**利点**:
- 認証を追加して保護可能
- Webインターフェースから実行可能
- ログとエラーハンドリングが容易

#### Option B: Render Shellアクセス
Renderの有料プランではSSHアクセスが可能で、サーバー上で直接スクリプト実行できます。

#### Option C: Alembicマイグレーション
データベースマイグレーションツールでシードデータを管理。

### 2. データベースマイグレーション管理

**現状**:
- `Base.metadata.create_all()`でテーブル自動作成
- スキーマ変更の履歴管理なし

**推奨**: Alembicの導入

```bash
# インストール
pip install alembic

# 初期化
alembic init alembic

# マイグレーションファイル生成
alembic revision --autogenerate -m "Initial migration"

# 実行
alembic upgrade head
```

**利点**:
- スキーマ変更の履歴を管理
- ロールバック可能
- チームでの開発が容易

### 3. 環境変数の管理

**現状**:
- DATABASE_URLを手動で設定

**改善案**:
1. `.env.example`ファイルの作成
2. `python-dotenv`の活用
3. 機密情報の安全な管理（AWS Secrets Manager、1Passwordなど）

```python
# .env.example
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key-here
```

### 4. 監視とロギング

**実装すべき項目**:
- アプリケーションログの集約（Datadog、Sentry）
- データベースクエリのパフォーマンス監視
- エラー追跡とアラート設定
- ヘルスチェックエンドポイントの強化

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # DB接続確認
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 5. セキュリティ強化

**実装すべき対策**:
- CORS設定の厳格化
- レート制限（Rate Limiting）
- API認証（JWT、OAuth2）
- 管理用エンドポイントの保護
- SQL Injectionチェック（SQLAlchemyのORMで基本的に保護済み）

### 6. パフォーマンス最適化

**検討項目**:
- データベースコネクションプーリングの調整
- クエリの最適化（N+1問題の解決）
- キャッシュ戦略（Redis）
- CDNの活用（静的コンテンツ）

### 7. バックアップとリカバリ

**実装すべき項目**:
- 定期的なデータベースバックアップ
- バックアップからのリストア手順の文書化
- ディザスタリカバリ計画

Render PostgreSQLは自動バックアップを提供していますが、定期的なエクスポートも推奨されます。

### 8. CI/CDの改善

**現状**: GitHub pushで自動デプロイ

**改善案**:
- GitHub Actionsでテスト自動化
- デプロイ前のリンター実行（flake8、black）
- ステージング環境の構築
- カナリアリリース

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest
```

---

## まとめ

### 達成したこと
✅ RenderにPostgreSQLデータベースを作成
✅ アプリケーションをPostgreSQL対応に更新
✅ 環境変数による設定管理を実装
✅ 本番環境への正常なデプロイ
✅ データ永続化の実現

### 技術的な学び
- クラウド環境でのデータベース設計と運用
- SQLAlchemyのデータベース抽象化
- Pythonパッケージの依存関係管理
- デプロイ時のトラブルシューティング
- セキュリティとネットワーク構成の理解

### 次のステップ
1. デモデータ投入APIの実装とデプロイ
2. Alembicによるマイグレーション管理の導入
3. 監視・ロギング体制の整備
4. セキュリティ対策の強化

---

## 参考リソース

### ドキュメント
- [Render Documentation](https://render.com/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### ツール
- [Render Dashboard](https://dashboard.render.com/)
- [GitHub Repository](https://github.com/Shun0914/project-transparency)
- [API Endpoint](https://project-transparency-api.onrender.com/docs)

### トラブルシューティング
- Render ログ: Dashboard → Service → Logs
- PostgreSQL接続確認: Dashboard → Database → Connect
- 環境変数確認: Dashboard → Service → Environment

---

**作成者**: Claude Code
**最終更新**: 2025-11-08
**バージョン**: 1.0
