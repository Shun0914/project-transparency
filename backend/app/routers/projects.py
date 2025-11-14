from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter()


@router.get("/projects", response_model=schemas.ProjectListResponse)
def get_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """プロジェクト一覧を取得（自分のプロジェクトのみ）"""
    projects = db.query(models.Project)\
        .filter(models.Project.user_id == current_user.id)\
        .order_by(models.Project.created_at.desc())\
        .all()
    return {"projects": projects}


@router.post("/projects", response_model=schemas.ProjectResponse, status_code=201)
def create_project(
    project: schemas.ProjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """プロジェクトを作成"""
    db_project = models.Project(
        name=project.name,
        document_url=project.document_url,
        user_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/projects/{project_id}", response_model=schemas.ProjectDetailResponse)
def get_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """プロジェクト詳細を取得（メンバー含む）"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 所有権チェック
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このプロジェクトにアクセスする権限がありません"
        )

    return project
