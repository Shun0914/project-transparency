# JWT認証実装 エラーレポート

## 概要
Project TransparencyアプリケーションへのJWT認証機能実装において発生したエラーと、その解決方法をまとめたレポートです。

実装日: 2025年11月15日

---

## エラー1: email-validatorモジュール未インストール

### エラー内容
```
ImportError: email-validator is not installed, run `pip install pydantic[email]`
```

### 発生状況
- バックエンドサーバー起動時に発生
- Pydanticの`EmailStr`型を使用するために必要なモジュールが不足

### 原因
- `requirements.txt`に`email-validator`が含まれていなかった
- Pydantic v2では`EmailStr`を使用する際に別途インストールが必要

### 解決方法
```bash
# 仮想環境内でインストール
cd backend
source venv/bin/activate
pip install email-validator==2.1.1
```

requirements.txtに追加:
```
email-validator==2.1.1
```

### 教訓
- Pydanticのオプション機能（EmailStr, HttpUrlなど）は追加パッケージが必要
- requirements.txtには全ての依存関係を明記すべき

---

## エラー2: bcryptパスワード長制限エラー

### エラー内容
```
ValueError: password cannot be longer than 72 bytes
```

### 発生状況
- ユーザー登録時、特殊文字を含む長いパスワードでエラー
- テストパスワード: `mJA!MChb5g5p8xsXnJ2$Bw%o`

### 原因
1. bcryptは72バイトまでのパスワードしか処理できない（アルゴリズム仕様）
2. bcrypt 5.0.0以降では、72バイトを超えるとエラーを発生させる（セキュリティ強化）
3. しかし、passlib 1.7.4がbcrypt 5.x以降のAPIに対応していない

### 試行した解決策

#### 試行1: パスワード切り詰めロジック（不採用）
```python
# auth.pyで72バイトに切り詰める処理を追加
password_bytes = password.encode('utf-8')[:72]
truncated_password = password_bytes.decode('utf-8', errors='ignore')
```
**結果**: bcrypt初期化時のエラーは解決せず

#### 試行2: bcrypt設定で許可（不採用）
```python
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=True
)
```
**結果**: passlib 1.7.4がこのオプションをサポートしていない

#### 最終解決策: bcryptバージョンダウングレード（採用）
```bash
pip uninstall bcrypt
pip install bcrypt==3.2.0
```

requirements.txtを更新:
```
bcrypt==3.2.0  # passlib 1.7.4との互換性のため
```

### 採用理由
- bcrypt 3.2.0はpasslib 1.7.4と完全互換
- 72バイトを超えるパスワードを自動で切り詰める（警告なし）
- セキュリティ上は問題なし（72バイトでも十分に強力）

### 教訓
- passlibのバージョンとbcryptのバージョンは互換性を確認する必要がある
- パスワードハッシュライブラリは慎重にバージョン管理すべき
- アルゴリズムの仕様制限（72バイト）を理解しておく

---

## エラー3: JWT "sub"クレーム型エラー

### エラー内容
```
jose.exceptions.JWTError: Subject must be a string.
```

### 発生状況
- ユーザー登録・ログイン後、認証が必要なAPIにアクセスすると401エラー
- サーバーログにJWTErrorが記録される

### 原因
JWT仕様（RFC 7519）では、`sub`（Subject）クレームは**文字列でなければならない**が、ユーザーIDを整数のまま渡していた:

```python
# 誤った実装
access_token = create_access_token(data={"sub": user.id})  # user.idはint型
```

### 解決方法
JWTトークン生成時に、ユーザーIDを文字列に変換:

```python
# auth.py - register_user, login_user
access_token = create_access_token(data={"sub": str(new_user.id)})
```

デコード時は整数に戻す:

```python
# auth.py - decode_access_token
def decode_access_token(token: str) -> TokenData:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    # 整数に変換
    user_id = int(user_id)
    token_data = TokenData(user_id=user_id)
    return token_data
```

### 教訓
- JWT標準仕様を遵守することが重要
- `sub`クレームは必ず文字列型にする
- データベースIDは整数でも、JWTでは文字列として扱う

---

## エラー4: データベーススキーマ不一致エラー

### エラー内容
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: projects.user_id
```

### 発生状況
- 認証機能実装後、既存データベースを使用してプロジェクト一覧取得時にエラー
- ユーザー登録とログインは成功している

### 原因
- `models.py`で`Project`モデルに`user_id`カラムを追加
- しかし、既存のSQLiteデータベースファイルには新しいカラムが存在しない
- SQLAlchemyの`create_all()`は既存テーブルを変更しない

### 解決方法
**開発環境**: データベースファイルを削除して再作成

```bash
# 既存データベースを削除
rm backend/project_transparency.db

# サーバー再起動（自動的に新しいスキーマでテーブル作成）
uvicorn app.main:app --reload
```

**本番環境**: マイグレーションツール（Alembic）を使用すべき

```bash
# 将来的な対応（推奨）
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Add user_id to projects"
alembic upgrade head
```

### 教訓
- モデル変更時はマイグレーション戦略が必要
- 開発初期段階ではDB削除で対応可能だが、本番では不可
- Alembicなどのマイグレーションツールの導入を検討すべき

---

## デバッグログの活用

実装中、以下のデバッグログを追加したことで問題の特定が容易になりました:

```python
# auth.py
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # ...
    print(f"DEBUG: Created token with data: {data}")
    print(f"DEBUG: Token: {encoded_jwt[:50]}...")
    return encoded_jwt

def decode_access_token(token: str) -> TokenData:
    # ...
    print(f"DEBUG: Decoded payload: {payload}")
    print(f"DEBUG: Extracted user_id: {user_id}, type: {type(user_id)}")
    # ...
```

```typescript
// frontend/src/lib/auth.ts
export const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
  console.log('[AUTH] Logging in...');
  const response = await axios.post<AuthResponse>(...);
  console.log('[AUTH] Login successful, token:', response.data.access_token.substring(0, 20) + '...');
  console.log('[AUTH] Token saved to localStorage');
  // ...
};
```

### 推奨事項
本番環境では、これらのデバッグログを削除または環境変数で制御すべき:

```python
import os
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if DEBUG:
    print(f"DEBUG: Token: {encoded_jwt[:50]}...")
```

---

## まとめ

### 実装完了までの主なステップ
1. ✅ 依存関係の追加（email-validator, python-jose, passlib, bcrypt）
2. ✅ バージョン互換性の解決（bcrypt 3.2.0）
3. ✅ JWT仕様準拠（subクレームを文字列に）
4. ✅ データベーススキーマ更新（user_id追加）

### 学んだベストプラクティス
- **依存関係管理**: バージョン互換性を明示的に記載
- **JWT実装**: 標準仕様（RFC 7519）を遵守
- **デバッグ**: 詳細なログ出力で問題を早期発見
- **スキーマ管理**: マイグレーション戦略の重要性

### 今後の改善提案
1. Alembicを導入してマイグレーション管理を行う
2. デバッグログを環境変数で制御
3. パスワード要件（最小長、複雑さ）をバリデーションに追加
4. トークンのリフレッシュ機能を実装
5. レート制限（ログイン試行回数制限）を追加

---

## 参考資料
- [JWT RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [passlib Documentation](https://passlib.readthedocs.io/)
- [bcrypt Specification](https://en.wikipedia.org/wiki/Bcrypt)
