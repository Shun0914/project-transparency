# API設計（確定版）

## ベースURL
```
http://localhost:8000/api
```

## エンドポイント一覧

### 1. Projects（プロジェクト管理）

#### プロジェクト一覧取得
```
GET /api/projects
```
**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "プロジェクトA",
      "document_url": "https://confluence.example.com/...",
      "created_at": "2024-11-01T10:00:00Z"
    }
  ]
}
```

#### プロジェクト作成
```
POST /api/projects
```
**Request:**
```json
{
  "name": "プロジェクトA",
  "document_url": "https://confluence.example.com/..."
}
```
**Response:**
```json
{
  "id": 1,
  "name": "プロジェクトA",
  "document_url": "https://confluence.example.com/...",
  "created_at": "2024-11-01T10:00:00Z"
}
```

#### プロジェクト詳細取得
```
GET /api/projects/{project_id}
```
**Response:**
```json
{
  "id": 1,
  "name": "プロジェクトA",
  "document_url": "https://confluence.example.com/...",
  "created_at": "2024-11-01T10:00:00Z",
  "members": [
    {
      "id": 1,
      "name": "田中太郎",
      "role": "PL",
      "email": "tanaka@example.com"
    }
  ]
}
```

---

### 2. Members（メンバー管理）

#### メンバー追加
```
POST /api/projects/{project_id}/members
```
**Request:**
```json
{
  "name": "田中太郎",
  "role": "PL",  // "Member" | "PM" | "PL"
  "email": "tanaka@example.com"  // 任意
}
```
**Response:**
```json
{
  "id": 1,
  "project_id": 1,
  "name": "田中太郎",
  "role": "PL",
  "email": "tanaka@example.com",
  "created_at": "2024-11-01T10:00:00Z"
}
```

#### メンバー一覧取得
```
GET /api/projects/{project_id}/members
```
**Response:**
```json
{
  "members": [
    {
      "id": 1,
      "name": "田中太郎",
      "role": "PL",
      "email": "tanaka@example.com",
      "latest_score": 85,  // 最新のスコア（なければnull）
      "latest_score_at": "2024-11-08T15:30:00Z"
    }
  ]
}
```

---

### 3. Scores（スコアリング）

#### スコア登録・更新
```
POST /api/members/{member_id}/scores
```
**Request:**
```json
{
  "score": 85,  // 0-100
  "comment": "ドキュメントは充実してるが、トラブル対応のフローが不明"  // 任意
}
```
**Response:**
```json
{
  "id": 1,
  "member_id": 1,
  "score": 85,
  "comment": "ドキュメントは充実してるが、トラブル対応のフローが不明",
  "created_at": "2024-11-08T15:30:00Z"
}
```

#### 個人のスコア履歴取得
```
GET /api/members/{member_id}/scores
```
**Response:**
```json
{
  "member": {
    "id": 1,
    "name": "田中太郎",
    "role": "PL"
  },
  "scores": [
    {
      "id": 3,
      "score": 85,
      "comment": "...",
      "created_at": "2024-11-08T15:30:00Z"
    },
    {
      "id": 2,
      "score": 80,
      "comment": "...",
      "created_at": "2024-11-05T10:00:00Z"
    }
  ]
}
```

---

### 4. Dashboard（ダッシュボード統合API）

#### プロジェクトダッシュボードデータ取得
```
GET /api/projects/{project_id}/dashboard
```
**Response:**
```json
{
  "project": {
    "id": 1,
    "name": "プロジェクトA",
    "document_url": "https://confluence.example.com/..."
  },
  "weighted_average": 78.5,  // 加重平均スコア
  "last_updated": "2024-11-08T15:30:00Z",
  "members_summary": [
    {
      "id": 1,
      "name": "田中太郎",
      "role": "PL",
      "weight": 3,
      "latest_score": 85,
      "latest_comment": "...",
      "latest_score_at": "2024-11-08T15:30:00Z"
    },
    {
      "id": 2,
      "name": "佐藤花子",
      "role": "PM",
      "weight": 2,
      "latest_score": 75,
      "latest_comment": null,
      "latest_score_at": "2024-11-07T12:00:00Z"
    }
  ],
  "timeline": [
    {
      "date": "2024-11-01",
      "weighted_average": 70.0
    },
    {
      "date": "2024-11-05",
      "weighted_average": 75.0
    },
    {
      "date": "2024-11-08",
      "weighted_average": 78.5
    }
  ]
}
```

---

## 加重平均の計算ロジック

```python
def calculate_weighted_average(members_scores):
    """
    役職による重み付けで平均スコアを計算
    
    重み:
    - PL: 3
    - PM: 2
    - Member: 1
    """
    ROLE_WEIGHTS = {
        "PL": 3,
        "PM": 2,
        "Member": 1
    }
    
    weighted_sum = 0
    total_weight = 0
    
    for member in members_scores:
        weight = ROLE_WEIGHTS[member.role]
        weighted_sum += member.latest_score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0
```

---

## エラーレスポンス

### 404 Not Found
```json
{
  "detail": "Project not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid role. Must be one of: Member, PM, PL"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "score"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```
