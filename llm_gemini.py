from google import genai
from dotenv import load_dotenv
import os, json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_notes_and_questions(transcript: str):
    prompt = f"""
You are an AI teaching assistant.

From the following lecture transcript:
1. Create well-formatted, human-readable study notes in markdown format with headings, bullet points, and sections
2. Create 10 MCQs

Each MCQ must include:
- id
- question
- 4 options (as a list of strings)
- correct (the exact correct option string)
- topic

Transcript:
{transcript}

Return strictly in JSON:
{{
  "notes": "## Topic Title\\n\\n### Key Points\\n- Point 1\\n- Point 2\\n\\n### Summary\\n...",
  "questions": [ ... ]
}}

IMPORTANT:
- The notes field must be a clean markdown string with proper headings (##, ###) and bullet points (-)
- Do NOT return raw data, JSON, or Python dicts inside the notes field
- Write notes as a human teacher would write for a student — clear, organized, easy to read
- Cover all important topics from the transcript in the notes
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash-lite",
            contents=prompt
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

    raw = response.text.strip()

    # Extract JSON — handle cases where Gemini wraps output in markdown
    start = raw.find("{")
    end = raw.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("Gemini did not return valid JSON:\n" + raw[:200])

    json_str = raw[start:end]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")

    if "notes" not in data or "questions" not in data:
        raise ValueError("Gemini response missing 'notes' or 'questions' keys")

    return data["notes"], data["questions"]


def chat_with_context(question: str, context_chunks: list[str]) -> str:
    context = "\n\n".join(context_chunks)
    prompt = f"""You are a helpful AI teaching assistant. Answer the student's question using ONLY the lecture context provided below. If the answer is not in the context, say "I don't have enough information from the lecture to answer that."

Lecture Context:
{context}

Student Question: {question}

Answer concisely and clearly:"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash-lite",
            contents=prompt
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

    return response.text.strip()
