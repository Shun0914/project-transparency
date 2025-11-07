-- ==========================================
-- DB設計（確定版）
-- ==========================================
-- 前提:
-- - プロジェクトごとにメンバーを登録
-- - ドキュメントURLは親ページ1つ（Confluence想定）
-- - スコア履歴は全て保存
-- - 役職による重み付け: PL=3, PM=2, Member=1
-- ==========================================

-- プロジェクト
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    document_url TEXT NOT NULL,  -- Confluenceの親ページURL（必須）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- メンバー
CREATE TABLE members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Member', 'PM', 'PL')),
    email TEXT,  -- 任意（将来の通知機能用）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- スコアリング履歴（全て保存）
CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
    comment TEXT,  -- 任意
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- ==========================================
-- インデックス（パフォーマンス最適化）
-- ==========================================
CREATE INDEX idx_members_project_id ON members(project_id);
CREATE INDEX idx_scores_member_id ON scores(member_id);
CREATE INDEX idx_scores_created_at ON scores(created_at);

-- ==========================================
-- 役職の重み付け（参考）
-- ==========================================
-- PL (Project Leader): 重み 3
-- PM (Project Manager): 重み 2
-- Member: 重み 1
--
-- 加重平均の計算:
-- weighted_avg = Σ(score × weight) / Σ(weight)
-- ==========================================
