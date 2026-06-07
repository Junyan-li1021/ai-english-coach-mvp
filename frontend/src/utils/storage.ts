export interface Session {
  id: string;
  createdAt: string;
  messages: Message[];
  scores?: Scores;
}

export interface Message {
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

export interface Scores {
  accuracy: number;    // 内容准确度 0-100
  fluency: number;     // 表达流利度 0-100
  overall: number;     // 综合评分
  feedback: string;    // 总评
}

const HISTORY_KEY = 'speakeasy_history';

export function saveSession(session: Session): void {
  const history = loadHistory();
  const idx = history.findIndex((s) => s.id === session.id);
  if (idx >= 0) {
    history[idx] = session;
  } else {
    history.unshift(session);
  }
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

export function loadSession(id: string): Session | null {
  const history = loadHistory();
  return history.find((s) => s.id === id) ?? null;
}

export function saveHistory(sessions: Session[]): void {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(sessions));
}

export function loadHistory(): Session[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function clearAll(): void {
  localStorage.removeItem(HISTORY_KEY);
}
