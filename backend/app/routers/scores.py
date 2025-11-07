from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.post("/members/{member_id}/scores", response_model=schemas.ScoreResponse, status_code=201)
def create_score(member_id: int, score: schemas.ScoreCreate, db: Session = Depends(get_db)):
    """メンバーのスコアを登録（履歴として追加）"""
    # メンバーの存在確認
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

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
def get_scores(member_id: int, db: Session = Depends(get_db)):
    """メンバーのスコア履歴を取得"""
    # メンバーの存在確認
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

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
