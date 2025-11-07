from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.post("/projects/{project_id}/members", response_model=schemas.MemberResponse, status_code=201)
def create_member(project_id: int, member: schemas.MemberCreate, db: Session = Depends(get_db)):
    """プロジェクトにメンバーを追加"""
    # プロジェクトの存在確認
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # メンバーの作成
    db_member = models.Member(
        project_id=project_id,
        name=member.name,
        role=member.role,
        email=member.email
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.get("/projects/{project_id}/members", response_model=schemas.MemberListResponse)
def get_members(project_id: int, db: Session = Depends(get_db)):
    """プロジェクトのメンバー一覧を取得（最新スコア付き）"""
    # プロジェクトの存在確認
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # メンバーを取得
    members = db.query(models.Member).filter(models.Member.project_id == project_id).all()

    # 各メンバーの最新スコアを取得
    result = []
    for member in members:
        latest_score = db.query(models.Score)\
            .filter(models.Score.member_id == member.id)\
            .order_by(models.Score.created_at.desc())\
            .first()

        result.append({
            "id": member.id,
            "name": member.name,
            "role": member.role,
            "email": member.email,
            "latest_score": latest_score.score if latest_score else None,
            "latest_score_at": latest_score.created_at if latest_score else None
        })

    return {"members": result}
