# Backend - Project Transparency API

プロジェクトの透明性を可視化する%スコアリングシステムのバックエンドAPI

## 技術スタック

- **FastAPI**: Python製の高速Webフレームワーク
- **SQLAlchemy**: ORM
- **SQLite**: データベース
- **Pydantic**: バリデーション
- **uvicorn**: ASGIサーバー

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
│   ├── main.py           # FastAPIアプリケーション
│   ├── database.py       # データベース接続
│   ├── models.py         # SQLAlchemyモデル
│   ├── schemas.py        # Pydanticスキーマ
│   └── routers/
│       ├── __init__.py
│       ├── projects.py   # プロジェクト関連API
│       ├── members.py    # メンバー関連API
│       ├── scores.py     # スコアリング関連API
│       └── dashboard.py  # ダッシュボード関連API
├── requirements.txt
└── README.md
```

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

SQLiteデータベース `project_transparency.db` が自動的に作成されます。

### テーブル構成

1. **projects**: プロジェクト情報
2. **members**: メンバー情報（役職含む）
3. **scores**: スコアリング履歴

詳細は `/design/db_design.sql` を参照してください。

## 開発メモ

- CORS設定: フロントエンド（http://localhost:3000）からのアクセスを許可
- データベースは起動時に自動作成
- バリデーションはPydanticで実施
