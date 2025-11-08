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

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. サーバーの起動

```bash
uvicorn app.main:app --reload
```

サーバーは `http://localhost:8000` で起動します。

### 3. APIドキュメント

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
│   ├── models.py            # SQLAlchemyモデル
│   ├── schemas.py           # Pydanticスキーマ
│   └── routers/
│       ├── __init__.py
│       ├── projects.py      # プロジェクト関連API
│       ├── members.py       # メンバー関連API
│       ├── scores.py        # スコアリング関連API
│       ├── dashboard.py     # ダッシュボード関連API
│       └── admin.py         # 管理用API（デモデータ投入）
├── .python-version          # Python 3.12.0を指定
├── requirements.txt         # Python依存関係
├── insert_demo_data.py      # デモデータ投入スクリプト
├── DEPLOYMENT_REPORT.md     # デプロイレポート（詳細な手順と学び）
└── README.md
```

### 重要なファイル

- **`.python-version`**: Renderで使用するPythonバージョンを指定（3.12.0）
- **`DEPLOYMENT_REPORT.md`**: PostgreSQL移行の詳細レポート
  - 発生した問題と解決策
  - 技術的な学び
  - システムアーキテクチャ
  - データベース設計
  - 今後の課題
- **`insert_demo_data.py`**: デモデータ投入スクリプト（ローカル実行用）
- **`app/routers/admin.py`**: 管理用APIエンドポイント（作成中）

## API エンドポイント

### Projects（プロジェクト管理）

- `GET /api/projects` - プロジェクト一覧
- `POST /api/projects` - プロジェクト作成
- `GET /api/projects/{id}` - プロジェクト詳細

### Members（メンバー管理）

- `POST /api/projects/{id}/members` - メンバー追加
- `GET /api/projects/{id}/members` - メンバー一覧

### Scores（スコアリング）

- `POST /api/members/{id}/scores` - スコア登録
- `GET /api/members/{id}/scores` - スコア履歴

### Dashboard（ダッシュボード）

- `GET /api/projects/{id}/dashboard` - ダッシュボードデータ

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

1. **projects**: プロジェクト情報
   - id, name, document_url, created_at

2. **members**: メンバー情報（役職含む）
   - id, project_id, name, role, email, created_at
   - CHECK制約: role IN ('Member', 'PM', 'PL')

3. **scores**: スコアリング履歴
   - id, member_id, score, comment, created_at
   - CHECK制約: score >= 0 AND score <= 100

詳細は `/design/db_design.sql` を参照してください。

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
```

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

## 開発メモ

- **CORS設定**: 本番環境のフロントエンドURLを許可
  ```python
  allow_origins=["http://localhost:3000"],
  allow_origin_regex=r"https://.*\.vercel\.app",
  ```
- **データベース**: 起動時に自動作成（`Base.metadata.create_all()`）
- **バリデーション**: Pydanticで実施
- **環境変数**: DATABASE_URLで開発/本番を自動切り替え
