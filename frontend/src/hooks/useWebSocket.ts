import { useRef, useEffect, useCallback, useState } from 'react';
import { float32ToInt16, int16ToBase64 } from '../utils/audio';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected';

interface UseWebSocketOptions {
  sessionId: string;
  onPartialResult?: (text: string) => void;
  onFinalResult?: (text: string) => void;
  onLLMReply?: (text: string) => void;
  onTTSAudio?: (audioBase64: string) => void;
  onError?: (error: Event) => void;
}

export function useWebSocket({
  sessionId,
  onPartialResult,
  onFinalResult,
  onLLMReply,
  onTTSAudio,
  onError,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // TODO: 替换为真实后端地址
    const url = `ws://localhost:8000/ws/interview/${sessionId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    setStatus('connecting');

    ws.onopen = () => {
      setStatus('connected');
      // 心跳保活：每 20s 发 ping
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 20000);
    };

    ws.onclose = () => {
      setStatus('disconnected');
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
    };

    ws.onerror = (event) => {
      onError?.(event);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'asr_partial':
            onPartialResult?.(data.text);
            break;
          case 'asr_final':
            onFinalResult?.(data.text);
            break;
          case 'llm_reply':
            onLLMReply?.(data.text);
            break;
          case 'tts_audio':
            onTTSAudio?.(data.audio);
            break;
        }
      } catch {
        // 非 JSON 消息忽略
      }
    };
  }, [sessionId, onPartialResult, onFinalResult, onLLMReply, onTTSAudio, onError]);

  const disconnect = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
    setStatus('disconnected');
  }, []);

  // 发送音频分片（base64 编码的 PCM Int16）
  const sendAudioChunk = useCallback((pcmInt16: Int16Array) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const base64 = int16ToBase64(pcmInt16);
      wsRef.current.send(JSON.stringify({
        type: 'audio_chunk',
        audio: base64,
      }));
    }
  }, []);

  // 发送文本消息
  const sendText = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'text',
        text,
      }));
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    connect,
    disconnect,
    sendAudioChunk,
    sendText,
  };
}
