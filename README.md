# Project Transparency - %スコアリングシステム

プロジェクトの透明性を可視化する主観的評価システムのMVP

## 🚀 本番環境

- **フロントエンド**: https://project-transparency.vercel.app (Vercel)
- **バックエンドAPI**: https://project-transparency-api.onrender.com (Render)
- **APIドキュメント**: https://project-transparency-api.onrender.com/docs

## 概要

このシステムは、プロジェクトメンバーが「このプロジェクトは何%ドキュメント化されているか」を主観的に評価し、チーム全体の認識を可視化するツールです。

### 主な特徴

- **JWT認証**: セキュアなユーザー認証とセッション管理
- **データ所有権**: ユーザーごとに独立したプロジェクト管理
- 役職による重み付け評価（PL×3, PM×2, Member×1）
- スコア履歴の完全保存
- リアルタイムでのダッシュボード更新
- 直感的なスライダーUI
- レスポンシブデザイン
- クラウドデプロイ対応（Vercel + Render + PostgreSQL）

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
- **FastAPI**: Python製の高速Webフレームワーク
- **SQLAlchemy**: ORM（Object-Relational Mapping）
- **PostgreSQL**: 本番環境データベース（Render PostgreSQL）
- **SQLite**: ローカル開発用データベース
- **Pydantic**: データバリデーション
- **uvicorn**: ASGIサーバー
- **psycopg2-binary**: PostgreSQL接続ドライバ
- **python-jose**: JWT認証（HS256アルゴリズム）
- **passlib + bcrypt**: パスワードハッシュ化

### フロントエンド
- **Next.js 14**: App Router使用
- **TypeScript**: 型安全な開発
- **Tailwind CSS**: ユーティリティファーストCSS
- **Recharts**: データビジュアライゼーション
- **axios**: HTTP クライアント（インターセプター使用）
- **JWT**: トークンベース認証
- **LocalStorage**: トークン永続化

### インフラ
- **Vercel**: フロントエンドホスティング
- **Render**: バックエンドAPI & PostgreSQLホスティング
- **GitHub**: ソースコード管理 & CI/CD

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

# 環境変数の設定（JWT用シークレットキー）
openssl rand -hex 32 > .env
echo "SECRET_KEY=$(cat .env)" > .env

# サーバーの起動
uvicorn app.main:app --reload
```

バックエンドは `http://localhost:8000` で起動します。
APIドキュメント: `http://localhost:8000/docs`

**重要**: `.env`ファイルに`SECRET_KEY`の設定が必須です。

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

## デプロイ

### 本番環境アーキテクチャ

```
┌─────────────────────┐
│   Vercel            │
│   (Frontend)        │
│   Next.js App       │
└──────────┬──────────┘
           │ HTTPS
           ↓
┌─────────────────────┐
│   Render            │
│   (Backend)         │
│   FastAPI + uvicorn │
└──────────┬──────────┘
           │ Internal
           ↓
┌─────────────────────┐
│   Render PostgreSQL │
│   (Database)        │
└─────────────────────┘
```

### バックエンド（Render）

1. **PostgreSQLデータベースの作成**
   - Renderダッシュボードで"New PostgreSQL"を選択
   - Database名: `project-transparency-db`
   - Region: Oregon (US West)

2. **Web Serviceの作成**
   - Repository: GitHub連携
   - Branch: `main`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **環境変数の設定**
   ```
   DATABASE_URL=<PostgreSQL Internal Database URL>
   SECRET_KEY=<openssl rand -hex 32で生成した秘密鍵>
   ```

   **重要**: ローカル開発環境とは異なる秘密鍵を使用してください。

4. **自動デプロイ**
   - Gitにpushすると自動的にデプロイされます

詳細な手順は `backend/DEPLOYMENT_REPORT.md` を参照してください。

### フロントエンド（Vercel）

1. **Vercelプロジェクトの作成**
   - GitHub repositoryを連携
   - Framework Preset: Next.js
   - Root Directory: `frontend`

2. **環境変数の設定**
   ```
   NEXT_PUBLIC_API_URL=https://project-transparency-api.onrender.com
   ```

3. **自動デプロイ**
   - mainブランチへのpushで自動デプロイ
   - プレビューデプロイ: Pull Request作成時

## 使い方

### 1. ユーザー登録とログイン

**初回アクセス時**:
1. アプリケーションにアクセスするとログイン画面が表示されます
2. 「新規登録」リンクをクリック
3. メールアドレス、パスワード（8文字以上）、名前を入力
4. 「登録」ボタンをクリック
5. 自動的にログインし、プロジェクト一覧ページへ遷移

**ログイン**:
1. ログイン画面でメールアドレスとパスワードを入力
2. 「ログイン」ボタンをクリック

**ログアウト**:
- ヘッダーの「ログアウト」ボタンをクリック

### 2. プロジェクト作成

1. プロジェクト一覧ページの「+ 新規プロジェクト」ボタンをクリック
2. プロジェクト名とドキュメントURLを入力
3. 「作成」ボタンをクリック

### 3. メンバー追加

1. プロジェクトカードをクリックしてダッシュボードを開く
2. 「+ メンバー追加」ボタンをクリック
3. 名前、役職、メールアドレス（任意）を入力
4. 「追加」ボタンをクリック

### 4. スコア入力

1. ダッシュボードから「スコア入力」ボタンをクリック
2. 各メンバーのスライダーでスコアを設定（0-100%）
3. コメント（任意）を入力
4. 「スコアを登録」ボタンをクリック

### 5. ダッシュボードで確認

- 加重平均スコア: 役職による重み付けで計算された総合スコア
- メンバー別スコア: 各メンバーの最新スコアとコメント
- スコア推移: 時系列でのスコア変化をグラフで表示

**データ所有権**: 各ユーザーは自分が作成したプロジェクトのみ表示・編集可能です。他のユーザーのデータは見えません。

## データベース設計

### テーブル構成

1. **users**: ユーザー情報
   - id, email (unique), hashed_password, name, created_at
   - 認証に使用

2. **projects**: プロジェクト情報
   - id, name, document_url, user_id (FK → users.id), created_at
   - ユーザーごとにプロジェクトを管理

3. **members**: メンバー情報
   - id, project_id (FK → projects.id), name, role, email, created_at
   - CHECK制約: role IN ('Member', 'PM', 'PL')

4. **scores**: スコアリング履歴
   - id, member_id (FK → members.id), score, comment, created_at
   - CHECK制約: score >= 0 AND score <= 100

詳細は `design/db_design.sql` を参照してください。

### リレーションシップ

```
users (1) ─── (N) projects (1) ─── (N) members (1) ─── (N) scores
```

- 1人のユーザーは複数のプロジェクトを持つ
- 1つのプロジェクトは複数のメンバーを持つ
- 1人のメンバーは複数のスコア履歴を持つ

## API設計

### 認証エンドポイント

- `POST /api/auth/register` - 新規ユーザー登録
- `POST /api/auth/login` - ログイン
- `GET /api/auth/me` - 現在のユーザー情報取得（要認証）

### プロジェクト・メンバー・スコア（全て要認証）

- `GET /api/projects` - 自分のプロジェクト一覧
- `POST /api/projects` - プロジェクト作成
- `GET /api/projects/{id}` - プロジェクト詳細
- `POST /api/projects/{id}/members` - メンバー追加
- `GET /api/projects/{id}/members` - メンバー一覧
- `POST /api/members/{id}/scores` - スコア登録
- `GET /api/projects/{id}/dashboard` - ダッシュボードデータ

詳細は `design/api_design.md` を参照してください。

### 認証方式

全てのAPI（認証関連を除く）は**JWTトークンによる認証が必須**です：

```
Authorization: Bearer <access_token>
```

- トークン有効期限: 24時間
- トークンがない、または無効な場合: `401 Unauthorized`

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

## 認証機能

### 実装されている機能

- ✅ **JWT認証**: HS256アルゴリズムによるトークンベース認証
- ✅ **ユーザー登録**: メールアドレス、パスワード、名前で新規登録
- ✅ **ログイン**: 既存ユーザーのログイン
- ✅ **パスワードセキュリティ**: bcryptによるハッシュ化
- ✅ **トークン管理**: LocalStorageでのトークン永続化（24時間有効）
- ✅ **認証ガード**: 未ログイン時の自動リダイレクト
- ✅ **401エラー処理**: トークン無効時の自動ログアウト
- ✅ **データ所有権**: ユーザーごとに独立したプロジェクト管理

### セキュリティ対策

- パスワードは平文保存せず、bcryptでハッシュ化
- JWT秘密鍵は環境変数で管理（Git管理対象外）
- 各APIで認証チェックを実施
- ユーザーは自分のデータのみアクセス可能

詳細なエラーレポートは `docs/report/08_JWT認証実装_エラーレポート.md` を参照してください。

## MVPで実装していない機能

以下は将来的な拡張として残されています：

- メンバー削除機能
- プロジェクト編集・削除
- 通知機能
- エクスポート機能
- 高度なフィルタリング
- トークンリフレッシュ機能
- パスワードリセット機能

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
