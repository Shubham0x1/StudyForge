from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid

from asr_gemini import transcribe_audio
from llm_gemini import generate_notes_and_questions, chat_with_context
from evaluation import evaluate_answers
from rag import add_to_vector_store, retrieve_context
from utils import extract_text_from_pdf

app = FastAPI(title="AI Classroom Learning Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR = "Data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

LECTURES = {}
QUESTIONS = {}
RESPONSES = {}


@app.get("/")
def root():
    return {
        "name": "AI Classroom Learning Platform",
        "status": "running",
        "docs": "/docs",
        "endpoints": [
            "POST /upload-lecture",
            "GET  /get-notes/{lecture_id}",
            "GET  /get-questions/{lecture_id}",
            "POST /submit-answers/{lecture_id}",
            "POST /chat/{lecture_id}",
            "GET  /analytics/{lecture_id}",
            "POST /regenerate-questions/{lecture_id}",
        ]
    }


# ----------------------------
# 1. Upload Lecture (Audio/PDF)
# ----------------------------

@app.post("/upload-lecture")
async def upload_lecture(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB"
        )

    lecture_id = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{lecture_id}_{file.filename}")

    with open(path, "wb") as f:
        f.write(contents)

    # Step 1: ASR / Text Extraction
    try:
        if ext == ".pdf":
            transcript = extract_text_from_pdf(contents)
        else:
            content_type_map = {
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4"
            }
            transcript = transcribe_audio(contents, content_type_map[ext])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    if not transcript or not transcript.strip():
        raise HTTPException(status_code=422, detail="Could not extract any text from the file")

    # Step 2: Store transcript in RAG
    add_to_vector_store(lecture_id, transcript)

    # Step 3: Generate Notes & Questions
    try:
        notes, questions = generate_notes_and_questions(transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {e}")

    LECTURES[lecture_id] = {
        "transcript": transcript,
        "notes": notes
    }

    QUESTIONS[lecture_id] = questions

    return {
        "lecture_id": lecture_id,
        "message": "Lecture processed successfully",
        "total_questions": len(questions)
    }


# ----------------------------
# 2. Get Questions
# ----------------------------

@app.get("/get-questions/{lecture_id}")
def get_questions(lecture_id: str):
    if lecture_id not in QUESTIONS:
        raise HTTPException(status_code=404, detail="Lecture not found")

    return {
        "lecture_id": lecture_id,
        "questions": QUESTIONS[lecture_id]
    }


# ----------------------------
# 3. Submit Answers
# ----------------------------

@app.post("/submit-answers/{lecture_id}")
async def submit_answers(lecture_id: str, payload: dict):
    if lecture_id not in QUESTIONS:
        raise HTTPException(status_code=404, detail="Lecture not found")

    user_answers = payload.get("answers")
    if not user_answers:
        raise HTTPException(status_code=400, detail="Missing 'answers' in request body")

    result = evaluate_answers(
        QUESTIONS[lecture_id],
        user_answers,
    )

    RESPONSES.setdefault(lecture_id, []).append(result)

    return result


# ----------------------------
# 4. Instructor Analytics
# ----------------------------

@app.get("/analytics/{lecture_id}")
def analytics(lecture_id: str):
    if lecture_id not in RESPONSES or not RESPONSES[lecture_id]:
        raise HTTPException(status_code=404, detail="No responses yet")

    submissions = RESPONSES[lecture_id]

    all_results = []
    for submission in submissions:
        all_results.extend(submission["question_results"])

    total = len(all_results)
    correct = sum(1 for q in all_results if q["is_correct"])

    topic_stats = {}
    for q in all_results:
        topic = q["topic"]
        topic_stats.setdefault(topic, {"correct": 0, "total": 0})
        topic_stats[topic]["total"] += 1
        if q["is_correct"]:
            topic_stats[topic]["correct"] += 1

    return {
        "total_submissions": len(submissions),
        "total_questions": total,
        "overall_accuracy": round((correct / total) * 100, 2) if total > 0 else 0,
        "topic_wise_performance": topic_stats
    }


# ----------------------------
# 5. Get Notes
# ----------------------------

@app.get("/get-notes/{lecture_id}")
def get_notes(lecture_id: str):
    if lecture_id not in LECTURES:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return {"lecture_id": lecture_id, "notes": LECTURES[lecture_id]["notes"]}


# ----------------------------
# 6. Chat with Lecture (RAG)
# ----------------------------

@app.post("/chat/{lecture_id}")
async def chat(lecture_id: str, payload: dict):
    if lecture_id not in LECTURES:
        raise HTTPException(status_code=404, detail="Lecture not found")

    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' in request body")

    context_chunks = retrieve_context(lecture_id, question, top_k=5)
    if not context_chunks:
        return {"answer": "No lecture content available to answer this question."}

    try:
        answer = chat_with_context(question, context_chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

    return {"answer": answer}


# ----------------------------
# 7. Regenerate Questions
# ----------------------------

@app.post("/regenerate-questions/{lecture_id}")
async def regenerate_questions(lecture_id: str):
    if lecture_id not in LECTURES:
        raise HTTPException(status_code=404, detail="Lecture not found")

    try:
        notes, questions = generate_notes_and_questions(LECTURES[lecture_id]["transcript"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {e}")

    QUESTIONS[lecture_id] = questions

    return {
        "message": "Questions regenerated successfully",
        "total_questions": len(questions)
    }
