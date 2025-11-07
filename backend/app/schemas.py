from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# ========== Project Schemas ==========

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, description="プロジェクト名")
    document_url: str = Field(..., min_length=1, description="ドキュメントURL")


class ProjectResponse(BaseModel):
    id: int
    name: str
    document_url: str
    created_at: str

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]


# ========== Member Schemas ==========

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, description="メンバー名")
    role: str = Field(..., description="役職 (Member, PM, PL)")
    email: Optional[str] = Field(None, description="メールアドレス（任意）")

    @field_validator('role')
    def validate_role(cls, v):
        if v not in ['Member', 'PM', 'PL']:
            raise ValueError('role must be one of: Member, PM, PL')
        return v


class MemberResponse(BaseModel):
    id: int
    project_id: int
    name: str
    role: str
    email: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class MemberWithLatestScore(BaseModel):
    id: int
    name: str
    role: str
    email: Optional[str]
    latest_score: Optional[int] = None
    latest_score_at: Optional[str] = None


class MemberListResponse(BaseModel):
    members: List[MemberWithLatestScore]


# ========== Score Schemas ==========

class ScoreCreate(BaseModel):
    score: int = Field(..., ge=0, le=100, description="スコア (0-100)")
    comment: Optional[str] = Field(None, description="コメント（任意）")


class ScoreResponse(BaseModel):
    id: int
    member_id: int
    score: int
    comment: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class MemberInfo(BaseModel):
    id: int
    name: str
    role: str


class ScoreHistoryResponse(BaseModel):
    member: MemberInfo
    scores: List[ScoreResponse]


# ========== Dashboard Schemas ==========

class ProjectInfo(BaseModel):
    id: int
    name: str
    document_url: str


class MemberSummary(BaseModel):
    id: int
    name: str
    role: str
    weight: int
    latest_score: Optional[int]
    latest_comment: Optional[str]
    latest_score_at: Optional[str]


class TimelinePoint(BaseModel):
    date: str
    weighted_average: float


class DashboardResponse(BaseModel):
    project: ProjectInfo
    weighted_average: Optional[float]
    last_updated: Optional[str]
    members_summary: List[MemberSummary]
    timeline: List[TimelinePoint]


# ========== Project Detail Schema ==========

class ProjectDetailResponse(BaseModel):
    id: int
    name: str
    document_url: str
    created_at: str
    members: List[MemberResponse]

    class Config:
        from_attributes = True
