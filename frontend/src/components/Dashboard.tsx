import { DashboardData } from '@/lib/api';
import { ROLE_LABELS, ROLE_COLORS } from '@/lib/types';
import ScoreChart from './ScoreChart';

interface DashboardProps {
  data: DashboardData;
  onRefresh: () => void;
}

export default function Dashboard({ data, onRefresh }: DashboardProps) {
  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">加重平均スコア</h3>
        <div className="flex items-end gap-4">
          <div className="text-6xl font-bold text-blue-600">
            {data.weighted_average !== undefined && data.weighted_average !== null
              ? `${data.weighted_average}%`
              : '---'}
          </div>
          {data.last_updated && (
            <div className="text-sm text-gray-500 mb-2">
              最終更新: {new Date(data.last_updated).toLocaleString('ja-JP')}
            </div>
          )}
        </div>
        <p className="text-sm text-gray-600 mt-4">
          役職による重み付け: PL×3, PM×2, Member×1
        </p>
      </div>

      {/* Timeline Chart */}
      {data.timeline && data.timeline.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">スコア推移</h3>
          <ScoreChart data={data.timeline} />
        </div>
      )}

      {/* Members Summary */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">メンバー別スコア</h3>
        {data.members_summary.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            メンバーがまだ登録されていません
          </p>
        ) : (
          <div className="space-y-4">
            {data.members_summary.map((member) => (
              <div
                key={member.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-3">
                    <h4 className="font-semibold text-gray-900">{member.name}</h4>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${ROLE_COLORS[member.role]}`}>
                      {ROLE_LABELS[member.role]}
                    </span>
                    <span className="text-sm text-gray-500">
                      重み: {member.weight}
                    </span>
                  </div>
                  <div className="text-right">
                    {member.latest_score !== undefined && member.latest_score !== null ? (
                      <>
                        <div className="text-2xl font-bold text-blue-600">
                          {member.latest_score}%
                        </div>
                        {member.latest_score_at && (
                          <div className="text-xs text-gray-400 mt-1">
                            {new Date(member.latest_score_at).toLocaleString('ja-JP')}
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-gray-400 text-sm">未入力</div>
                    )}
                  </div>
                </div>
                {member.latest_comment && (
                  <div className="mt-2 p-3 bg-gray-50 rounded text-sm text-gray-700">
                    <p className="font-medium text-gray-600 mb-1">コメント:</p>
                    {member.latest_comment}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
