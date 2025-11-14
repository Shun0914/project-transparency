from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Project, Member, Score

router = APIRouter()

@router.post("/seed-demo-data")
def seed_demo_data(db: Session = Depends(get_db)):
    """デモデータを投入するエンドポイント"""

    # 既存のデータをチェック
    existing_projects = db.query(Project).count()
    if existing_projects > 0:
        return {
            "message": f"既に{existing_projects}件のプロジェクトが存在します",
            "note": "既存のデータは削除されません"
        }

    # プロジェクト1: Webアプリケーション開発
    project1 = Project(
        name="ECサイトリニューアルプロジェクト",
        document_url="https://docs.google.com/document/d/example1"
    )
    db.add(project1)
    db.flush()

    # プロジェクト1のメンバー
    members1 = [
        Member(project_id=project1.id, name="山田太郎", role="PM", email="yamada@example.com"),
        Member(project_id=project1.id, name="佐藤花子", role="PL", email="sato@example.com"),
        Member(project_id=project1.id, name="鈴木一郎", role="Member", email="suzuki@example.com"),
        Member(project_id=project1.id, name="田中美咲", role="Member", email="tanaka@example.com"),
        Member(project_id=project1.id, name="高橋健太", role="Member", email="takahashi@example.com"),
    ]
    for member in members1:
        db.add(member)
    db.flush()

    # プロジェクト1のスコア（過去3ヶ月分）
    base_date = datetime.utcnow()
    for i, member in enumerate(members1):
        if member.role == "PM":
            scores = [92, 94, 95, 93, 96]
        elif member.role == "PL":
            scores = [88, 90, 92, 91, 93]
        else:
            if i == 2:  # 鈴木一郎
                scores = [75, 78, 82, 85, 88]
            elif i == 3:  # 田中美咲
                scores = [82, 84, 86, 87, 90]
            else:  # 高橋健太
                scores = [70, 72, 76, 80, 84]

        for j, score_value in enumerate(scores):
            created_date = base_date - timedelta(days=(len(scores) - 1 - j) * 7)
            score = Score(
                member_id=member.id,
                score=score_value,
                comment=f"Week {j+1} evaluation",
                created_at=created_date.isoformat()
            )
            db.add(score)

    # プロジェクト2: モバイルアプリ開発
    project2 = Project(
        name="社内業務アプリ開発",
        document_url="https://docs.google.com/document/d/example2"
    )
    db.add(project2)
    db.flush()

    # プロジェクト2のメンバー
    members2 = [
        Member(project_id=project2.id, name="伊藤誠", role="PM", email="ito@example.com"),
        Member(project_id=project2.id, name="渡辺優子", role="PL", email="watanabe@example.com"),
        Member(project_id=project2.id, name="中村大輔", role="Member", email="nakamura@example.com"),
        Member(project_id=project2.id, name="小林あかり", role="Member", email="kobayashi@example.com"),
    ]
    for member in members2:
        db.add(member)
    db.flush()

    # プロジェクト2のスコア
    for i, member in enumerate(members2):
        if member.role == "PM":
            scores = [90, 91, 89, 92, 94]
        elif member.role == "PL":
            scores = [85, 87, 88, 90, 91]
        else:
            if i == 2:  # 中村大輔
                scores = [78, 81, 83, 85, 87]
            else:  # 小林あかり
                scores = [80, 82, 84, 86, 88]

        for j, score_value in enumerate(scores):
            created_date = base_date - timedelta(days=(len(scores) - 1 - j) * 7)
            score = Score(
                member_id=member.id,
                score=score_value,
                comment=f"Week {j+1} evaluation",
                created_at=created_date.isoformat()
            )
            db.add(score)

    # プロジェクト3: データ分析基盤構築
    project3 = Project(
        name="データ分析基盤構築プロジェクト",
        document_url="https://docs.google.com/document/d/example3"
    )
    db.add(project3)
    db.flush()

    # プロジェクト3のメンバー
    members3 = [
        Member(project_id=project3.id, name="加藤雄介", role="PL", email="kato@example.com"),
        Member(project_id=project3.id, name="吉田麻衣", role="Member", email="yoshida@example.com"),
        Member(project_id=project3.id, name="山口拓也", role="Member", email="yamaguchi@example.com"),
    ]
    for member in members3:
        db.add(member)
    db.flush()

    # プロジェクト3のスコア
    for i, member in enumerate(members3):
        if member.role == "PL":
            scores = [91, 92, 90, 93, 94]
        else:
            if i == 1:  # 吉田麻衣
                scores = [83, 85, 87, 88, 90]
            else:  # 山口拓也
                scores = [76, 79, 82, 84, 86]

        for j, score_value in enumerate(scores):
            created_date = base_date - timedelta(days=(len(scores) - 1 - j) * 7)
            score = Score(
                member_id=member.id,
                score=score_value,
                comment=f"Week {j+1} evaluation",
                created_at=created_date.isoformat()
            )
            db.add(score)

    # コミット
    db.commit()

    total_members = len(members1) + len(members2) + len(members3)
    total_scores = total_members * 5

    return {
        "message": "デモデータの投入が完了しました",
        "projects": 3,
        "members": total_members,
        "scores": total_scores
    }
