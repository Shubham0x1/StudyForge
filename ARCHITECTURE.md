# AI Classroom Platform — Architecture

## Overview

The AI Classroom Platform is a FastAPI-based backend that converts lecture audio or PDF files into interactive educational content — study notes, MCQ questions, automated answer evaluation, and performance analytics.

**Problem**: Instructors record lectures but students lack structured study material and self-assessment tools.

**Solution**: A pipeline that automatically transcribes lectures, generates notes and quizzes, evaluates student answers semantically, and provides topic-wise performance analytics.

---

## Project Structure

```
AI-Classroom-Platform/
├── app.py                 # FastAPI orchestrator — REST endpoints
├── asr_whisper.py         # Hybrid Whisper ASR (local, two-pass)
├── asr_gemini.py          # Gemini ASR (cloud-based, alternative)
├── llm_gemini.py          # Content generation — notes + MCQs via Gemini
├── rag.py                 # Vector store — FAISS indexing + retrieval
├── evaluation.py          # Answer scoring — semantic similarity
├── utils.py               # Text cleaning, PDF/DOCX extraction
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (GEMINI_API_KEY)
└── Data/
    └── uploads/           # Uploaded lecture files (audio/PDF)
```

---

## System Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                     Instructor                          │
│              Uploads Audio / PDF File                   │
└────────────────────────┬────────────────────────────────┘
                         │  POST /upload-lecture
                         ▼
┌─────────────────────────────────────────────────────────┐
│               Stage 1: Transcription                    │
│                                                         │
│  Audio ──► asr_whisper.py (Hybrid Whisper ASR)          │
│              ├─ Pass 1: distil-small.en (fast, cheap)   │
│              │     │                                    │
│              │     ├── confidence >= -0.5 → keep text   │
│              │     └── confidence <  -0.5 → re-transcribe│
│              │                                  │       │
│              └─ Pass 2: medium.en (accurate) ◄──┘       │
│                                                         │
│  PDF   ──► utils.py (PyPDF2 text extraction + cleaning) │
└────────────────────────┬────────────────────────────────┘
                         │ cleaned transcript
                         ▼
┌─────────────────────────────────────────────────────────┐
│               Stage 2: RAG Indexing                     │
│                      rag.py                             │
│                                                         │
│  1. Chunk text (500 chars, 50-char overlap)             │
│  2. Embed with all-MiniLM-L6-v2 (384-dim vectors)      │
│  3. Store in FAISS IndexFlatL2 (exact L2 search)        │
│                                                         │
│  Purpose: enables semantic retrieval during evaluation  │
└────────────────────────┬────────────────────────────────┘
                         │ indexed in VECTOR_DB
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Stage 3: Content Generation                  │
│                   llm_gemini.py                         │
│                                                         │
│  Model: Gemini 2.5 Flash Lite                           │
│                                                         │
│  Input:  lecture transcript                              │
│  Output: JSON with:                                     │
│    ├─ "notes"     → structured study notes (string)     │
│    └─ "questions" → 10 MCQs, each with:                 │
│         { id, question, options[4], correct, topic }    │
└────────────────────────┬────────────────────────────────┘
                         │ notes + questions
                         ▼
┌─────────────────────────────────────────────────────────┐
│               In-Memory Cache                           │
│                                                         │
│  LECTURES  { lecture_id → { transcript, notes } }       │
│  QUESTIONS { lecture_id → [ MCQ objects ] }              │
│  RESPONSES { lecture_id → { score, question_results } } │
│  VECTOR_DB { lecture_id → { faiss_index, chunks } }     │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌─────────────────┐          ┌────────────────────────┐
│     Student     │          │      Instructor        │
│                 │          │                        │
│  GET /get-      │          │  GET /analytics/       │
│  questions      │          │  {lecture_id}          │
│                 │          │                        │
│  POST /submit-  │          │  Returns:              │
│  answers        │          │  - Overall accuracy %  │
│                 │          │  - Topic-wise breakdown│
└────────┬────────┘          └────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│             Stage 4: Answer Evaluation                  │
│                    evaluation.py                        │
│                                                         │
│  1. Encode user answer    → 384-dim vector              │
│  2. Encode correct answer → 384-dim vector              │
│  3. Cosine similarity > 0.6 → correct                   │
│                                                         │
│  Returns: score, per-question { is_correct, similarity, │
│           topic }                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Sequence Diagrams

### Lecture Upload Flow

```
Instructor          app.py          asr_whisper.py     rag.py         llm_gemini.py
    │                 │                  │                │                │
    │── POST /upload ─►│                  │                │                │
    │                 │── save file ─────►│                │                │
    │                 │                  │                │                │
    │                 │── transcribe() ──►│                │                │
    │                 │                  │── Pass 1 ─────►│                │
    │                 │                  │   (distil)     │                │
    │                 │                  │── Pass 2? ─────►│               │
    │                 │                  │   (medium)     │                │
    │                 │◄── transcript ───│                │                │
    │                 │                  │                │                │
    │                 │── add_to_vector_store() ──────────►│               │
    │                 │                  │                │── chunk ──────►│
    │                 │                  │                │── embed ──────►│
    │                 │                  │                │── index ──────►│
    │                 │                  │                │                │
    │                 │── generate_notes_and_questions() ─────────────────►│
    │                 │                  │                │                │── prompt Gemini
    │                 │                  │                │                │── parse JSON
    │                 │◄── { notes, questions } ──────────────────────────│
    │                 │                  │                │                │
    │◄── { lecture_id, total_questions }─│                │                │
```

### Student Answer Flow

```
Student             app.py           rag.py          evaluation.py
    │                 │                │                  │
    │── GET /get-questions ──►│        │                  │
    │◄── { questions[] } ────│        │                  │
    │                        │        │                  │
    │── POST /submit-answers ►│       │                  │
    │                        │── retrieve_context() ──►│  │
    │                        │◄── context chunks ──────│  │
    │                        │                         │  │
    │                        │── evaluate_answers() ──────►│
    │                        │                         │  │── encode answers
    │                        │                         │  │── cosine similarity
    │                        │◄── { score, results[] } ───│
    │                        │                         │  │
    │◄── { score, results } ─│                         │  │
```

---

## API Reference

### `POST /upload-lecture`

Upload an audio file (MP3, WAV, M4A) or PDF for processing.

**Request**: `multipart/form-data` with `file` field

**Response**:
```json
{
  "lecture_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Lecture processed successfully",
  "total_questions": 10
}
```

---

### `GET /get-questions/{lecture_id}`

Retrieve generated MCQs for a lecture.

**Response**:
```json
{
  "lecture_id": "a1b2c3d4-...",
  "questions": [
    {
      "id": 1,
      "question": "What is the primary function of mitochondria?",
      "options": [
        "Protein synthesis",
        "Energy production",
        "Cell division",
        "DNA replication"
      ],
      "correct": "Energy production",
      "topic": "Cell Biology"
    }
  ]
}
```

---

### `POST /submit-answers/{lecture_id}`

Submit student answers for evaluation.

**Request**:
```json
{
  "answers": {
    "1": "Energy production",
    "2": "Osmosis",
    "3": "RNA polymerase"
  }
}
```

**Response**:
```json
{
  "score": 2,
  "question_results": [
    {
      "question_id": "1",
      "is_correct": true,
      "similarity": 1.0,
      "topic": "Cell Biology"
    },
    {
      "question_id": "2",
      "is_correct": false,
      "similarity": 0.34,
      "topic": "Membrane Transport"
    }
  ]
}
```

---

### `GET /analytics/{lecture_id}`

Instructor dashboard — aggregated performance across all student submissions.

**Response**:
```json
{
  "total_submissions": 5,
  "total_questions": 50,
  "overall_accuracy": 70.0,
  "topic_wise_performance": {
    "Cell Biology": { "correct": 15, "total": 20 },
    "Membrane Transport": { "correct": 5, "total": 15 },
    "Genetics": { "correct": 15, "total": 15 }
  }
}
```

---

## Components

### [app.py](app.py) — FastAPI Orchestrator

Entry point. Wires all pipeline stages together via REST endpoints. Manages CORS middleware (`allow_origins=["*"]`) and in-memory state.

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/upload-lecture` | POST | Audio/PDF file | `lecture_id`, question count |
| `/get-questions/{lecture_id}` | GET | Path param | MCQ array |
| `/submit-answers/{lecture_id}` | POST | JSON `{ answers }` | Score + per-question results |
| `/analytics/{lecture_id}` | GET | Path param | Accuracy + topic breakdown |

---

### [asr_whisper.py](asr_whisper.py) — Hybrid ASR (Primary)

Cost-optimized two-pass transcription using `faster-whisper`.

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `cheap_model` | `distil-small.en` | Fast initial pass, INT8 on CPU |
| `accurate_model` | `medium.en` | High-quality fallback, INT8 on CPU |
| `CONFIDENCE_THRESHOLD` | `-0.5` | `avg_logprob` cutoff for re-transcription |
| `beam_size` | `5` | Beam search width for decoding |

**How it works**:
1. Transcribe full audio with `distil-small.en`
2. For each segment, check `avg_logprob` against threshold
3. If below threshold → extract segment audio via FFmpeg → re-transcribe with `medium.en`
4. Concatenate all segment texts into final transcript

---

### [asr_gemini.py](asr_gemini.py) — Gemini ASR (Alternative)

Cloud-based transcription using Gemini 2.5 Flash native audio model.

| Feature | Detail |
|---------|--------|
| Model | `gemini-2.5-flash-native-audio-latest` |
| Formats | MP3 (`audio/mpeg`), WAV (`audio/wav`), M4A (`audio/mp4`) |
| Status | **Not wired** into `app.py` — available as drop-in replacement |

---

### [rag.py](rag.py) — Vector Store

Semantic retrieval layer for context-aware evaluation.

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Chunk size | 500 chars | Text window size |
| Overlap | 50 chars | Overlap between chunks to avoid splitting context |
| Embedding model | `all-MiniLM-L6-v2` | 384-dim embeddings, fast on CPU |
| Index type | `IndexFlatL2` | Exact nearest-neighbor (L2 distance) |
| `top_k` | 3 | Number of chunks returned per query |

**Functions**:
- `chunk_text(text, size, overlap)` — sliding window chunker
- `add_to_vector_store(lecture_id, text)` — chunk + embed + index
- `retrieve_context(lecture_id, query, top_k)` — semantic search over indexed chunks

---

### [llm_gemini.py](llm_gemini.py) — Content Generation

Generates educational content from transcript via Gemini LLM.

| Parameter | Value |
|-----------|-------|
| Model | `gemini-2.5-flash-lite` |
| Output format | JSON (`{ notes, questions }`) |
| Questions count | 10 MCQs per lecture |

**JSON parsing strategy**: Finds first `{` and last `}` in raw response to extract JSON, handling cases where the model wraps output in markdown code blocks.

---

### [evaluation.py](evaluation.py) — Answer Evaluation

Scores student responses using embedding-based semantic similarity.

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Model | `all-MiniLM-L6-v2` | Same embedding model as RAG |
| Method | Cosine similarity | Measures directional similarity |
| Threshold | `0.6` | Similarity above this = correct |

**Why semantic evaluation?** — String matching (`==`) would fail on paraphrased answers like "ATP production" vs "Energy production". Embedding similarity captures semantic equivalence.

---

### [utils.py](utils.py) — Text Utilities

| Function | Library | Purpose |
|----------|---------|---------|
| `clean_text()` | `re` | Strips whitespace, removes fillers (`um`, `uh`, `hmm`, `erm`) |
| `extract_text_from_pdf()` | PyPDF2 | Page-by-page text extraction from PDF bytes |
| `extract_text_from_docx()` | python-docx | Paragraph extraction from DOCX bytes |

---

## Storage Architecture

All data is held **in-memory** using Python dicts. No external database.

```
┌──────────────────────────────────────────────────────────────┐
│                     In-Memory State                          │
│                                                              │
│  LECTURES ─────┐                                             │
│    lecture_id → │ { transcript: str, notes: str }            │
│                └─────────────────────────────────────────    │
│                                                              │
│  QUESTIONS ────┐                                             │
│    lecture_id → │ [ { id, question, options, correct,        │
│                │     topic } ]                               │
│                └─────────────────────────────────────────    │
│                                                              │
│  RESPONSES ────┐                                             │
│    lecture_id → │ [ { score: int,                            │
│                │     question_results: [ { question_id,      │
│                │       is_correct, similarity, topic } ]     │
│                │   }, ... ]  (list — supports multi-student) │
│                └─────────────────────────────────────────    │
│                                                              │
│  VECTOR_DB ────┐                                             │
│    lecture_id → │ { index: faiss.IndexFlatL2,                │
│                │   chunks: [str] }                           │
│                └─────────────────────────────────────────    │
└──────────────────────────────────────────────────────────────┘
```

> **Limitation**: All data is lost on server restart. For production use, consider PostgreSQL (structured data), ChromaDB/Pinecone (vector store), and Redis (caching).

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for LLM + cloud ASR |

### Tunable Constants

| Constant | File | Default | Description |
|----------|------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | `asr_whisper.py` | `-0.5` | Logprob cutoff for ASR fallback |
| Chunk `size` | `rag.py` | `500` | Character count per text chunk |
| Chunk `overlap` | `rag.py` | `50` | Overlap between adjacent chunks |
| `top_k` | `rag.py` | `3` | Number of chunks retrieved |
| Similarity threshold | `evaluation.py` | `0.6` | Cosine sim cutoff for correct answer |
| `beam_size` | `asr_whisper.py` | `5` | Whisper beam search width |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Web framework | FastAPI + Uvicorn | Async REST API server |
| ASR (local) | faster-whisper | Two-pass Whisper transcription |
| ASR (cloud) | Google Gemini 2.5 Flash | Alternative cloud transcription |
| LLM | Google Gemini 2.5 Flash Lite | Notes + MCQ generation |
| Embeddings | SentenceTransformer `all-MiniLM-L6-v2` | 384-dim text embeddings |
| Vector search | FAISS (`faiss-cpu`) | In-memory nearest-neighbor search |
| Audio processing | FFmpeg (subprocess) | Segment extraction for ASR fallback |
| PDF parsing | PyPDF2 | Text extraction from PDFs |
| DOCX parsing | python-docx | Text extraction from Word docs |
| Env management | python-dotenv | `.env` file loading |

---

## Setup

### Prerequisites

- Python 3.10+
- FFmpeg installed and available in `PATH`
- Google Gemini API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd AI-Classroom-Platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Quick Test

```bash
# Upload a lecture
curl -X POST http://localhost:8000/upload-lecture \
  -F "file=@lecture.mp3"

# Get questions (use lecture_id from upload response)
curl http://localhost:8000/get-questions/<lecture_id>

# Submit answers
curl -X POST http://localhost:8000/submit-answers/<lecture_id> \
  -H "Content-Type: application/json" \
  -d '{"answers": {"1": "Energy production", "2": "Osmosis"}}'

# View analytics
curl http://localhost:8000/analytics/<lecture_id>
```

---

## Design Decisions & Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Hybrid ASR** (cheap + accurate) | Reduces processing time and compute cost for clear audio | Adds complexity; FFmpeg dependency for segment extraction |
| **In-memory storage** | Simple, zero-config, fast reads | Data lost on restart; single-server only; no multi-user isolation |
| **Semantic similarity for scoring** | Handles paraphrased answers gracefully | Threshold (0.6) may misclassify edge cases; not suitable for numeric or exact-match answers |
| **FAISS IndexFlatL2** | Exact search, no index build overhead | O(n) search — doesn't scale beyond ~100K vectors per lecture |
| **Character-based chunking** | Simple, predictable chunk sizes | May split mid-word or mid-sentence; sentence-aware chunking would be better |
| **Single Gemini call for notes + questions** | Fewer API calls, lower latency | If generation fails, both notes and questions are lost |
| **`all-MiniLM-L6-v2`** | Fast, lightweight (80MB), good general-purpose embeddings | Less accurate than larger models for domain-specific content |

---

## Known Limitations

1. **No persistence** — All data (lectures, questions, scores, vectors) lives in memory and is lost on server restart.
2. **No authentication** — All endpoints are open; no user sessions, roles, or access control.
3. **`asr_gemini.py` unused** — Cloud ASR module exists but isn't integrated into the main pipeline.
4. **Synchronous processing** — Upload endpoint blocks until the full pipeline completes (ASR + RAG + LLM), which can take minutes for long audio files.
5. **CORS wildcard** — `allow_origins=["*"]` is set, which is fine for dev but insecure for production.

---

## Future Improvements

- **Database persistence** — PostgreSQL for structured data, ChromaDB/Pinecone for vectors
- **Background task processing** — Use Celery or FastAPI `BackgroundTasks` for async pipeline execution
- **Multi-user support** — User authentication (JWT), per-student response tracking
- **Streaming upload progress** — WebSocket or SSE for real-time pipeline status
- **Sentence-aware chunking** — Split on sentence boundaries instead of fixed character count
- **Configurable question count** — Allow instructors to specify number and difficulty of MCQs
- **Frontend** — React/Next.js dashboard for instructors and students
