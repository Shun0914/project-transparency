from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime
from collections import defaultdict
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter()

# 役職の重み
ROLE_WEIGHTS = {
    "PL": 3,
    "PM": 2,
    "Member": 1
}


def calculate_weighted_average(members_with_scores: List[Dict]) -> float:
    """加重平均スコアを計算"""
    weighted_sum = 0
    total_weight = 0

    for member in members_with_scores:
        if member["latest_score"] is not None:
            weight = ROLE_WEIGHTS.get(member["role"], 1)
            weighted_sum += member["latest_score"] * weight
            total_weight += weight

    return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0


@router.get("/projects/{project_id}/dashboard", response_model=schemas.DashboardResponse)
def get_dashboard(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """プロジェクトのダッシュボードデータを取得"""
    # プロジェクトの存在確認と所有権チェック
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このプロジェクトにアクセスする権限がありません"
        )

    # プロジェクト情報
    project_info = {
        "id": project.id,
        "name": project.name,
        "document_url": project.document_url
    }

    # メンバー一覧を取得
    members = db.query(models.Member).filter(models.Member.project_id == project_id).all()

    # 各メンバーの最新スコアを取得
    members_summary = []
    last_updated = None

    for member in members:
        latest_score = db.query(models.Score)\
            .filter(models.Score.member_id == member.id)\
            .order_by(models.Score.created_at.desc())\
            .first()

        members_summary.append({
            "id": member.id,
            "name": member.name,
            "role": member.role,
            "weight": ROLE_WEIGHTS.get(member.role, 1),
            "latest_score": latest_score.score if latest_score else None,
            "latest_comment": latest_score.comment if latest_score else None,
            "latest_score_at": latest_score.created_at if latest_score else None
        })

        # 最終更新日時を取得
        if latest_score and (last_updated is None or latest_score.created_at > last_updated):
            last_updated = latest_score.created_at

    # 加重平均スコアを計算
    weighted_average = calculate_weighted_average(members_summary)

    # タイムラインの生成（日付ごとの加重平均）
    timeline = []

    # 全てのスコアを取得（プロジェクトのメンバーのスコア）
    member_ids = [m.id for m in members]
    if member_ids:
        all_scores = db.query(models.Score)\
            .filter(models.Score.member_id.in_(member_ids))\
            .order_by(models.Score.created_at.asc())\
            .all()

        # 日付ごとにグループ化
        scores_by_date = defaultdict(list)
        for score in all_scores:
            # ISO形式の日付から日付部分のみを抽出
            date_str = score.created_at[:10]  # "2024-11-08"
            scores_by_date[date_str].append(score)

        # 各日付での最新スコアで加重平均を計算
        for date_str in sorted(scores_by_date.keys()):
            # その日付までの各メンバーの最新スコアを取得
            member_scores_at_date = {}
            for member in members:
                # その日付までのスコアを取得
                scores_until_date = db.query(models.Score)\
                    .filter(
                        models.Score.member_id == member.id,
                        models.Score.created_at <= date_str + "T23:59:59"
                    )\
                    .order_by(models.Score.created_at.desc())\
                    .first()

                if scores_until_date:
                    member_scores_at_date[member.id] = {
                        "role": member.role,
                        "latest_score": scores_until_date.score
                    }

            # その日付での加重平均を計算
            if member_scores_at_date:
                weighted_sum = 0
                total_weight = 0
                for member_id, data in member_scores_at_date.items():
                    weight = ROLE_WEIGHTS.get(data["role"], 1)
                    weighted_sum += data["latest_score"] * weight
                    total_weight += weight

                avg = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0
                timeline.append({
                    "date": date_str,
                    "weighted_average": avg
                })

    return {
        "project": project_info,
        "weighted_average": weighted_average if members_summary else None,
        "last_updated": last_updated,
        "members_summary": members_summary,
        "timeline": timeline
    }
