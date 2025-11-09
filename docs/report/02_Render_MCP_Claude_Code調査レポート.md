# Render MCP + Claude Code 技術調査レポート

## 概要

このレポートは、Render MCPサーバーとClaude Codeの連携により、AIが自律的にインフラ構築やデプロイを実行できる仕組みについて技術的に調査・分析したものです。

---

## エグゼクティブサマリー

### 何が起きたのか

**プロンプト1つで以下が自動実行された:**
1. RenderにPostgreSQLデータベースを作成
2. 環境変数を設定
3. ローカルのコードを修正（SQLite → PostgreSQL）
4. GitHubにpush
5. 自動デプロイ
6. デモデータを投入

**所要時間:** 約2分  
**従来の手作業:** 約47分  
**効率化:** 約23倍

---

## Model Context Protocol (MCP) とは

### 定義

> MCP is an open protocol that standardizes how applications provide context to LLMs. Think of MCP like a USB-C port for AI applications.

**出典:** Anthropic公式ドキュメント

### 背景

Anthropicが2024年に発表したオープンソース標準。
AIアシスタントが外部ツールやデータソースに接続するための統一規格。

### 目的

> Today, we're open-sourcing the Model Context Protocol (MCP), a new standard for connecting AI assistants to the systems where data lives, including content repositories, business tools, and development environments.

**出典:** Anthropic News

**従来の問題:**
- 各ツールごとに個別の統合が必要
- 統合コストが高い
- スケールしない

**MCPによる解決:**
- 統一された接続方法
- 一度MCPサーバーを作れば、全てのMCPクライアントから使える
- AI × ツールの連携がスケールする

---

## アーキテクチャ

### 全体構成

```
┌─────────────┐   JSON-RPC   ┌─────────────┐   HTTP/API   ┌─────────────┐
│ Claude Code │ ◄──────────► │ MCP Server  │ ◄──────────► │  External   │
│  (Client)   │              │             │              │   Service   │
└─────────────┘              └─────────────┘              └─────────────┘
     MCP Host                                                (Render API)
```

### 役割分担

**Claude Code (MCP Host):**
- ユーザーのプロンプトを解析
- 適切なMCPツールを選択
- ツールを呼び出す
- 結果をユーザーに返す

**MCP Server:**
- MCPプロトコルを実装
- 外部サービスAPIをラップ
- JSON-RPC形式で通信
- 結果を標準化して返す

**External Service:**
- Render API
- GitHub API
- Slack API
- など

---

## 通信プロトコル

### JSON-RPC 2.0

MCPは JSON-RPC 2.0 を使用してクライアントとサーバー間で通信します。

### リクエスト形式

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "tools/call",
  "params": {
    "name": "create_postgres",
    "arguments": {
      "name": "project_transparency_db",
      "plan": "free",
      "region": "oregon"
    }
  }
}
```

### レスポンス形式（成功）

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "PostgreSQL database created successfully"
      }
    ]
  }
}
```

### レスポンス形式（エラー）

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "error": {
    "code": -32000,
    "message": "Database already exists",
    "data": {
      "details": "A database with this name already exists"
    }
  }
}
```

---

## Render MCP Server

### 概要

Renderが公式に提供するMCPサーバー。
Render のインフラをAIから操作できるようにする。

**GitHub:** https://github.com/render-oss/render-mcp-server

### セットアップ方法

#### 1. API Key作成

Render Dashboard → Account Settings → API Keys

#### 2. Claude Codeに設定

```bash
claude mcp add --transport http render https://mcp.render.com/mcp \
  --header "Authorization: Bearer <YOUR_API_KEY>"
```

#### 3. Workspaceを設定

```
Set my Render workspace to [WORKSPACE_NAME]
```

### 提供されるツール（一部抜粋）

#### Workspace管理
- `list_workspaces` - ワークスペース一覧
- `select_workspace` - ワークスペース選択
- `get_selected_workspace` - 現在のワークスペース取得

#### Service管理
- `list_services` - サービス一覧
- `get_service` - サービス詳細
- `create_web_service` - Webサービス作成
- `create_static_site` - 静的サイト作成
- `update_environment_variables` - 環境変数更新 ← 今回使用

#### Deploy管理
- `list_deploys` - デプロイ履歴
- `get_deploy` - デプロイ詳細

#### Logs & Metrics
- `list_logs` - ログ取得
- `get_metrics` - パフォーマンス指標取得

#### PostgreSQL
- `list_postgres_instances` - Postgres一覧
- `get_postgres` - Postgres詳細
- `create_postgres` - Postgres作成 ← 今回使用
- `query_render_postgres` - SQLクエリ実行 ← 今回使用

#### Redis (Key Value)
- `list_key_value` - Redis一覧
- `get_key_value` - Redis詳細
- `create_key_value` - Redis作成

---

## 実際の実行フロー

### シナリオ: PostgreSQLへの移行とデモデータ投入

**プロンプト:**
```
project-transparency-apiのRenderデータベースに接続して、
デモデータを投入してください。
```

### Step 1: 状況分析

Claude Codeが現在の状況を分析:
- アプリはSQLiteを使用している
- RenderにはPostgresデータベースがない
- まずPostgresを作成する必要がある

### Step 2: Postgres作成

**MCP呼び出し:**
```
render - create_postgres(
  name="project_transparency_db",
  plan="free",
  region="oregon"
)
```

**Render APIが実行:**
1. PostgreSQLインスタンスを作成
2. 接続情報を生成
3. DATABASE_URLを返す

**結果:**
```
DATABASE_URL=postgresql://user:password@host:5432/database
```

### Step 3: 環境変数設定

**MCP呼び出し:**
```
render - update_environment_variables(
  serviceId="srv-xxx",
  envVars=[
    {
      "key": "DATABASE_URL",
      "value": "postgresql://..."
    }
  ]
)
```

**Render APIが実行:**
1. サービスの環境変数を更新
2. 自動的に再デプロイをトリガー

**結果:**
```
Environment variables updated.
A new deploy has been triggered.
```

### Step 4: ローカルコード修正

Claude Codeがローカルで実行:

**1. database.pyを修正:**
```python
# Before
SQLALCHEMY_DATABASE_URL = "sqlite:///./project_transparency.db"

# After
import os
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./project_transparency.db"
)
```

**2. requirements.txtを更新:**
```
# 追加
psycopg2-binary==2.9.9
```

**3. デモデータ投入スクリプト作成:**
```python
# backend/insert_demo_data.py
# (スクリプトの内容)
```

### Step 5: Git操作

Claude Codeがローカルで実行:

```bash
git status
# 変更ファイルを確認

git diff backend/app/database.py
git diff backend/requirements.txt
# 差分を確認

git add backend/app/database.py backend/requirements.txt backend/insert_demo_data.py
# ファイルを追加

git commit -m "Add PostgreSQL support for Render deployment"
# コミット

git push origin main
# プッシュ
```

### Step 6: 自動デプロイ (CI/CD)

**GitHub:**
- pushを検知

**Render:**
- 自動的にビルド開始
- `pip install -r requirements.txt`
- `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- 環境変数 `DATABASE_URL` を使ってPostgresに接続
- デプロイ完了

### Step 7: デモデータ投入

**MCP呼び出し（試行）:**
```
render - query_render_postgres(
  postgresId="dpg-xxx",
  sql="INSERT INTO projects ..."
)
```

**エラー発生:**
```
SSL/TLS required
```

**Claude Codeの対応:**
- Plan A (MCP経由) 失敗
- Plan B (ローカルスクリプト) に切り替え
- `insert_demo_data.py`を実行
- データ投入成功

---

## 権限とセキュリティ

### API Keyの権限

> Render API keys are currently broadly scoped, giving your AI tools the same permissions that you would have access to.

**出典:** Render MCP Server README

**つまり:**
- あなたができること = Claude Codeができること
- 全てのワークスペース・サービスへのアクセス
- データベースの作成・削除
- 環境変数の変更

### 現在の制限

**破壊的操作の制限:**
- サービスの削除: 不可
- サービスの変更: 環境変数のみ可
- 手動デプロイトリガー: 不可

**出典:** Render MCP Server README

> The MCP server does not support modifying or deleting existing Render resources, with one exception: You can modify an existing service's environment variables.

### セキュリティ上の注意

> The Render MCP server attempts to minimize exposing sensitive information (like connection strings) to the MCP host's context. However, we make no guarantees about this behavior, and users should remain vigilant when discussing sensitive data.

**出典:** Render MCP Server README

**推奨事項:**
- API Keyの管理を厳密に
- 本番環境での使用は慎重に
- 機密情報を含むプロンプトは避ける

---

## Claude Codeのファイル操作

### アクセス可能な範囲

Claude Codeは以下にアクセスできます:

**1. 現在のディレクトリ:**
- カレントディレクトリ以下の全ファイル
- 読み取り・書き込み・削除

**2. Gitリポジトリ:**
- `git status`, `git diff`
- `git add`, `git commit`, `git push`
- ブランチ操作

**3. シェルコマンド:**
- `bash`で任意のコマンド実行
- パッケージインストール
- スクリプト実行

### 実行例

**ファイル確認:**
```bash
git status
```

**差分確認:**
```bash
git diff backend/app/database.py
```

**ファイル追加:**
```bash
git add backend/app/database.py
```

**コミット:**
```bash
git commit -m "Add PostgreSQL support"
```

**プッシュ:**
```bash
git push origin main
```

---

## エラーハンドリングと代替案

### 実際に起きたエラー

#### エラー1: Pydanticのビルドエラー

**症状:**
```
error: failed to create directory `/usr/local/cargo/registry/cache/`
Read-only file system
```

**原因:**
- `pydantic==2.5.0`が古い
- Rustのビルドが必要
- Renderの環境でRustビルドができない

**Claude Codeの対応:**
1. エラーを検知
2. requirements.txtを更新
   ```
   pydantic==2.10.0  # ビルド済みwheelがある
   ```
3. GitHubにpush
4. 自動再デプロイ
5. 成功

#### エラー2: SSL接続エラー

**症状:**
```
server error: FATAL: SSL/TLS required
```

**原因:**
- RenderのPostgresはSSL接続必須
- MCP経由の直接クエリがSSL非対応

**Claude Codeの対応:**
1. エラーを検知
2. Plan A (MCP経由) を諦める
3. Plan B (ローカルスクリプト) に切り替え
4. `insert_demo_data.py`を作成
5. SSL対応の接続で実行
6. 成功

### AIの自律的判断

**重要なポイント:**
- エラーが出ても止まらない
- 自動で代替案を試す
- 人間のように「Plan B」を考える
- トラブルシューティング能力

---

## パフォーマンス比較

### 従来の手動作業

```
1. Renderでポチポチ → Postgres作成（5分）
2. 接続文字列をコピー（1分）
3. コード修正（5分）
4. 環境変数設定（3分）
5. git add, commit, push（2分）
6. デプロイ待ち（5分）
7. マイグレーション実行（3分）
8. デモデータ作成スクリプト書く（10分）
9. 実行（2分）

合計: 約36分（デプロイ待ち含めると47分）
```

### AI自動化

```
プロンプト: 「Postgresに移行してデモデータ入れて」
  ↓
Claude Code: （全自動実行）
  ↓
完了

所要時間: 約2分
```

### 効率化率

- **手作業:** 47分
- **AI自動化:** 2分
- **効率化:** 約23倍

---

## 技術的な制約と限界

### Render MCP Server の制限

**1. サービスタイプの制限**
- Web ServiceとStatic Siteのみ作成可能
- Private Service、Background Worker、Cron Job は不可

**2. 設定オプションの制限**
- Image-backed serviceは作成不可
- IP allowlistの設定不可

**3. 操作の制限**
- サービスの変更・削除は不可（環境変数のみ可）
- 手動デプロイトリガーは不可

**4. 無料プランの制限**
- 無料インスタンスは作成不可

**出典:** Render MCP Server README

### Claude Codeの制限

**1. コンテキストウィンドウ**
- 大量のファイルを一度に扱えない
- 長いログは切り詰められる

**2. 非同期処理**
- デプロイ完了を待つのが難しい
- タイムアウトの可能性

**3. セキュリティ**
- ローカルファイルへの全アクセス
- 慎重な使用が必要

---

## ユースケース

### 開発フロー

**1. 新しいサービスの立ち上げ:**
```
プロンプト: 
「Node.jsのExpressアプリをmy-appという名前でデプロイして」

Claude Code:
→ create_web_service
→ 自動デプロイ
```

**2. データベースの追加:**
```
プロンプト:
「user-dbという名前でPostgresを作成して」

Claude Code:
→ create_postgres
→ 接続情報を表示
```

**3. ログの確認:**
```
プロンプト:
「my-appの最新のエラーログを見せて」

Claude Code:
→ list_logs(level=["error"])
→ エラー内容を表示
```

**4. パフォーマンス分析:**
```
プロンプト:
「my-appのCPUとメモリ使用率を過去2時間分見せて」

Claude Code:
→ get_metrics(metricTypes=["cpu_usage", "memory_usage"])
→ グラフ表示
```

---

## 他のMCPサーバー

### 公式MCPサーバー

Anthropicが提供している主なMCPサーバー:

**開発ツール:**
- GitHub MCP Server
- GitLab MCP Server
- Linear MCP Server

**ビジネスツール:**
- Slack MCP Server
- Google Drive MCP Server
- Notion MCP Server

**データベース:**
- PostgreSQL MCP Server
- Supabase MCP Server

**ブラウザ自動化:**
- Puppeteer MCP Server

### サードパーティMCPサーバー

コミュニティが開発しているMCPサーバー:

**コミュニケーション:**
- Discord MCP Server
- Teams MCP Server

**プロジェクト管理:**
- Jira MCP Server
- Asana MCP Server
- Monday.com MCP Server

**データソース:**
- Airtable MCP Server
- Box MCP Server

---

## 今後の展望

### MCP エコシステムの成長

**現状:**
- 数十のMCPサーバーが公開されている
- 主要なSaaSツールがMCPをサポートし始めている

**今後の予測:**
- より多くのツールがMCPをサポート
- MCPがデファクトスタンダードになる可能性
- AI × ツール連携が爆発的に拡大

### Claude Codeの進化

**現在の能力:**
- ファイル操作
- Git操作
- MCP経由の外部ツール操作

**今後の期待:**
- より長いコンテキストウィンドウ
- 非同期処理の改善
- マルチモーダル対応

---

## 結論

### 技術的な達成

**1. 完全自動化:**
- プロンプト1つでインフラ構築からデプロイまで
- 人間の介入なし
- エラーも自動で対処

**2. 統一されたインターフェース:**
- MCPという標準規格
- どんなツールでも同じ方法で操作
- USB-Cのような統一規格

**3. AI x Infrastructure:**
- AIがコードを書くだけでなく、インフラも構築
- 「教える」から「やる」への転換
- エンジニアの仕事の一部が自動化

### ビジネス的インパクト

**効率化:**
- 47分 → 2分（23倍）
- エラー対応も自動
- 属人化の解消

**スケーラビリティ:**
- 一度セットアップすれば何度でも使える
- チーム全体で恩恵
- ナレッジが形式知化される

### 今後の課題

**セキュリティ:**
- API Keyの管理
- 権限の細分化
- 監査ログの整備

**信頼性:**
- エラーハンドリングの改善
- 非同期処理の安定化
- タイムアウト対策

**ユーザビリティ:**
- より直感的なプロンプト
- エラーメッセージの改善
- ドキュメントの充実

---

## 参考資料

### 公式ドキュメント

**Anthropic:**
- Model Context Protocol 公式サイト: https://modelcontextprotocol.io/
- Claude Code MCP ドキュメント: https://docs.claude.com/en/docs/claude-code/mcp
- Introducing the Model Context Protocol: https://www.anthropic.com/news/model-context-protocol

**Render:**
- Render MCP Server: https://render.com/docs/mcp-server
- GitHub Repository: https://github.com/render-oss/render-mcp-server

### コミュニティリソース

- Claude MCP Community: https://www.claudemcp.com/
- MCP GitHub Organization: https://github.com/modelcontextprotocol

---

## まとめ

Model Context Protocol (MCP) とClaude Codeの組み合わせにより:

1. **AIがインフラを構築できる時代が来た**
2. **プロンプト1つで複雑な作業が完了する**
3. **エラーも自動で対処する**
4. **開発効率が劇的に向上する（23倍）**
5. **これは始まりに過ぎない**

**インフラエンジニアリングの民主化が始まっている。**
