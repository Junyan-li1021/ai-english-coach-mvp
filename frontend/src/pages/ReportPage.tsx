import { useNavigate, useParams } from 'react-router-dom';
import ScoreCard from '../components/ScoreCard';
import ChatBubble from '../components/ChatBubble';

// Mock 数据
const MOCK_SCORES = {
  accuracy: 82,
  fluency: 75,
  overall: 78,
  feedback: '整体表现不错，内容准确度较高。建议注意语速控制和连读练习，提升流利度。',
};

const MOCK_REVIEW = [
  {
    role: 'assistant' as const,
    text: 'Can you tell me about yourself?',
    timestamp: '10:00',
  },
  {
    role: 'user' as const,
    text: 'My name is Li Ming. I have five years of experience in software development, specializing in web applications.',
    timestamp: '10:15',
  },
  {
    role: 'assistant' as const,
    text: 'That\'s a good introduction. Can you describe a challenging project you\'ve worked on?',
    timestamp: '10:20',
  },
  {
    role: 'user' as const,
    text: 'Sure. Last year I led a team to rebuild our payment system, which handled over one million transactions per day.',
    timestamp: '10:35',
  },
];

export default function ReportPage() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* 顶部栏 */}
      <div className="flex items-center justify-between px-4 py-3 bg-white shadow-sm">
        <button
          onClick={() => navigate('/')}
          className="text-gray-500 hover:text-gray-700 text-sm"
        >
          ← 返回首页
        </button>
        <h2 className="font-semibold text-gray-800">练习报告</h2>
        <div className="w-16" />
      </div>

      <div className="max-w-lg mx-auto px-4 mt-6 space-y-6">
        {/* 评分卡片 */}
        <ScoreCard scores={MOCK_SCORES} />

        {/* 逐句回顾 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">逐句回顾</h3>
          <div className="space-y-1">
            {MOCK_REVIEW.map((msg, i) => (
              <ChatBubble key={i} {...msg} />
            ))}
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/')}
            className="flex-1 py-3 rounded-xl border border-gray-300 text-gray-700
              font-medium hover:bg-gray-50 transition"
          >
            返回首页
          </button>
          <button
            onClick={() => {
              const newId = crypto.randomUUID().slice(0, 8);
              navigate(`/practice/${newId}`);
            }}
            className="flex-1 py-3 rounded-xl bg-blue-600 text-white
              font-medium hover:bg-blue-700 transition shadow-lg shadow-blue-500/30"
          >
            再练一次
          </button>
        </div>
      </div>
    </div>
  );
}
