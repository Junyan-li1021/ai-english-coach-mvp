import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AudioRecorder from '../components/AudioRecorder';
import ChatBubble from '../components/ChatBubble';
import { useWebSocket } from '../hooks/useWebSocket';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

// Mock 数据用于 UI 展示
const MOCK_MESSAGES: Message[] = [
  {
    role: 'assistant',
    text: 'Hello! Welcome to your mock interview. Let\'s start with a simple question: Can you tell me about yourself?',
    timestamp: '10:00',
  },
];

export default function PracticePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
  const [partialText, setPartialText] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const { status, connect, disconnect, sendAudioChunk } = useWebSocket({
    sessionId: sessionId ?? '',
    onPartialResult: (text) => setPartialText(text),
    onFinalResult: (text) => {
      setPartialText('');
      setMessages((prev) => [
        ...prev,
        { role: 'user', text, timestamp: new Date().toLocaleTimeString() },
      ]);
    },
    onLLMReply: (text) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text, timestamp: new Date().toLocaleTimeString() },
      ]);
    },
    onError: () => {
      console.error('WebSocket error');
    },
  });

  // 自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, partialText]);

  // 结束练习
  const endPractice = () => {
    disconnect();
    navigate(`/report/${sessionId}`);
  };

  const statusText =
    status === 'connected'
      ? '已连接'
      : status === 'connecting'
      ? '连接中...'
      : '未连接';

  const statusColor =
    status === 'connected'
      ? 'bg-green-500'
      : status === 'connecting'
      ? 'bg-yellow-500'
      : 'bg-gray-400';

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 顶部栏 */}
      <div className="flex items-center justify-between px-4 py-3 bg-white shadow-sm">
        <button
          onClick={() => navigate('/')}
          className="text-gray-500 hover:text-gray-700 text-sm"
        >
          ← 返回
        </button>
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${statusColor}`} />
          <span className="text-sm text-gray-600">{statusText}</span>
        </div>
        <button
          onClick={connect}
          className="text-xs text-blue-500 hover:text-blue-700 mr-2"
        >
          连接
        </button>
        <button
          onClick={endPractice}
          className="text-sm text-red-500 hover:text-red-700 font-medium"
        >
          结束练习
        </button>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.map((msg, i) => (
          <ChatBubble key={i} {...msg} />
        ))}
        {partialText && (
          <ChatBubble role="user" text={partialText + '...'} />
        )}
        <div ref={bottomRef} />
      </div>

      {/* 底部录音区域 */}
      <div className="bg-white border-t border-gray-200 px-4 py-4 flex flex-col items-center">
        <AudioRecorder
          onAudioChunk={sendAudioChunk}
          onStart={() => console.log('Recording started')}
          onStop={() => console.log('Recording stopped')}
        />
      </div>
    </div>
  );
}
