# プロジェクト実装指示書（Claude Code用）

## 概要
プロジェクトの透明性を可視化する「%スコアリング」システムのMVPを実装してください。
このシステムは、プロジェクトメンバーが「このプロジェクトは何%ドキュメント化されているか」を主観的に評価し、チーム全体の認識を可視化するツールです。

## プロジェクト構成

```
project-transparency/
├── backend/           # FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── projects.py
│   │       ├── members.py
│   │       ├── scores.py
│   │       └── dashboard.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/          # Next.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # プロジェクト一覧
│   │   │   └── projects/
│   │   │       └── [id]/
│   │   │           ├── page.tsx    # ダッシュボード
│   │   │           └── scoring/
│   │   │               └── page.tsx # スコアリング
│   │   ├── components/
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── ScoreChart.tsx
│   │   └── lib/
│   │       └── api.ts              # API client
│   ├── package.json
│   ├── tailwind.config.js
│   └── README.md
│
└── README.md          # プロジェクト全体のREADME
```

## 技術スタック

### バックエンド
- **FastAPI**: Python製の高速Webフレームワーク
- **SQLAlchemy**: ORM
- **SQLite**: データベース（開発用）
- **Pydantic**: バリデーション
- **uvicorn**: ASGIサーバー

### フロントエンド
- **Next.js 14**: App Router使用
- **TypeScript**: 型安全性
- **Tailwind CSS**: スタイリング
- **Recharts**: グラフ描画
- **axios**: HTTP client

## データベース設計

詳細は `design/db_design.sql` を参照してください。

### テーブル構成
1. **projects**: プロジェクト情報
2. **members**: メンバー情報（役職: Member/PM/PL）
3. **scores**: スコアリング履歴（全て保存）

### 重要な仕様
- 役職による重み付け: PL=3, PM=2, Member=1
- スコア履歴は全て保存（更新ではなく追加）
- プロジェクトに対してドキュメントURLは1つ（Confluence親ページ想定）

## API設計

詳細は `design/api_design.md` を参照してください。

### エンドポイント
- `GET /api/projects`: プロジェクト一覧
- `POST /api/projects`: プロジェクト作成
- `GET /api/projects/{id}`: プロジェクト詳細
- `POST /api/projects/{id}/members`: メンバー追加
- `GET /api/projects/{id}/members`: メンバー一覧
- `POST /api/members/{member_id}/scores`: スコア登録
- `GET /api/members/{member_id}/scores`: スコア履歴
- `GET /api/projects/{id}/dashboard`: ダッシュボードデータ（統合API）

### 重要な計算ロジック
加重平均スコアの計算:
```python
weighted_avg = Σ(score × role_weight) / Σ(role_weight)
```

## 実装の優先順位

### Phase 1: バックエンド基盤
1. プロジェクト構造のセットアップ
2. データベース接続とモデル定義
3. Pydanticスキーマ定義
4. 基本的なCRUD APIの実装

### Phase 2: フロントエンド基盤
1. Next.jsプロジェクトのセットアップ
2. Tailwind CSSの設定
3. API clientの実装
4. 基本的なルーティング

### Phase 3: 機能実装
1. プロジェクト一覧・作成機能
2. メンバー登録機能
3. スコアリング機能
4. ダッシュボード表示（加重平均、グラフ）

## 実装時の注意点

### バックエンド
- **CORS設定を忘れずに**: フロントエンドからのアクセスを許可
- **エラーハンドリング**: 適切な HTTPException を返す
- **バリデーション**: Pydanticでリクエストを検証
- **ON DELETE CASCADE**: 親レコード削除時の整合性確保

### フロントエンド
- **App Router使用**: Pages Routerではなく App Router
- **Server/Client Component**: 適切に使い分け
- **型定義**: APIレスポンスの型を定義
- **エラーハンドリング**: ローディング状態とエラー表示

### UI/UX
- **シンプルさ重視**: 複雑な機能は避ける
- **レスポンシブデザイン**: モバイルでも見やすく
- **直感的な操作**: 説明なしで使えるUI
- **リアルタイム更新**: スコア入力後、即座にダッシュボードに反映

## MVPで実装しない機能

以下は将来的な拡張として残し、MVPでは実装しません:
- ユーザー認証・ログイン
- メンバー削除機能
- プロジェクト編集・削除
- 通知機能
- エクスポート機能
- 高度なフィルタリング

## 起動方法（実装後）

### バックエンド
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### フロントエンド
```bash
cd frontend
npm install
npm run dev
```

## テストケース（実装時の動作確認）

1. **プロジェクト作成**
   - プロジェクト名「プロジェクトA」、ドキュメントURL入力
   - 作成後、プロジェクト一覧に表示される

2. **メンバー登録**
   - 3名のメンバーを登録（PL×1, PM×1, Member×1）
   - メンバー一覧に表示される

3. **スコアリング**
   - 各メンバーがスコアを入力（例: 85, 75, 70）
   - コメントは任意

4. **ダッシュボード表示**
   - 加重平均が正しく計算される（例: (85×3 + 75×2 + 70×1) / (3+2+1) = 78.3）
   - 個別スコアが表示される
   - グラフで可視化される

5. **スコア更新**
   - 同じメンバーが再度スコアを入力
   - 履歴が保存される
   - ダッシュボードが更新される

## 参考資料

- FastAPI公式ドキュメント: https://fastapi.tiangolo.com/
- Next.js公式ドキュメント: https://nextjs.org/docs
- Tailwind CSS: https://tailwindcss.com/docs
- Recharts: https://recharts.org/

## その他の要件

- **コードの可読性**: 適切なコメントと命名規則
- **エラーメッセージ**: ユーザーフレンドリーなメッセージ
- **README**: 各ディレクトリに実装内容を記載
- **環境変数**: 設定は環境変数で管理（.env.example提供）

---

以上の仕様に基づいて、フルスタックのMVPアプリケーションを実装してください。
