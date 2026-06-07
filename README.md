# SpeakEasy - AI English Speaking Coach

An AI-powered English speaking practice tool for Chinese learners. Practice mock interviews with AI and get real-time feedback.

## Tech Stack

| Module | Technology |
|--------|-----------|
| Frontend | React 18 + TypeScript + Vite + TailwindCSS |
| Backend | Python 3.11 + FastAPI + WebSocket |
| ASR | Alibaba Cloud Speech (real-time streaming) |
| TTS | Alibaba Cloud Speech (streaming, English voice) |
| LLM | DeepSeek-V3 (dialogue + scoring) |
| Oral Evaluation | Youdao Zhiyun (pronunciation/fluency scoring) |
| Deployment | Alibaba Cloud ECS + Docker Compose + Nginx |

## Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/Junyan-li1021/ai-english-coach-mvp.git
cd ai-english-coach-mvp
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services
```bash
docker compose up --build
```

### 3. Open Browser
```
http://localhost
```

## Smoke Tests

Verify all API connections work before development:

```bash
cd backend
pip install -r requirements.txt
python tests/smoke/test_aliyun_asr.py    # Test ASR
python tests/smoke/test_aliyun_tts.py    # Test TTS
python tests/smoke/test_deepseek.py      # Test LLM
python tests/smoke/test_youdao_eval.py   # Test Oral Eval
python tests/smoke/test_full_chain.py    # Full pipeline
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/session` | POST | Create new session |
| `/api/session/{id}` | GET | Get session status |
| `/api/session/{id}/evaluate` | POST | Trigger evaluation |
| `/ws/interview/{id}` | WS | Real-time conversation |

## Development Plan

| Day | Issue | Goal |
|-----|-------|------|
| 0 | #2 | Smoke test all API connections |
| 1 | #3 | Project skeleton + voice pipeline |
| 2 | #4 | Multi-turn dialogue + state |
| 3 | #5 | Scoring + report + deploy |
| 4-7 | #6 | Polish + new scenarios |

## Environment Variables

See [.env.example](./.env.example) for all required variables.

## License

MIT
