# StudyForge — AI Classroom Learning Platform

An AI-powered learning platform that transforms lecture audio and PDFs into structured study notes, quizzes, and an intelligent chat assistant — fully deployed and production-ready.

---

## 🌐 Live Demo

| App | URL |
|---|---|
| 🎓 Frontend (Streamlit UI) | [studyforge.streamlit.app](https://studyforge-6cj2vrwgevxjjgju8ifs8c.streamlit.app/) |
| ⚙️ Backend API | [studyforge-tnlg.onrender.com](https://studyforge-tnlg.onrender.com) |
| 📖 API Docs | [studyforge-tnlg.onrender.com/docs](https://studyforge-tnlg.onrender.com/docs) |

---

## 🎯 Goal

Build a production-grade, AI-powered classroom platform with:

- **Frontend** — Student-facing UI to upload lectures, view notes, take quizzes, chat with AI, and track performance.
- **Backend** — FastAPI REST API handling transcription, note generation, quiz creation, RAG-based chat, and analytics.

---

## ⚡ Features

### 🎓 Student Experience
- Upload lecture audio (MP3, WAV, M4A) or PDF slides.
- Auto-generated structured study notes in markdown format.
- AI-generated 10-question MCQ quiz from the lecture content.
- Regenerate fresh quiz questions anytime with one click.
- RAG-powered chat — ask any question about the lecture.
- Instant answer evaluation with score, accuracy, and grade.

### 📊 Analytics
- Track total quiz submissions per lecture.
- View overall accuracy percentage.
- Topic-wise performance breakdown with bar charts.

### ⚙️ Backend API
- RESTful API built with FastAPI.
- Gemini 2.5 Flash for audio transcription (ASR) and LLM tasks.
- Simple chunk-based RAG for context-aware chat responses.
- PDF text extraction via pypdf.
- In-memory vector store for fast lecture context retrieval.

---

## 🗂️ Project Structure

```
StudyForge/
├── app.py               # FastAPI backend — all API endpoints
├── asr_gemini.py        # Audio transcription via Gemini API
├── llm_gemini.py        # Note + MCQ generation, RAG chat via Gemini
├── rag.py               # Chunk-based RAG vector store
├── evaluation.py        # Quiz answer evaluation logic
├── utils.py             # PDF/DOCX text extraction utilities
├── streamlit_app.py     # Streamlit frontend UI
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container config
├── docker-compose.yml   # Docker Compose config
└── Data/uploads/        # Uploaded lecture files
```

---

## 💻 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **Backend** | Python, FastAPI, Uvicorn |
| **AI / LLM** | Google Gemini 2.5 Flash (ASR + Notes + Chat) |
| **RAG** | Custom chunk-based in-memory retrieval |
| **Document Parsing** | pypdf, python-docx |
| **Frontend Deploy** | Streamlit Community Cloud |
| **Backend Deploy** | Render (Docker) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### 1. Clone the Repository
```bash
git clone https://github.com/Shubham0x1/StudyForge.git
cd StudyForge
```

### 2. Set Up Environment
```bash
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run the Backend
```bash
uvicorn app:app --reload --port 8000
```
The API will be running at `http://localhost:8000`.

### 4. Run the Frontend
In a new terminal:
```bash
streamlit run streamlit_app.py
```
Open `http://localhost:8501` in your browser.

---

## 🐳 Docker

```bash
docker-compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`

---

## 🌍 Deployment

### Backend — Render (Docker)
1. Create a new **Web Service** on [Render](https://render.com).
2. Connect your GitHub repository `Shubham0x1/StudyForge`.
3. Select **Docker** as the runtime.
4. Add environment variable: `GEMINI_API_KEY=your_key`
5. Deploy — Render auto-detects the `Dockerfile`.

### Frontend — Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io).
2. Connect your GitHub repository.
3. Set main file path to `streamlit_app.py`.
4. Add secret: `GEMINI_API_KEY = "your_key"` under Advanced Settings.
5. Deploy.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API health check + endpoint list |
| POST | `/upload-lecture` | Upload audio/PDF, run full pipeline |
| GET | `/get-notes/{lecture_id}` | Fetch generated study notes |
| GET | `/get-questions/{lecture_id}` | Fetch MCQ questions |
| POST | `/submit-answers/{lecture_id}` | Submit and evaluate quiz answers |
| GET | `/analytics/{lecture_id}` | Topic-wise performance analytics |
| POST | `/chat/{lecture_id}` | Ask questions about the lecture (RAG) |
| POST | `/regenerate-questions/{lecture_id}` | Generate a fresh set of MCQs |

---

## ⚠️ Known Limitations

- Free tier on Render spins down after inactivity — first request may take ~50 seconds to wake up.
- In-memory storage resets on server restart (lecture data is not persisted).
- RAG uses simple chunk retrieval — semantic search not implemented on free tier.

---

## 📄 License

This project is for educational and portfolio purposes.

---

## 👨‍💻 Author

**Shubham Gusain**

GitHub: [https://github.com/Shubham0x1](https://github.com/Shubham0x1)

---

## ⭐ Support

If you like this project, consider giving the repository a **star ⭐**.
