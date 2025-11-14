# JWT認証実装 学習レポート

## 📋 概要

Project TransparencyアプリケーションにJWT（JSON Web Token）認証機能を実装し、ユーザーごとのデータ所有権を確立しました。このレポートでは、実装過程で学んだ重要なポイントと技術的な洞察をまとめます。

**実装期間**: 2025年11月14-15日
**実装範囲**: バックエンド（FastAPI）、フロントエンド（Next.js）、本番環境デプロイ

---

## 🎯 プロジェクト目標

### Before（実装前）
- 認証なし、誰でもアクセス可能
- データの所有権概念なし
- 本番環境でのセキュリティリスク

### After（実装後）
- ✅ JWT認証によるセキュアなアクセス制御
- ✅ ユーザーごとの独立したデータ管理
- ✅ 本番環境で完全動作
- ✅ フロントエンドとバックエンドのシームレスな統合

---

## 🏗️ アーキテクチャ設計

### システム全体図

```
┌─────────────────────────────────────────────────────────┐
│                    User (Browser)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Frontend (Next.js / Vercel)                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  - Login/Register Pages                          │   │
│  │  - AuthGuard (Route Protection)                  │   │
│  │  - Token Storage (LocalStorage)                  │   │
│  │  - Axios Interceptor (Auto Auth Header)          │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS + JWT Token
                     ↓
┌─────────────────────────────────────────────────────────┐
│            Backend API (FastAPI / Render)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  - JWT Token Verification                        │   │
│  │  - Password Hashing (bcrypt)                     │   │
│  │  - User Authentication                           │   │
│  │  - Data Ownership Check                          │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ Internal Connection
                     ↓
┌─────────────────────────────────────────────────────────┐
│          Database (PostgreSQL / Render)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  users (id, email, hashed_password, name)        │   │
│  │    ↓                                             │   │
│  │  projects (id, name, user_id ← FK)               │   │
│  │    ↓                                             │   │
│  │  members (id, project_id ← FK)                   │   │
│  │    ↓                                             │   │
│  │  scores (id, member_id ← FK)                     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 認証フロー

```
1. ユーザー登録/ログイン
   ↓
2. バックエンドでパスワード検証
   ↓
3. JWTトークン生成（sub: user_id, exp: 24時間）
   ↓
4. フロントエンドがLocalStorageに保存
   ↓
5. API呼び出し時、自動的にAuthorizationヘッダー追加
   ↓
6. バックエンドでトークン検証
   ↓
7. user_idでデータフィルタリング
   ↓
8. レスポンス返却
```

---

## 🔑 重要な実装ポイント

### 1. JWT仕様への準拠

#### 問題
最初、ユーザーIDを整数のままJWTの`sub`クレームに設定していた：

```python
# ❌ 誤った実装
access_token = create_access_token(data={"sub": user.id})  # user.id は int型
```

#### エラー
```
jose.exceptions.JWTError: Subject must be a string.
```

#### 解決策
JWT仕様（RFC 7519）では、`sub`クレームは**文字列でなければならない**：

```python
# ✅ 正しい実装
access_token = create_access_token(data={"sub": str(user.id)})

# デコード時は整数に戻す
def decode_access_token(token: str) -> TokenData:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = int(payload.get("sub"))  # 文字列 → 整数
    return TokenData(user_id=user_id)
```

#### 学び
**標準仕様を遵守することの重要性**。独自の実装ではなく、RFCなどの標準仕様を確認し、それに従うことでライブラリ間の互換性が保たれる。

---

### 2. パスワードセキュリティとライブラリ互換性

#### 問題
長いパスワードで以下のエラーが発生：

```
ValueError: password cannot be longer than 72 bytes
```

#### 原因
- bcryptアルゴリズムは**72バイトまで**しか処理できない（仕様）
- bcrypt 5.x以降は72バイトを超えるとエラーを発生させる（セキュリティ強化）
- しかし、passlib 1.7.4がbcrypt 5.x以降のAPIに対応していない

#### 試行錯誤
1. **試行1**: パスワードを72バイトに切り詰める → 初期化エラー解決せず
2. **試行2**: `bcrypt__truncate_error=True` → passlib未対応
3. **最終解決**: bcryptを3.2.0にダウングレード

```bash
pip install bcrypt==3.2.0
```

#### 実装
```python
def get_password_hash(password: str) -> str:
    # bcrypt 3.2.0は自動で72バイトに切り詰める
    password_bytes = password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_password)
```

#### 学び
- **ライブラリのバージョン互換性**を常に確認する
- 新しいバージョンが必ずしも良いとは限らない
- セキュリティライブラリは特に慎重にバージョン管理すべき
- アルゴリズムの仕様制限（72バイト）を理解する

---

### 3. データベースマイグレーション戦略

#### 問題
モデルに`user_id`カラムを追加したが、既存のデータベース（SQLite/PostgreSQL）には反映されない：

```python
class Project(Base):
    # ... 既存フィールド ...
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 追加
```

#### エラー
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError)
no such column: projects.user_id
```

#### 開発環境での解決策
SQLiteファイルを削除して再作成：

```bash
rm backend/project_transparency.db
uvicorn app.main:app --reload  # 自動的に新しいスキーマで作成
```

#### 本番環境での解決策
PostgreSQLは削除できないため、環境変数でコントロール：

```python
# main.py
if os.getenv("RESET_DB", "false").lower() == "true":
    Base.metadata.drop_all(bind=engine)  # 全テーブル削除

Base.metadata.create_all(bind=engine)  # 再作成
```

**運用手順**：
1. Renderで`RESET_DB=true`を設定
2. デプロイ → テーブル再作成
3. `RESET_DB`を削除（重要！）

#### より良い方法：Alembic
将来的には、Alembicを使った段階的マイグレーションを推奨：

```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Add user_id to projects"
alembic upgrade head
```

#### 学び
- **開発環境と本番環境で異なる戦略が必要**
- SQLAlchemyの`create_all()`は既存テーブルを変更しない
- 本番環境でのデータ保持を考慮したマイグレーション戦略が重要
- Alembicなどのマイグレーションツールの重要性

---

### 4. フロントエンドの認証フロー設計

#### 設計方針
**シームレスなユーザー体験**を重視：

1. **自動リダイレクト**: 未認証時は自動的にログインページへ
2. **トークン永続化**: LocalStorageで24時間保持
3. **自動ヘッダー追加**: axiosインターセプターで全リクエストに自動付与
4. **エラー自動処理**: 401エラー時の自動ログアウト

#### 実装：AuthGuard

```typescript
// components/AuthGuard.tsx
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const publicPaths = ['/auth/login', '/auth/register'];
    const isPublicPath = publicPaths.includes(pathname);

    if (!isPublicPath && !isAuthenticated()) {
      router.push('/auth/login');  // 自動リダイレクト
    }
  }, [pathname, router]);

  return <>{children}</>;
}
```

#### 実装：Axiosインターセプター

```typescript
// lib/api.ts
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;  // 自動追加
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken();  // 自動ログアウト
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);
```

#### 学び
- **インターセプターパターン**で横断的関心事を一元管理
- ユーザーに認証の存在を意識させない設計
- エラー処理の一元化によるコードの簡潔化

---

### 5. データ所有権の実装

#### 設計
各ユーザーは自分のデータのみアクセス可能：

```
users (1) ─── (N) projects (1) ─── (N) members (1) ─── (N) scores
```

#### バックエンド実装

```python
@router.get("/projects", response_model=schemas.ProjectListResponse)
def get_projects(
    current_user: models.User = Depends(get_current_user),  # 認証必須
    db: Session = Depends(get_db)
):
    # current_user.id で自動フィルタリング
    projects = db.query(models.Project)\
        .filter(models.Project.user_id == current_user.id)\
        .all()
    return {"projects": projects}
```

#### セキュリティチェック

```python
@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # 所有者チェック
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")

    return project
```

#### 学び
- **依存性注入（Depends）** を活用した認証チェックの統一
- 各エンドポイントで**明示的な所有者チェック**
- 404と403の使い分け（存在しない vs アクセス権なし）

---

## 🔒 セキュリティ対策

### 1. パスワードセキュリティ

#### 実装内容
- **ハッシュ化**: bcryptによる一方向ハッシュ
- **ソルト**: bcryptが自動的に生成
- **コストファクター**: bcryptのデフォルト設定（自動調整）

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

#### ベストプラクティス
- ✅ 平文パスワードは絶対に保存しない
- ✅ ログにパスワードを出力しない
- ✅ HTTPSで通信（本番環境）
- ✅ 最小パスワード長を設定（8文字以上）

### 2. JWT トークンセキュリティ

#### SECRET_KEY管理
```python
# ❌ 絶対にやってはいけない
SECRET_KEY = "my-secret-key"  # ハードコーディング

# ✅ 正しい方法
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
```

#### .gitignore設定
```
# .gitignore
.env
*.env
backend/.env
```

#### 本番環境での設定
- 開発環境と**異なる秘密鍵**を使用
- 環境変数で管理（Renderの Environment Variables）
- 定期的なローテーション（推奨）

### 3. トークン有効期限

```python
ACCESS_TOKEN_EXPIRE_HOURS = 24

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

#### 推奨事項
- 短い有効期限（1-24時間）
- リフレッシュトークンの実装（将来的）
- 自動ログアウト機能

### 4. CORS設定

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 開発環境
    allow_origin_regex=r"https://.*\.vercel\.app",  # 本番環境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### ポイント
- 本番環境では特定のドメインのみ許可
- `allow_credentials=True` でCookieを許可
- 開発と本番で異なる設定

---

## 🚀 デプロイと運用

### デプロイフロー

```
GitHub Push
   ↓
Render（Backend）自動デプロイ
   ├── ビルド: pip install -r requirements.txt
   ├── テーブル作成: Base.metadata.create_all()
   └── 起動: uvicorn app.main:app
   ↓
Vercel（Frontend）自動デプロイ
   ├── ビルド: npm run build
   └── デプロイ: Next.js App
```

### 環境変数管理

#### Render（Backend）
```
DATABASE_URL=<PostgreSQL Internal URL>
SECRET_KEY=<openssl rand -hex 32で生成>
```

#### Vercel（Frontend）
```
NEXT_PUBLIC_API_BASE_URL=https://project-transparency-api.onrender.com
```

### トラブルシューティング経験

#### 問題1: デプロイ後にuser_idエラー
**原因**: データベーススキーマが更新されていない
**解決**: `RESET_DB=true` で一時的にリセット

#### 問題2: フロントエンドにログイン画面が表示されない
**原因**: フロントエンドファイルがコミットされていない
**解決**: プロジェクトルートから `git add .` を実行

---

## 📊 実装の成果

### 定量的成果

- **新規ファイル**: 17ファイル
- **コード行数**: 約800行追加
- **エラー解決**: 4つの主要エラーを解決
- **ドキュメント**: 4つの詳細ドキュメント作成

### 定性的成果

✅ **セキュリティ**: 本番環境でのセキュアなアクセス制御
✅ **ユーザー体験**: シームレスな認証フロー
✅ **データ整合性**: ユーザーごとの独立したデータ管理
✅ **保守性**: 明確なドキュメントとエラーレポート

---

## 🎓 学んだこと

### 技術的学び

1. **標準仕様の重要性**
   - JWT RFC 7519への準拠
   - 独自実装ではなく標準に従う

2. **ライブラリ管理**
   - バージョン互換性の確認
   - 新しい ≠ 良い
   - セキュリティライブラリは特に慎重に

3. **データベース設計**
   - マイグレーション戦略の重要性
   - 開発環境と本番環境の違い
   - 外部キー制約による整合性

4. **フロントエンド設計**
   - インターセプターパターン
   - 横断的関心事の一元管理
   - ユーザー体験重視の設計

5. **セキュリティ**
   - パスワードハッシュ化
   - 秘密鍵の管理
   - 環境変数の使い方

### 開発プロセスの学び

1. **エラーは学びの機会**
   - 各エラーから重要な知識を獲得
   - エラーメッセージを丁寧に読む
   - ドキュメントで原因を調査

2. **段階的実装**
   - バックエンド → フロントエンド → 統合
   - 各段階でテストを実施
   - 小さく確実に進める

3. **ドキュメンテーション**
   - 詳細なエラーレポート
   - 学習レポート
   - 将来の自分や他者のために

4. **本番環境との違い**
   - 開発環境で動いても本番で動かない場合がある
   - 環境変数の設定漏れ
   - データベースのスキーマ差異

---

## 🔮 今後の改善案

### 短期的改善（1-2週間）

1. **トークンリフレッシュ機能**
   - アクセストークン: 15分
   - リフレッシュトークン: 7日間

2. **パスワードリセット機能**
   - メール送信
   - ワンタイムトークン

3. **レート制限**
   - ログイン試行回数制限
   - ブルートフォース攻撃対策

### 中期的改善（1-2ヶ月）

4. **メール確認機能**
   - 登録時のメール認証
   - アカウントアクティベーション

5. **2要素認証（2FA）**
   - TOTP（Time-based One-Time Password）
   - Google Authenticator連携

6. **ロギングと監視**
   - ログイン履歴
   - 異常アクセス検知
   - セキュリティイベントの記録

### 長期的改善（3ヶ月以上）

7. **OAuth2対応**
   - Google/GitHub認証
   - ソーシャルログイン

8. **権限管理（RBAC）**
   - ロールベースアクセス制御
   - Admin, User, Guestなど

9. **セッション管理**
   - アクティブセッション一覧
   - リモートログアウト機能

---

## 📚 参考資料

### 公式ドキュメント

- **JWT**: [RFC 7519 - JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- **FastAPI Security**: [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- **passlib**: [passlib Documentation](https://passlib.readthedocs.io/)
- **bcrypt**: [bcrypt Specification](https://en.wikipedia.org/wiki/Bcrypt)

### 関連レポート

1. `06_JWT認証とセキュリティの理解.md` - JWT基礎知識
2. `07_JWT認証機能追加_要件定義書.md` - 要件定義
3. `08_JWT認証実装_エラーレポート.md` - エラーと解決策
4. `09_JWT認証実装_学習レポート.md` - 本レポート（総括）

---

## 💡 結論

JWT認証の実装を通じて、以下の重要な学びを得ました：

1. **標準仕様への準拠**の重要性
2. **ライブラリのバージョン管理**の難しさと重要性
3. **データベースマイグレーション**戦略の必要性
4. **セキュリティ**は設計段階から考慮すべき
5. **ユーザー体験**を重視した認証フロー設計

これらの知識は、今後のWeb アプリケーション開発において非常に有用です。

特に印象的だったのは、**エラーから学ぶことの価値**です。JWT "sub"クレーム型エラーやbcrypt互換性問題など、各エラーが深い理解につながりました。

**認証は全てのWebアプリケーションの基礎**です。この実装経験は、今後のプロジェクトでも活かせる貴重な資産となりました。

---

**作成日**: 2025年11月15日
**作成者**: Claude Code with Human Collaboration
**バージョン**: 1.0
