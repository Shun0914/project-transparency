from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/projects", response_model=schemas.ProjectListResponse)
def get_projects(db: Session = Depends(get_db)):
    """プロジェクト一覧を取得"""
    projects = db.query(models.Project).order_by(models.Project.created_at.desc()).all()
    return {"projects": projects}


@router.post("/projects", response_model=schemas.ProjectResponse, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """プロジェクトを作成"""
    db_project = models.Project(
        name=project.name,
        document_url=project.document_url
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/projects/{project_id}", response_model=schemas.ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """プロジェクト詳細を取得（メンバー含む）"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
