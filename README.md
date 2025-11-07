# Project Transparency - %スコアリングシステム

プロジェクトの透明性を可視化する主観的評価システムのMVP

## 概要

このシステムは、プロジェクトメンバーが「このプロジェクトは何%ドキュメント化されているか」を主観的に評価し、チーム全体の認識を可視化するツールです。

### 主な特徴

- 役職による重み付け評価（PL×3, PM×2, Member×1）
- スコア履歴の完全保存
- リアルタイムでのダッシュボード更新
- 直感的なスライダーUI
- レスポンシブデザイン

## プロジェクト構成

```
project-transparency/
├── backend/           # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routers/
│   └── requirements.txt
│
├── frontend/          # Next.js
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── package.json
│
├── design/            # 設計ドキュメント
│   ├── db_design.sql
│   └── api_design.md
│
├── docs/              # プロジェクトドキュメント
└── README.md
```

## 技術スタック

### バックエンド
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- uvicorn

### フロントエンド
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Recharts
- axios

## セットアップと起動

### 前提条件

- Python 3.8+
- Node.js 18+
- npm or yarn

### 1. バックエンドのセットアップ

```bash
cd backend

# 依存関係のインストール
pip install -r requirements.txt

# サーバーの起動
uvicorn app.main:app --reload
```

バックエンドは `http://localhost:8000` で起動します。
APIドキュメント: `http://localhost:8000/docs`

### 2. フロントエンドのセットアップ

新しいターミナルウィンドウを開いて：

```bash
cd frontend

# 依存関係のインストール
npm install

# 環境変数の設定
cp .env.local.example .env.local

# 開発サーバーの起動
npm run dev
```

フロントエンドは `http://localhost:3000` で起動します。

## 使い方

### 1. プロジェクト作成

1. トップページの「+ 新規プロジェクト」ボタンをクリック
2. プロジェクト名とドキュメントURLを入力
3. 「作成」ボタンをクリック

### 2. メンバー追加

1. プロジェクトカードをクリックしてダッシュボードを開く
2. 「+ メンバー追加」ボタンをクリック
3. 名前、役職、メールアドレス（任意）を入力
4. 「追加」ボタンをクリック

### 3. スコア入力

1. ダッシュボードから「スコア入力」ボタンをクリック
2. 各メンバーのスライダーでスコアを設定（0-100%）
3. コメント（任意）を入力
4. 「スコアを登録」ボタンをクリック

### 4. ダッシュボードで確認

- 加重平均スコア: 役職による重み付けで計算された総合スコア
- メンバー別スコア: 各メンバーの最新スコアとコメント
- スコア推移: 時系列でのスコア変化をグラフで表示

## データベース設計

### テーブル構成

1. **projects**: プロジェクト情報
   - id, name, document_url, created_at

2. **members**: メンバー情報
   - id, project_id, name, role, email, created_at

3. **scores**: スコアリング履歴
   - id, member_id, score, comment, created_at

詳細は `design/db_design.sql` を参照してください。

## API設計

### 主要エンドポイント

- `GET /api/projects` - プロジェクト一覧
- `POST /api/projects` - プロジェクト作成
- `GET /api/projects/{id}` - プロジェクト詳細
- `POST /api/projects/{id}/members` - メンバー追加
- `GET /api/projects/{id}/members` - メンバー一覧
- `POST /api/members/{id}/scores` - スコア登録
- `GET /api/projects/{id}/dashboard` - ダッシュボードデータ

詳細は `design/api_design.md` を参照してください。

## 加重平均の計算

役職による重み付けでスコアを計算：

```
加重平均 = Σ(スコア × 重み) / Σ(重み)

重み:
- PL (Project Leader): 3
- PM (Project Manager): 2
- Member: 1
```

例：
- PL（重み3）: 85点
- PM（重み2）: 75点
- Member（重み1）: 70点

加重平均 = (85×3 + 75×2 + 70×1) / (3+2+1) = 78.3点

## MVPで実装していない機能

以下は将来的な拡張として残されています：

- ユーザー認証・ログイン
- メンバー削除機能
- プロジェクト編集・削除
- 通知機能
- エクスポート機能
- 高度なフィルタリング

## ディレクトリ詳細

各ディレクトリの詳細については、以下のREADMEを参照してください：

- バックエンド: `backend/README.md`
- フロントエンド: `frontend/README.md`

## ライセンス

MIT License

## 開発者向け情報

### バックエンド開発

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### フロントエンド開発

```bash
cd frontend
npm run dev
```

### ビルド

```bash
# フロントエンド
cd frontend
npm run build
npm start
```

## トラブルシューティング

### CORSエラー

バックエンドの`main.py`でCORS設定を確認してください：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    ...
)
```

### データベースエラー

SQLiteデータベースファイルを削除して再作成：

```bash
cd backend
rm project_transparency.db
uvicorn app.main:app --reload
```

### フロントエンドのビルドエラー

node_modulesを削除して再インストール：

```bash
cd frontend
rm -rf node_modules
npm install
```

## 参考資料

- FastAPI: https://fastapi.tiangolo.com/
- Next.js: https://nextjs.org/docs
- Tailwind CSS: https://tailwindcss.com/docs
- Recharts: https://recharts.org/
