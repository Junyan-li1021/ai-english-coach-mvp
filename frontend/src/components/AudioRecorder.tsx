import { useState, useRef, useCallback, useEffect } from 'react';
import { float32ToInt16 } from '../utils/audio';

interface AudioRecorderProps {
  onAudioChunk: (pcmInt16: Int16Array) => void;
  onStart?: () => void;
  onStop?: () => void;
}

export default function AudioRecorder({ onAudioChunk, onStart, onStop }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;

      // 使用 ScriptProcessorNode 采集 PCM（兼容性好）
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (event) => {
        const float32 = event.inputBuffer.getChannelData(0);
        const int16 = float32ToInt16(float32);
        onAudioChunk(int16);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      setIsRecording(true);
      onStart?.();
    } catch (err) {
      console.error('Failed to start recording:', err);
      alert('无法访问麦克风，请检查权限设置');
    }
  }, [onAudioChunk, onStart]);

  const stopRecording = useCallback(() => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close();

    processorRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;
    audioContextRef.current = null;

    setIsRecording(false);
    onStop?.();
  }, [onStop]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (isRecording) {
        processorRef.current?.disconnect();
        sourceRef.current?.disconnect();
        streamRef.current?.getTracks().forEach((t) => t.stop());
        audioContextRef.current?.close();
      }
    };
  }, []);

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        className={`w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl
          transition-all duration-200 select-none
          ${isRecording
            ? 'bg-red-500 scale-110 shadow-lg shadow-red-500/50'
            : 'bg-blue-500 hover:bg-blue-600 shadow-lg shadow-blue-500/30'
          }`}
      >
        {isRecording ? '⏹' : '🎤'}
      </button>
      <span className="text-sm text-gray-500">
        {isRecording ? '松开停止录音' : '按住说话'}
      </span>
    </div>
  );
}
