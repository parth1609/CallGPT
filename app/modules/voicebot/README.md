# Voicebot Module — Exotel AgentStream Integration

## Overview
This module adds a WebSocket endpoint at `/voicebot` for handling real phone calls
from farmers via Exotel AgentStream. It uses the existing VoiceService (STT/TTS)
and LangGraph customer pipeline (RAG) to process voice queries.

## How It Works
1. Farmer calls an Exotel number assigned to a company
2. Exotel opens a WebSocket to `wss://<your-server>/voicebot`
3. Exotel sends `connected` → `start` → `media` (audio) → `stop` events
4. On `stop`, server transcribes audio → queries RAG pipeline → generates TTS response
5. Server sends back audio as a `media` event for Exotel to play to farmer
6. Connection stays open for multi-turn conversation

## Required Supabase Tables

Run the following SQL in your Supabase SQL Editor **before** using the voicebot endpoint:

```sql
-- Companies table: maps Exotel phone numbers to company buckets
CREATE TABLE IF NOT EXISTS companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_name TEXT NOT NULL,
    bucket_name TEXT NOT NULL,
    exotel_number TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Call logs table: records each conversation turn
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    caller_number TEXT NOT NULL,
    question TEXT,
    answer TEXT,
    called_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example: Insert a test company
-- INSERT INTO companies (company_name, bucket_name, exotel_number)
-- VALUES ('Test Farm Co', 'openai-bucket', '+91XXXXXXXXXX');
```

## Prerequisites
- `pydub` Python package (added to requirements.txt)
- `ffmpeg` installed on the deployment server (required by pydub for MP3→PCM conversion)
- Supabase tables created (see SQL above)
- At least one company row in the `companies` table

## Configuration
The voicebot uses the same environment variables as the rest of the app:
- `SUPABASE_URL`, `SUPABASE_KEY` — for company lookup and call logging
- `GROQ_API_KEY` — for STT (Whisper) and LLM
- `DATABASE_URL` — for LangGraph conversation persistence (checkpointer)
