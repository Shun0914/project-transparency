# Frontend - Project Transparency

プロジェクトの透明性を可視化する%スコアリングシステムのフロントエンド

## 技術スタック

- **Next.js 14**: App Router使用
- **TypeScript**: 型安全性
- **Tailwind CSS**: スタイリング
- **Recharts**: グラフ描画
- **axios**: HTTP client

## セットアップ

### 1. 依存関係のインストール

```bash
npm install
```

### 2. 環境変数の設定

`.env.local`ファイルを作成し、APIのベースURLを設定します：

```bash
cp .env.local.example .env.local
```

`.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

### 3. 開発サーバーの起動

```bash
npm run dev
```

アプリケーションは `http://localhost:3000` で起動します。

## プロジェクト構造

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # ルートレイアウト
│   │   ├── page.tsx                # プロジェクト一覧ページ
│   │   ├── globals.css             # グローバルスタイル
│   │   └── projects/
│   │       └── [id]/
│   │           ├── page.tsx        # ダッシュボードページ
│   │           └── scoring/
│   │               └── page.tsx    # スコアリングページ
│   ├── components/
│   │   ├── ProjectCard.tsx         # プロジェクトカード
│   │   ├── Dashboard.tsx           # ダッシュボード
│   │   └── ScoreChart.tsx          # スコアグラフ
│   └── lib/
│       ├── api.ts                  # APIクライアント
│       └── types.ts                # 型定義
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── README.md
```

## 主な機能

### 1. プロジェクト一覧

- プロジェクトの作成
- プロジェクト一覧の表示
- プロジェクト詳細への遷移

### 2. ダッシュボード

- 加重平均スコアの表示
- メンバー別スコア一覧
- スコア推移グラフ
- メンバー追加機能

### 3. スコアリング

- メンバーごとのスコア入力
- スライダーUIでの直感的な入力
- コメント追加機能
- リアルタイムでのダッシュボード更新

## ページ構成

### プロジェクト一覧 (`/`)

- 全プロジェクトの一覧表示
- 新規プロジェクト作成フォーム

### プロジェクトダッシュボード (`/projects/[id]`)

- 加重平均スコアの表示
- メンバー別スコア一覧
- スコア推移グラフ
- メンバー追加機能
- スコア入力ページへのリンク

### スコアリングページ (`/projects/[id]/scoring`)

- メンバーごとのスコア入力フォーム
- 0-100のスライダー入力
- コメント入力欄

## UI/UXの特徴

- **レスポンシブデザイン**: モバイル・タブレット・デスクトップに対応
- **直感的な操作**: 説明なしで使えるシンプルなUI
- **リアルタイム更新**: スコア入力後、即座にダッシュボードに反映
- **視覚的なフィードバック**: ローディング状態とエラー表示

## ビルド

```bash
npm run build
```

本番用のビルドを作成します。

## 本番環境での起動

```bash
npm start
```

ビルド後のアプリケーションを起動します。
