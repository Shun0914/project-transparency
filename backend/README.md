# Backend - Project Transparency API

プロジェクトの透明性を可視化する%スコアリングシステムのバックエンドAPI

## 🚀 本番環境

- **API URL**: https://project-transparency-api.onrender.com
- **API Docs**: https://project-transparency-api.onrender.com/docs
- **Database**: Render PostgreSQL (Oregon Region)
- **Hosting**: Render Web Service

## 技術スタック

- **FastAPI**: Python製の高速Webフレームワーク
- **SQLAlchemy**: ORM（Object-Relational Mapping）
- **PostgreSQL**: 本番環境データベース（Render）
- **SQLite**: ローカル開発用データベース
- **Pydantic**: データバリデーション
- **uvicorn**: ASGIサーバー
- **psycopg2-binary**: PostgreSQL接続ドライバ (Python 3.12用)
- **python-jose**: JWT（JSON Web Token）処理
- **passlib**: パスワードハッシュ化（bcryptサポート）
- **bcrypt**: パスワードハッシュアルゴリズム

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、JWT用のシークレットキーを設定します：

```bash
# ランダムな秘密鍵を生成
openssl rand -hex 32

# .envファイルに追加
echo "SECRET_KEY=<生成された秘密鍵>" > .env
```

例:
```
SECRET_KEY=592b619e821fddb43955a2284ae2dad8dd37985416936ebaed25bd0b1a4b797c
```

**重要**: 本番環境では必ず異なる秘密鍵を使用し、`.env`ファイルをGit管理対象外にしてください（`.gitignore`に追加済み）。

### 3. サーバーの起動

```bash
uvicorn app.main:app --reload
```

サーバーは `http://localhost:8000` で起動します。

### 4. APIドキュメント

起動後、以下のURLでAPIドキュメントを確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## プロジェクト構造

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   ├── database.py          # データベース接続（SQLite/PostgreSQL対応）
│   ├── models.py            # SQLAlchemyモデル（User, Project, Member, Score）
│   ├── schemas.py           # Pydanticスキーマ
│   ├── auth.py              # JWT認証・パスワードハッシュ化ロジック
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # 認証API（登録、ログイン、ユーザー情報取得）
│       ├── projects.py      # プロジェクト関連API（要認証）
│       ├── members.py       # メンバー関連API（要認証）
│       ├── scores.py        # スコアリング関連API（要認証）
│       ├── dashboard.py     # ダッシュボード関連API（要認証）
│       └── admin.py         # 管理用API（デモデータ投入）
├── .env                     # 環境変数（SECRET_KEY等）※Git管理対象外
├── .python-version          # Python 3.12.0を指定
├── requirements.txt         # Python依存関係
├── insert_demo_data.py      # デモデータ投入スクリプト
├── DEPLOYMENT_REPORT.md     # デプロイレポート（詳細な手順と学び）
└── README.md
```

### 重要なファイル

- **`.env`**: 環境変数（SECRET_KEY等）。必ず設定が必要
- **`.python-version`**: Renderで使用するPythonバージョンを指定（3.12.0）
- **`app/auth.py`**: JWT認証ロジック、パスワードハッシュ化、トークン検証
- **`app/models.py`**: データベースモデル（User, Project, Member, Score）
- **`DEPLOYMENT_REPORT.md`**: PostgreSQL移行の詳細レポート
  - 発生した問題と解決策
  - 技術的な学び
  - システムアーキテクチャ
  - データベース設計
  - 今後の課題
- **`insert_demo_data.py`**: デモデータ投入スクリプト（ローカル実行用）
- **`app/routers/admin.py`**: 管理用APIエンドポイント（作成中）

## API エンドポイント

### Authentication（認証）

- `POST /api/auth/register` - 新規ユーザー登録
  - リクエスト: `{ email, password, name }`
  - レスポンス: `{ access_token, token_type }`
- `POST /api/auth/login` - ログイン
  - リクエスト: `{ email, password }`
  - レスポンス: `{ access_token, token_type }`
- `GET /api/auth/me` - 現在のログインユーザー情報取得（要認証）
  - ヘッダー: `Authorization: Bearer <token>`
  - レスポンス: `{ id, email, name, created_at }`

### Projects（プロジェクト管理）**※全て要認証**

- `GET /api/projects` - 自分のプロジェクト一覧
- `POST /api/projects` - プロジェクト作成
- `GET /api/projects/{id}` - プロジェクト詳細（自分のプロジェクトのみ）

### Members（メンバー管理）**※全て要認証**

- `POST /api/projects/{id}/members` - メンバー追加
- `GET /api/projects/{id}/members` - メンバー一覧

### Scores（スコアリング）**※全て要認証**

- `POST /api/members/{id}/scores` - スコア登録
- `GET /api/members/{id}/scores` - スコア履歴

### Dashboard（ダッシュボード）**※全て要認証**

- `GET /api/projects/{id}/dashboard` - ダッシュボードデータ

### 認証について

全てのAPI（認証関連を除く）は**JWTトークンによる認証が必須**です。リクエストヘッダーに以下を含めてください：

```
Authorization: Bearer <access_token>
```

トークンがない、または無効な場合は `401 Unauthorized` が返されます。

## 主な機能

### 加重平均スコアの計算

役職による重み付けでスコアを計算：
- PL (Project Leader): 重み 3
- PM (Project Manager): 重み 2
- Member: 重み 1

計算式:
```
weighted_avg = Σ(score × weight) / Σ(weight)
```

### スコア履歴管理

- スコアは全て履歴として保存（更新ではなく追加）
- 各メンバーの最新スコアを取得可能
- 日付ごとのタイムラインを生成

## データベース

### ローカル環境（SQLite）

SQLiteデータベース `project_transparency.db` が自動的に作成されます。

### 本番環境（PostgreSQL）

Render PostgreSQLに接続します。環境変数`DATABASE_URL`で自動的に切り替わります。

```python
# database.py内の処理
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./project_transparency.db")

# Renderの"postgres://"をSQLAlchemy形式"postgresql://"に変換
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

### テーブル構成

1. **users**: ユーザー情報
   - id, email (unique), hashed_password, name, created_at
   - 認証に使用

2. **projects**: プロジェクト情報
   - id, name, document_url, user_id (FK → users.id), created_at
   - ユーザーごとにプロジェクトを管理

3. **members**: メンバー情報（役職含む）
   - id, project_id (FK → projects.id), name, role, email, created_at
   - CHECK制約: role IN ('Member', 'PM', 'PL')

4. **scores**: スコアリング履歴
   - id, member_id (FK → members.id), score, comment, created_at
   - CHECK制約: score >= 0 AND score <= 100

詳細は `/design/db_design.sql` を参照してください。

### データの所有権

- 各ユーザーは自分が作成したプロジェクトのみアクセス可能
- プロジェクトは `user_id` で紐付けられ、他のユーザーからは見えない
- メンバーやスコアも所属プロジェクトの所有者のみがアクセス可能

## Renderへのデプロイ

### 前提条件

- Renderアカウント
- GitHubリポジトリ
- PostgreSQLデータベース（Render上に作成）

### 1. PostgreSQLデータベースの作成

```bash
# Renderダッシュボードから
- New → PostgreSQL
- Name: project-transparency-db
- Database: project_transparency_db
- User: project_transparency_db_user
- Region: Oregon (US West)
- Version: PostgreSQL 16
- Plan: Free
```

作成後、"Internal Database URL"をコピーしておきます。

### 2. Web Serviceの作成と設定

```bash
# Renderダッシュボードから
- New → Web Service
- Connect Repository: GitHub連携
- Name: project-transparency-api
- Region: Oregon (US West)
- Branch: main
- Root Directory: backend
- Runtime: Python 3
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
- Plan: Free
```

### 3. 環境変数の設定

Environment タブで以下を設定:

```
Key: DATABASE_URL
Value: <Internal Database URLをペースト>

Key: SECRET_KEY
Value: <openssl rand -hex 32で生成した秘密鍵>
```

**重要**: ローカル開発環境とは異なる秘密鍵を使用してください。

### 4. Python バージョンの指定

`.python-version` ファイルを作成:
```
3.12.0
```

**重要**: Python 3.13はpsycopg2-binary 2.9.9と互換性がないため、3.12を使用します。

### 5. デプロイの確認

```bash
# ヘルスチェック
curl https://project-transparency-api.onrender.com/

# APIドキュメント確認
open https://project-transparency-api.onrender.com/docs
```

### トラブルシューティング

詳細なトラブルシューティングと技術的な学びについては、`DEPLOYMENT_REPORT.md`を参照してください。

#### よくある問題

1. **Python 3.13互換性エラー**
   - 解決策: `.python-version`で3.12.0を指定

2. **PostgreSQL接続エラー**
   - 解決策: DATABASE_URLが正しく設定されているか確認
   - 内部接続URLを使用（External URLではない）

3. **CORS エラー**
   - 解決策: `main.py`のCORS設定にフロントエンドURLを追加

## 認証とセキュリティ

### JWT認証

- **アルゴリズム**: HS256
- **トークン有効期限**: 24時間
- **クレーム**: `sub`（ユーザーID）, `exp`（有効期限）

### パスワードセキュリティ

- **ハッシュアルゴリズム**: bcrypt（コストファクター自動調整）
- **最小パスワード長**: 8文字
- **バージョン**: bcrypt 3.2.0（passlib 1.7.4との互換性のため）

### セキュリティベストプラクティス

1. **SECRET_KEYの管理**
   - 環境変数で管理（.envファイル）
   - 本番環境では異なる秘密鍵を使用
   - Git管理対象外（.gitignoreに追加済み）

2. **パスワードの取り扱い**
   - 平文パスワードは保存しない
   - bcryptで一方向ハッシュ化
   - 72バイト制限を考慮（自動切り詰め）

3. **データアクセス制御**
   - 全APIで認証必須（認証エンドポイントを除く）
   - ユーザーは自分のデータのみアクセス可能
   - プロジェクトIDによる所有権チェック

### 実装上の注意点

- **JWT "sub"クレーム**: JWT仕様により文字列である必要があるため、`str(user.id)`で変換
- **bcrypt互換性**: bcrypt 5.x以降はpasslib 1.7.4と非互換のため、3.2.0を使用
- **email-validator**: Pydanticの`EmailStr`使用時は別途インストール必要

詳細なエラーレポートは `/docs/report/08_JWT認証実装_エラーレポート.md` を参照してください。

## 開発メモ

- **CORS設定**: 本番環境のフロントエンドURLを許可
  ```python
  allow_origins=["http://localhost:3000"],
  allow_origin_regex=r"https://.*\.vercel\.app",
  ```
- **データベース**: 起動時に自動作成（`Base.metadata.create_all()`）
- **バリデーション**: Pydanticで実施
- **環境変数**: DATABASE_URLで開発/本番を自動切り替え
- **認証**: JWTトークンベース、24時間有効
