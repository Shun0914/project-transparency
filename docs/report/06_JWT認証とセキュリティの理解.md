# JWT認証とセキュリティの理解

**作成日**: 2025-11-16  
**目的**: Project Transparencyへの認証機能追加に向けた、JWT・bcrypt・認証の仕組みの深い理解

---

## 📋 目次

1. [なぜ認証が必要なのか](#なぜ認証が必要なのか)
2. [JWT（JSON Web Token）とは](#jwtjson-web-tokenとは)
3. [パスワードのハッシュ化（bcrypt）](#パスワードのハッシュ化bcrypt)
4. [セッションベース vs トークンベース](#セッションベース-vs-トークンベース)
5. [Cookieとは](#cookieとは)
6. [認証の全体フロー](#認証の全体フロー)
7. [実装設計](#実装設計)
8. [今後の実装計画](#今後の実装計画)

---

## なぜ認証が必要なのか

### 現状のProject Transparency

```python
@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()
```

**問題点:**
- 誰でもアクセスできる
- 誰のプロジェクトか区別できない
- データの削除・編集を誰でもできる
- セキュリティリスク大

---

### 認証があると

```python
@app.get("/api/projects")
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # current_user が取得できている = 認証成功
    # そのユーザーのプロジェクトだけを返す
    return db.query(Project).filter(Project.user_id == current_user.id).all()
```

**メリット:**
- ログインしたユーザーだけアクセス可能
- ユーザーごとにデータを分離
- 不正な操作を防げる

---

## JWT（JSON Web Token）とは

### 一言で言うと

**「3つのパーツで構成された、署名付きのトークン形式」**

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│                                      │                                                │
│                                      │                                                └─ Signature（署名）
│                                      └─ Payload（データ）
└─ Header（メタ情報）
```

---

### JWTの構造

#### 1. Header（ヘッダー）

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

Base64エンコード → `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`

**役割:** アルゴリズムの指定

---

#### 2. Payload（ペイロード）

```json
{
  "user_id": 123,
  "email": "user@example.com",
  "exp": 1700000000
}
```

Base64エンコード → `eyJ1c2VyX2lkIjoxMjMsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsImV4cCI6MTcwMDAwMDAwMH0`

**役割:** ユーザー情報の保存

**重要:** 暗号化されていない（誰でもデコードできる）

---

#### 3. Signature（署名）

```python
signature = HMAC_SHA256(
    base64(header) + "." + base64(payload),
    SECRET_KEY
)
```

→ `SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c`

**役割:** 改ざん検知

---

### JWTの重要な性質

#### ❌ 誤解: JWTは暗号化されている

**実際:**
- Header と Payload はBase64エンコードだけ
- 誰でもデコードして中身を読める

```python
import base64
import json

payload = "eyJ1c2VyX2lkIjoxMjMsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSJ9"
decoded = base64.b64decode(payload + "==")
print(json.loads(decoded))
# → {"user_id": 123, "email": "user@example.com"}
```

**だから、パスワードなどの機密情報は入れない**

---

#### ✅ 正しい理解: JWTは改ざん検知できる

**Signatureの役割:**

```
攻撃者が Payload を改ざん:
  元: {"user_id": 123}
  改: {"user_id": 999}

サーバーが検証:
  1. Payload を取り出す
  2. SECRET_KEY で署名を再計算
  3. 受け取った署名と比較
  
  再計算した署名 ≠ 受け取った署名
  → 改ざんされている！
```

**SECRET_KEY を知っているのはサーバーだけ**  
→ 攻撃者は正しい署名を作れない

---

### JWT発行の流れ

```python
# ログイン時
@app.post("/api/auth/login")
def login(email: str, password: str, db: Session):
    # 1. パスワード検証
    user = verify_user(email, password)
    
    # 2. JWTを生成
    token = jwt.encode(
        {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=24)
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    
    # 3. クライアントに返す（DBには保存しない）
    return {"access_token": token}
```

**内部処理:**

```python
# jwt.encode() の内部で何が起こるか

# 1. Header を Base64 エンコード
header = base64_encode({"alg": "HS256", "typ": "JWT"})

# 2. Payload を Base64 エンコード
payload = base64_encode({"user_id": 123, "email": "user@example.com"})

# 3. Signature を生成
message = header + "." + payload
signature = HMAC_SHA256(message, SECRET_KEY)

# 4. 結合
token = header + "." + payload + "." + signature
```

---

### JWT検証の流れ

```python
# API呼び出し時
@app.get("/api/projects")
def get_projects(authorization: str = Header(None)):
    # 1. トークンを受け取る
    token = authorization.replace("Bearer ", "")
    
    # 2. トークンを検証
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # → {"user_id": 123, "email": "user@example.com"}
        
        user_id = payload["user_id"]
        return {"message": f"Hello user {user_id}"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

**内部処理:**

```python
# jwt.decode() の内部で何が起こるか

# 1. トークンを分割
parts = token.split(".")
header_encoded = parts[0]
payload_encoded = parts[1]
received_signature = parts[2]

# 2. 署名を再計算
message = header_encoded + "." + payload_encoded
expected_signature = HMAC_SHA256(message, SECRET_KEY)

# 3. 比較
if expected_signature == received_signature:
    # OK - 改ざんされていない
    payload = json.loads(base64_decode(payload_encoded))
    return payload
else:
    # NG - 改ざんされている
    raise InvalidTokenError
```

---

### 重要なポイント

**検証に使うもの:**
- Header（トークンから取得）
- Payload（トークンから取得）
- Signature（トークンから取得）
- SECRET_KEY（サーバーが保持）

**検証に使わないもの:**
- ❌ パスワード
- ❌ データベース（※）

※ user_id を使ってユーザー情報を取得する場合は除く

**パスワードはログイン時の1回だけ使う**

**その後の検証には SECRET_KEY だけ使う**

---

## パスワードのハッシュ化（bcrypt）

### なぜハッシュ化が必要なのか

#### ❌ 間違った方法: 平文で保存

```sql
-- データベース
| id | email            | password    |
|----|------------------|-------------|
| 1  | user@example.com | password123 |
```

**問題:**
- データベースが漏洩したら、全員のパスワードが見える
- 管理者もパスワードを見られる
- 致命的なセキュリティリスク

---

#### ✅ 正しい方法: ハッシュ化して保存

```sql
-- データベース
| id | email            | hashed_password                                                |
|----|------------------|----------------------------------------------------------------|
| 1  | user@example.com | $2b$12$N9qo8uLOickgx2ZMRZoMye/IjZAgcfl7p92ldGxad68LJZdL17lhO |
```

**メリット:**
- データベースが漏洩しても、パスワードは分からない
- 管理者でもパスワードを見られない

---

### ハッシュ化とは

**一言で言うと:**  
「どんなデータでも、固定長のランダムに見える文字列に変換する」一方通行の関数

**特徴:**
- **一方通行** - 元に戻せない
- **同じ入力 → 同じ出力** - 必ず同じ結果
- **少しでも変わると全く違う出力**

```python
import hashlib

# 入力1
hash1 = hashlib.sha256(b"password").hexdigest()
# → "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"

# 入力2（1文字だけ違う）
hash2 = hashlib.sha256(b"Password").hexdigest()
# → "e7cf3ef4f17c3999a94f2c6f612e8a888e5b1026878e4e19398b23bd38ec221a"
```

---

### なぜSHA256ではダメなのか

**問題: SHA256は速すぎる**

```python
# 100万回のハッシュ化: 約0.5秒
for i in range(1000000):
    hashlib.sha256(password.encode()).hexdigest()
```

**GPUを使えば、毎秒数十億回の計算が可能**

→ 弱いパスワードは数秒〜数分で解読される

---

### bcryptの解決策: わざと遅くする

```python
import bcrypt

# 100回のハッシュ化: 約10秒
for i in range(100):
    bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

**SHA256との比較:**

| ハッシュ関数 | 1回あたりの時間 | 100万回の時間 |
|------------|---------------|-------------|
| SHA256 | 0.0000005秒 | 0.5秒 |
| bcrypt | 0.1秒 | 27時間 |

**bcryptはSHA256の20万倍遅い！**

**遅さが防御になる**

---

### bcryptの仕組み

#### 1. 自動でSaltを生成

```python
password = "password123"

# ハッシュ化（Saltは自動で内部に含まれる）
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed)
# b'$2b$12$N9qo8uLOickgx2ZMRZoMye/IjZAgcfl7p92ldGxad68LJZdL17lhO'
```

**構造:**
```
$2b$12$N9qo8uLOickgx2ZMRZoMye/IjZAgcfl7p92ldGxad68LJZdL17lhO
│  │  │                     │
│  │  │                     └─ ハッシュ値（31文字）
│  │  └─ Salt（22文字）
│  └─ コスト（計算の重さ）
└─ アルゴリズムバージョン
```

**Saltが含まれているので:**
- 同じパスワードでも、毎回違うハッシュが生成される
- レインボーテーブル攻撃が無効化される

---

#### 2. コストを調整できる

```python
# コスト = 10（デフォルト）
bcrypt.gensalt(rounds=10)  # 約0.05秒

# コスト = 12（推奨）
bcrypt.gensalt(rounds=12)  # 約0.2秒

# コスト = 14
bcrypt.gensalt(rounds=14)  # 約0.8秒
```

**コストが1増えると、計算時間が2倍になる**

**将来的にコンピューターが速くなったら:**
- コストを上げるだけで対応できる

---

### 実装例

#### ユーザー登録時

```python
import bcrypt

@app.post("/api/auth/register")
def register(email: str, password: str, db: Session):
    # パスワードをハッシュ化
    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=12)
    )
    
    # データベースに保存
    new_user = User(
        email=email,
        hashed_password=hashed_password.decode('utf-8')
    )
    db.add(new_user)
    db.commit()
    
    return {"message": "登録完了"}
```

---

#### ログイン時

```python
@app.post("/api/auth/login")
def login(email: str, password: str, db: Session):
    # ユーザーを取得
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # パスワードを検証
    if bcrypt.checkpw(
        password.encode('utf-8'),
        user.hashed_password.encode('utf-8')
    ):
        # パスワード正しい → トークン発行
        token = create_jwt_token(user.id)
        return {"access_token": token}
    else:
        raise HTTPException(401, "Invalid credentials")
```

---

### bcrypt.checkpw() の内部動作

```python
stored_hash = "$2b$12$N9qo8uLOickgx2ZMRZoMye/IjZAgcfl7p92ldGxad68LJZdL17lhO"
input_password = "password123"

# 1. ハッシュからSaltを取り出す
salt = stored_hash[:29]

# 2. 入力パスワード + Salt でハッシュ化
computed_hash = bcrypt.hashpw(input_password.encode(), salt.encode())

# 3. 比較
if computed_hash == stored_hash:
    print("パスワード正しい")
```

**「元に戻す」のではなく「再計算して比較」**

---

## セッションベース vs トークンベース

### セッションベース認証（Cookie使用）

#### 仕組み

```
ログイン
  ↓
サーバーがセッションIDを生成（ランダム文字列）
  ↓
サーバーのメモリ/DBに保存
  ↓
セッションIDをCookieでブラウザに送る
  ↓
次回リクエスト時、Cookieで自動送信
  ↓
サーバーがメモリ/DBを見て「誰か」を確認
```

---

#### 実装例

```python
# サーバーのメモリ
sessions = {
    "abc123": {"user_id": 1, "email": "user@example.com"},
    "def456": {"user_id": 2, "email": "another@example.com"}
}

# ログイン
@app.post("/login")
def login(email: str, password: str, response: Response):
    user = verify_user(email, password)
    
    session_id = generate_random_string()  # "abc123"
    
    # サーバーのメモリに保存
    sessions[session_id] = {"user_id": user.id, "email": user.email}
    
    # Cookieで送る
    response.set_cookie("session_id", session_id, httponly=True)
    
    return {"message": "ログイン成功"}

# API呼び出し
@app.get("/api/profile")
def get_profile(request: Request):
    session_id = request.cookies.get("session_id")
    
    # メモリから取得
    session_data = sessions.get(session_id)
    
    if not session_data:
        raise HTTPException(401)
    
    user_id = session_data["user_id"]
    return {"user_id": user_id}
```

---

### トークンベース認証（JWT）

#### 仕組み

```
ログイン
  ↓
サーバーがJWTを生成
  ↓
サーバーは何も保存しない
  ↓
JWTをレスポンスで返す
  ↓
次回リクエスト時、Authorizationヘッダーで送信
  ↓
サーバーが署名を検証して「誰か」を確認
```

---

#### 実装例

```python
# サーバーのメモリ: 空っぽ

# ログイン
@app.post("/login")
def login(email: str, password: str):
    user = verify_user(email, password)
    
    # JWT生成
    token = jwt.encode({"user_id": user.id}, SECRET_KEY)
    
    # サーバーは何も保存しない
    return {"access_token": token}

# API呼び出し
@app.get("/api/profile")
def get_profile(token: str):
    # トークンを検証
    payload = jwt.decode(token, SECRET_KEY)
    user_id = payload["user_id"]
    
    return {"user_id": user_id}
```

---

### 比較表

| 項目 | セッションベース | トークンベース（JWT） |
|------|----------------|---------------------|
| **サーバーの保存** | ✅ sessions辞書/DB | ❌ 何も保存しない |
| **情報の保存場所** | サーバーのメモリ/DB | トークンの中 |
| **検証方法** | メモリ/DBを見る | 署名を検証 |
| **スケール** | 難しい（共有メモリ必要） | 簡単（どのサーバーでもOK） |
| **強制無効化** | 簡単（削除するだけ） | 難しい（ブラックリスト必要） |
| **パフォーマンス** | I/Oが必要 | CPU計算のみ |

---

### なぜJWTを選ぶのか

**Project Transparencyの要件:**
- Vercel（フロント）と Render（バック）が別ドメイン
- 将来的にスケールする可能性
- シンプルな実装

**→ トークンベース（JWT）が適している**

---

## Cookieとは

### 一言で言うと

**「ブラウザに保存される小さなテキストファイル」**

サーバーがブラウザに「これ覚えといて」と渡すメモ

---

### 具体例

#### 1回目の訪問

```http
GET / HTTP/1.1
Host: amazon.com

↓ レスポンス

HTTP/1.1 200 OK
Set-Cookie: session_id=abc123xyz; Path=/; HttpOnly
Set-Cookie: user_preferences=dark_mode; Path=/

<html>ようこそ！</html>
```

**ブラウザに保存される:**
```
amazon.com のCookie:
  - session_id=abc123xyz
  - user_preferences=dark_mode
```

---

#### 2回目の訪問（次の日）

```http
GET / HTTP/1.1
Host: amazon.com
Cookie: session_id=abc123xyz; user_preferences=dark_mode

↓ レスポンス

HTTP/1.1 200 OK

<html>おかえりなさい、駿介さん！</html>
```

**Cookieがあるから:**
- ログイン状態を覚えている
- 設定を覚えている

---

### Cookieの属性

#### HttpOnly

```python
response.set_cookie("session_id", "abc123", httponly=True)
```

**意味:** JavaScriptからアクセスできない

**用途:** XSS攻撃を防ぐ

---

#### Secure

```python
response.set_cookie("session_id", "abc123", secure=True)
```

**意味:** HTTPS接続でのみ送信される

**用途:** 盗聴を防ぐ

---

#### SameSite

```python
response.set_cookie("session_id", "abc123", samesite="Lax")
```

**意味:** 別のサイトからのリクエストでCookieを送るかどうか

**用途:** CSRF攻撃を防ぐ

---

### localStorage vs Cookie

| 項目 | Cookie | localStorage |
|------|--------|--------------|
| **容量** | 4KB | 5-10MB |
| **自動送信** | ✅ ブラウザが自動で送る | ❌ JavaScriptで手動送信 |
| **有効期限** | 設定可能 | 永続（手動削除まで） |
| **サーバーアクセス** | ✅ サーバーが読み書き可能 | ❌ JavaScriptのみ |
| **XSS耐性** | ✅ HttpOnlyで保護可能 | ❌ JavaScriptで読める |
| **CSRF耐性** | ❌ 自動送信が弱点 | ✅ 自動送信しない |

---

### Project Transparencyでの選択

**選択肢1: JWT + localStorage（シンプル）**

```typescript
// ログイン成功後
localStorage.setItem("access_token", token);

// API呼び出し
fetch('/api/projects', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
})
```

**メリット:** シンプル  
**デメリット:** XSSに弱い

**→ まずはこれで実装**

---

## 認証の全体フロー

### ユーザー登録

```
フロントエンド                    バックエンド                    データベース
     │                                │                                │
     │ POST /api/auth/register        │                                │
     │ {email, password}              │                                │
     ├───────────────────────────────>│                                │
     │                                │ パスワードをbcryptでハッシュ化     │
     │                                │                                │
     │                                │ INSERT INTO users              │
     │                                ├───────────────────────────────>│
     │                                │                                │
     │                                │ user_id返却                     │
     │                                │<───────────────────────────────┤
     │ 200 OK                         │                                │
     │ {message: "登録完了"}           │                                │
     │<───────────────────────────────┤                                │
```

---

### ログイン

```
フロントエンド                    バックエンド                    データベース
     │                                │                                │
     │ POST /api/auth/login           │                                │
     │ {email, password}              │                                │
     ├───────────────────────────────>│                                │
     │                                │ SELECT * FROM users            │
     │                                │ WHERE email = ?                │
     │                                ├───────────────────────────────>│
     │                                │                                │
     │                                │ user返却                        │
     │                                │<───────────────────────────────┤
     │                                │                                │
     │                                │ bcrypt.checkpw()               │
     │                                │ パスワード検証                  │
     │                                │                                │
     │                                │ JWT生成                         │
     │                                │ (DBには保存しない)              │
     │                                │                                │
     │ 200 OK                         │                                │
     │ {access_token: "eyJhbGci..."}  │                                │
     │<───────────────────────────────┤                                │
     │                                │                                │
     │ localStorage.setItem()         │                                │
     │ トークン保存                    │                                │
```

---

### API呼び出し

```
フロントエンド                    バックエンド                    データベース
     │                                │                                │
     │ localStorage.getItem()         │                                │
     │ トークン取得                    │                                │
     │                                │                                │
     │ GET /api/projects              │                                │
     │ Authorization: Bearer token    │                                │
     ├───────────────────────────────>│                                │
     │                                │ jwt.decode(token, SECRET_KEY)  │
     │                                │ 署名検証                        │
     │                                │                                │
     │                                │ payload取得                     │
     │                                │ {user_id: 123}                 │
     │                                │                                │
     │                                │ SELECT * FROM projects         │
     │                                │ WHERE user_id = 123            │
     │                                ├───────────────────────────────>│
     │                                │                                │
     │                                │ projects返却                    │
     │                                │<───────────────────────────────┤
     │ 200 OK                         │                                │
     │ {projects: [...]}              │                                │
     │<───────────────────────────────┤                                │
```

---

### ログアウト

```
フロントエンド                    バックエンド
     │                                │
     │ localStorage.removeItem()      │
     │ トークン削除                    │
     │                                │
     │ /loginにリダイレクト            │
     │                                │
     
     
（サーバー側は何もしない）
（トークンは有効期限まで使える）
```

---

## 実装設計

### データベース設計

#### usersテーブル

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### 既存テーブルの修正

```sql
-- projectsテーブルに user_id を追加
ALTER TABLE projects ADD COLUMN user_id INTEGER;
ALTER TABLE projects ADD FOREIGN KEY (user_id) REFERENCES users(id);

-- membersテーブルは変更なし
-- scoresテーブルは変更なし
```

---

### API設計

#### 新規エンドポイント

```
POST /api/auth/register
  Request:  {email, password, name}
  Response: {message: "登録完了"}

POST /api/auth/login
  Request:  {email, password}
  Response: {access_token: "eyJhbGci..."}

GET /api/auth/me
  Headers:  Authorization: Bearer <token>
  Response: {id, email, name}
```

---

#### 既存エンドポイントの修正

```python
# Before（認証なし）
@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

# After（認証あり）
@app.get("/api/projects")
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Project).filter(
        Project.user_id == current_user.id
    ).all()
```

---

### 認証ミドルウェア

```python
from fastapi import Depends, HTTPException, Header
import jwt

SECRET_KEY = "your-secret-key-here"  # 環境変数から取得

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Authorizationヘッダーからトークンを取得し、検証する
    """
    if not authorization:
        raise HTTPException(401, "Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # トークンを検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    
    # ユーザーを取得
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(401, "User not found")
    
    return user
```

---

### CORS設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ローカル開発
        "https://project-transparency.vercel.app"  # 本番
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 環境変数

```bash
# .env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./project_transparency.db
```

**SECRET_KEY の生成:**

```python
import secrets
print(secrets.token_urlsafe(32))
# → "rHk3j9dX2mP8qW5vY1nT7eR4aK6bN0oL"
```

---

## 今後の実装計画

### Phase 1: バックエンド実装（1週間）

**Day 1-2: 基礎実装**
- usersテーブル作成
- User モデル定義
- register エンドポイント
- login エンドポイント

**Day 3-4: 認証ミドルウェア**
- get_current_user 実装
- トークン検証ロジック
- エラーハンドリング

**Day 5-7: 既存API修正**
- 全エンドポイントに認証追加
- projectsテーブルに user_id 追加
- データの所有権チェック

---

### Phase 2: フロントエンド実装（1週間）

**Day 1-2: 認証画面**
- ログインページ作成
- 登録ページ作成
- フォームバリデーション

**Day 3-4: トークン管理**
- localStorage 連携
- API呼び出し時の Authorization ヘッダー追加
- トークン期限切れハンドリング

**Day 5-7: 既存画面修正**
- 未ログイン時のリダイレクト
- ログアウト機能
- ユーザー情報表示

---

### Phase 3: テストとデプロイ（3日）

**Day 1: テスト**
- Postman でAPI動作確認
- フロント・バック連携確認
- エッジケーステスト

**Day 2: デプロイ**
- Render に環境変数設定
- Vercel に環境変数設定
- 本番環境動作確認

**Day 3: ドキュメント整備**
- README更新
- API仕様書更新
- 運用マニュアル作成

---

## 学んだこと

### 技術的な学び

1. **JWT の仕組み**
   - 3パーツ構成（Header, Payload, Signature）
   - 署名による改ざん検知
   - ステートレスな認証

2. **bcrypt の必要性**
   - わざと遅くすることでセキュリティを高める
   - Salt の自動管理
   - コストの調整可能性

3. **セッション vs トークン**
   - サーバーの状態管理の違い
   - スケーラビリティの違い
   - それぞれのメリット・デメリット

4. **Cookie の役割**
   - ブラウザの状態保存
   - 自動送信の仕組み
   - セキュリティ属性

---

### 概念的な学び

1. **「保存しない」ことの強さ**
   - サーバーがトークンを保存しないからスケールする
   - トークン自体が情報を持つ
   - 検証は署名の再計算だけ

2. **ハッシュ化の本質**
   - 「元に戻す」のではなく「再計算して比較」
   - 同じ入力 + 同じ秘密鍵 → 同じ署名
   - 一方通行だからこそ安全

3. **認証の段階的理解**
   - 誰が（認証 - Authentication）
   - 何をできる（認可 - Authorization）
   - セキュリティの多層防御

---

## 参考資料

- **JWT公式**: https://jwt.io/
- **bcrypt**: https://github.com/pyca/bcrypt/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **OWASP認証チートシート**: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

---

**作成日**: 2025-11-16  
**バージョン**: 1.0  
**次のステップ**: 実装開始
