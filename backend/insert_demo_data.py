"""
デモデータ投入スクリプト
Renderのデータベースにデモデータを投入します
"""
import sys
import os
from datetime import datetime, timedelta

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(__file__))

from app.database import engine, SessionLocal, Base
from app.models import Project, Member, Score

def create_tables():
    """テーブルを作成"""
    print("テーブルを作成中...")
    Base.metadata.create_all(bind=engine)
    print("テーブルの作成完了")

def insert_demo_data():
    """デモデータを投入"""
    db = SessionLocal()

    try:
        # 既存のデータをチェック
        existing_projects = db.query(Project).count()
        if existing_projects > 0:
            print(f"既に{existing_projects}件のプロジェクトが存在します")
            response = input("既存のデータを削除して新しいデモデータを投入しますか？ (y/N): ")
            if response.lower() != 'y':
                print("キャンセルしました")
                return

            # 既存のデータを削除
            print("既存のデータを削除中...")
            db.query(Score).delete()
            db.query(Member).delete()
            db.query(Project).delete()
            db.commit()
            print("既存のデータを削除しました")

        print("デモデータを投入中...")

        # プロジェクト1: Webアプリケーション開発
        project1 = Project(
            name="ECサイトリニューアルプロジェクト",
            document_url="https://docs.google.com/document/d/example1"
        )
        db.add(project1)
        db.flush()  # IDを取得するためにflush

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
            # PM・PLは高めのスコア、Memberは徐々に上昇
            if member.role == "PM":
                scores = [92, 94, 95, 93, 96]
                comments = [
                    "プロジェクト全体を適切にリード",
                    "ステークホルダーとのコミュニケーションが良好",
                    "リスク管理が徹底されている",
                    "進捗管理が的確",
                    "チームの士気向上に貢献"
                ]
            elif member.role == "PL":
                scores = [88, 90, 92, 91, 93]
                comments = [
                    "技術的な判断が的確",
                    "メンバーへの技術指導が丁寧",
                    "コードレビューの質が高い",
                    "アーキテクチャ設計が優秀",
                    "チーム全体の生産性向上に貢献"
                ]
            else:
                # メンバーごとに異なる成長曲線
                if i == 2:  # 鈴木一郎
                    scores = [75, 78, 82, 85, 88]
                    comments = [
                        "基本的なタスクは完了できている",
                        "フロントエンド実装が向上",
                        "積極的に質問し学習している",
                        "コードの品質が改善",
                        "チームに貢献できるようになってきた"
                    ]
                elif i == 3:  # 田中美咲
                    scores = [82, 84, 86, 87, 90]
                    comments = [
                        "UIデザインのスキルが高い",
                        "ユーザー体験を重視した実装",
                        "レスポンシブ対応が的確",
                        "デザインの一貫性を保っている",
                        "優れたUI実装を継続"
                    ]
                else:  # 高橋健太
                    scores = [70, 72, 76, 80, 84]
                    comments = [
                        "新人ながら積極的に学習",
                        "バックエンド実装の基礎を習得",
                        "API実装のスキルが向上",
                        "エラーハンドリングが改善",
                        "着実に成長している"
                    ]

            for j, (score_value, comment) in enumerate(zip(scores, comments)):
                # 過去から現在にかけてのスコア
                created_date = base_date - timedelta(days=(len(scores) - 1 - j) * 7)
                score = Score(
                    member_id=member.id,
                    score=score_value,
                    comment=comment,
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
                comments = [
                    "プロジェクト管理が適切",
                    "スケジュール調整が上手",
                    "課題解決が迅速",
                    "ステークホルダー対応が良好",
                    "プロジェクトを成功に導いている"
                ]
            elif member.role == "PL":
                scores = [85, 87, 88, 90, 91]
                comments = [
                    "モバイル開発の知識が豊富",
                    "コードの品質管理が徹底",
                    "チーム開発を円滑に進行",
                    "技術的な課題を適切に解決",
                    "メンバーの成長をサポート"
                ]
            else:
                if i == 2:  # 中村大輔
                    scores = [78, 81, 83, 85, 87]
                    comments = [
                        "Android開発のスキルが高い",
                        "パフォーマンス最適化を実施",
                        "クリーンなコードを書けている",
                        "テストカバレッジが向上",
                        "継続的に高い成果を出している"
                    ]
                else:  # 小林あかり
                    scores = [80, 82, 84, 86, 88]
                    comments = [
                        "iOS開発の実力がある",
                        "SwiftUIの実装が優秀",
                        "アニメーションの実装が美しい",
                        "ユーザビリティを重視",
                        "安定した品質の実装を継続"
                    ]

            for j, (score_value, comment) in enumerate(zip(scores, comments)):
                created_date = base_date - timedelta(days=(len(scores) - 1 - j) * 7)
                score = Score(
                    member_id=member.id,
                    score=score_value,
                    comment=comment,
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
                comments = [
                    "データ基盤設計が優秀",
                    "スケーラビリティを考慮した設計",
                    "パフォーマンスチューニングが適切",
                    "ドキュメントが充実",
                    "プロジェクトを技術的にリード"
                ]
            else:
                if i == 1:  # 吉田麻衣
                    scores = [83, 85, 87, 88, 90]
                    comments = [
                        "データ処理パイプラインの実装が優秀",
                        "ETL処理の最適化を実施",
                        "エラーハンドリングが適切",
                        "データ品質管理を徹底",
                        "安定した高品質の成果"
                    ]
                else:  # 山口拓也
                    scores = [76, 79, 82, 84, 86]
                    comments = [
                        "データ可視化のスキルが向上",
                        "BIツールの活用が上手",
                        "ダッシュボード設計が改善",
                        "ユーザーニーズを理解した実装",
                        "継続的に成長している"
                    ]

            for j, (score_value, comment) in enumerate(zip(scores, comments)):
                created_date = base_date - timedelta(days=(len(scores) - 1 - j) * 7)
                score = Score(
                    member_id=member.id,
                    score=score_value,
                    comment=comment,
                    created_at=created_date.isoformat()
                )
                db.add(score)

        # コミット
        db.commit()
        print("\nデモデータの投入が完了しました！")
        print(f"- プロジェクト数: 3")
        print(f"- メンバー数: {len(members1) + len(members2) + len(members3)}")
        print(f"- スコア数: {(len(members1) + len(members2) + len(members3)) * 5}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=== デモデータ投入スクリプト ===")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set (using SQLite)')}")
    print()

    # テーブルを作成
    create_tables()
    print()

    # デモデータを投入
    insert_demo_data()
