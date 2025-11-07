'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getMembers, createScore, getProject, MemberWithScore, Project } from '@/lib/api';
import { ROLE_LABELS, ROLE_COLORS } from '@/lib/types';

export default function ScoringPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const projectId = parseInt(params.id);

  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<MemberWithScore[]>([]);
  const [scores, setScores] = useState<{ [memberId: number]: { score: number; comment: string } }>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [projectData, membersData] = await Promise.all([
        getProject(projectId),
        getMembers(projectId)
      ]);
      setProject(projectData);
      setMembers(membersData);

      // Initialize scores with current values
      const initialScores: { [memberId: number]: { score: number; comment: string } } = {};
      membersData.forEach(member => {
        initialScores[member.id] = {
          score: member.latest_score || 50,
          comment: ''
        };
      });
      setScores(initialScores);

      setError('');
    } catch (err) {
      setError('データの読み込みに失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleScoreChange = (memberId: number, score: number) => {
    setScores(prev => ({
      ...prev,
      [memberId]: { ...prev[memberId], score }
    }));
  };

  const handleCommentChange = (memberId: number, comment: string) => {
    setScores(prev => ({
      ...prev,
      [memberId]: { ...prev[memberId], comment }
    }));
  };

  const handleSubmit = async (memberId: number) => {
    try {
      setSubmitting(true);
      setError('');
      setSuccess('');

      const scoreData = scores[memberId];
      await createScore(memberId, {
        score: scoreData.score,
        comment: scoreData.comment || undefined
      });

      setSuccess('スコアを登録しました');

      // Clear comment after submission
      setScores(prev => ({
        ...prev,
        [memberId]: { ...prev[memberId], comment: '' }
      }));

      // Reload data to show updated scores
      await loadData();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('スコアの登録に失敗しました');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  if (!project || members.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">メンバーが登録されていません</p>
        <button
          onClick={() => router.push(`/projects/${projectId}`)}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          ダッシュボードに戻る
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <button
          onClick={() => router.push(`/projects/${projectId}`)}
          className="text-blue-600 hover:text-blue-800 mb-4 flex items-center"
        >
          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          ダッシュボードに戻る
        </button>

        <h2 className="text-3xl font-bold text-gray-900 mb-2">スコア入力</h2>
        <p className="text-gray-600">{project.name}</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4">
          {success}
        </div>
      )}

      <div className="space-y-6">
        {members.map((member) => (
          <div key={member.id} className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{member.name}</h3>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${ROLE_COLORS[member.role]}`}>
                  {ROLE_LABELS[member.role]}
                </span>
                {member.latest_score !== undefined && (
                  <p className="text-sm text-gray-500 mt-2">
                    現在のスコア: {member.latest_score}%
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    スコア: {scores[member.id]?.score || 50}%
                  </label>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={scores[member.id]?.score || 50}
                  onChange={(e) => handleScoreChange(member.id, parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  コメント（任意）
                </label>
                <textarea
                  value={scores[member.id]?.comment || ''}
                  onChange={(e) => handleCommentChange(member.id, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="スコアの理由や改善点など..."
                />
              </div>

              <button
                onClick={() => handleSubmit(member.id)}
                disabled={submitting}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                {submitting ? '登録中...' : 'スコアを登録'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
