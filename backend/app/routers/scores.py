from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter()


def verify_member_ownership(member_id: int, user_id: int, db: Session):
    """メンバーの所有権を確認する（プロジェクト経由）"""
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    project = db.query(models.Project).filter(models.Project.id == member.project_id).first()
    if not project or project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このメンバーにアクセスする権限がありません"
        )
    return member


@router.post("/members/{member_id}/scores", response_model=schemas.ScoreResponse, status_code=201)
def create_score(
    member_id: int,
    score: schemas.ScoreCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """メンバーのスコアを登録（履歴として追加）"""
    # メンバーの所有権チェック
    verify_member_ownership(member_id, current_user.id, db)

    # スコアの作成
    db_score = models.Score(
        member_id=member_id,
        score=score.score,
        comment=score.comment
    )
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score


@router.get("/members/{member_id}/scores", response_model=schemas.ScoreHistoryResponse)
def get_scores(
    member_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """メンバーのスコア履歴を取得"""
    # メンバーの所有権チェック
    member = verify_member_ownership(member_id, current_user.id, db)

    # スコア履歴を取得（新しい順）
    scores = db.query(models.Score)\
        .filter(models.Score.member_id == member_id)\
        .order_by(models.Score.created_at.desc())\
        .all()

    return {
        "member": {
            "id": member.id,
            "name": member.name,
            "role": member.role
        },
        "scores": scores
    }
