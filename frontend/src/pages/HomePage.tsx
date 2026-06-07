import { useNavigate } from 'react-router-dom';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 mb-4">
          SpeakEasy
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          AI 驱动的英语口语面试练习平台
        </p>
        <p className="text-gray-400 mb-10 max-w-md mx-auto">
          通过实时语音对话，模拟真实面试场景，获得即时的发音与表达反馈
        </p>
        <button
          onClick={() => {
            // 生成随机 sessionId 后跳转
            const sessionId = crypto.randomUUID().slice(0, 8);
            navigate(`/practice/${sessionId}`);
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold
            px-8 py-4 rounded-xl text-lg shadow-lg shadow-blue-500/30
            transition-all duration-200 hover:scale-105"
        >
          开始面试练习
        </button>
      </div>
      <div className="mt-16 flex gap-8 text-center text-gray-500 text-sm">
        <div>
          <div className="text-3xl mb-1">🎙️</div>
          <div>实时语音识别</div>
        </div>
        <div>
          <div className="text-3xl mb-1">🤖</div>
          <div>AI 智能对话</div>
        </div>
        <div>
          <div className="text-3xl mb-1">📊</div>
          <div>详细评分报告</div>
        </div>
      </div>
    </div>
  );
}
