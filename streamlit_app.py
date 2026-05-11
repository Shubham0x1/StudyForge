import streamlit as st
import requests
import json

API_URL = "https://studyforge-tnlg.onrender.com"

st.set_page_config(page_title="AI Classroom", page_icon="🎓", layout="wide")

# ---- Custom CSS ----
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .score-card h1 { margin: 0; font-size: 48px; }
    .score-card p { margin: 0; opacity: 0.9; }
    .chat-msg {
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        max-width: 80%;
    }
    .user-msg {
        background: #e3f2fd;
        margin-left: auto;
        text-align: right;
    }
    .ai-msg {
        background: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# ---- Helper ----
def safe_error(resp):
    try:
        return resp.json().get("detail", "Unknown error")
    except Exception:
        return f"Server error (status {resp.status_code}). The backend may be waking up — wait 30 seconds and try again."

# ---- Session State ----
if "lecture_id" not in st.session_state:
    st.session_state.lecture_id = None
if "notes" not in st.session_state:
    st.session_state.notes = None
if "questions" not in st.session_state:
    st.session_state.questions = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_result" not in st.session_state:
    st.session_state.quiz_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- Header ----
st.title("AI Classroom Platform")
st.caption("Upload a lecture. Get notes, quiz yourself, chat with AI, and track performance.")

# ---- Sidebar: Upload ----
with st.sidebar:
    st.header("Upload Lecture")
    uploaded_file = st.file_uploader(
        "Choose an audio or PDF file",
        type=["mp3", "wav", "m4a", "pdf"],
        help="Supported: MP3, WAV, M4A, PDF (max 50MB)"
    )

    if uploaded_file and st.button("Process Lecture", type="primary", use_container_width=True):
        with st.spinner("Processing... The server may take 30-60s to wake up on first request."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            try:
                resp = requests.post(f"{API_URL}/upload-lecture", files=files, timeout=300)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.lecture_id = data["lecture_id"]
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_result = None
                    st.session_state.chat_history = []

                    # Fetch notes
                    notes_resp = requests.get(f"{API_URL}/get-notes/{data['lecture_id']}", timeout=30)
                    if notes_resp.status_code == 200:
                        st.session_state.notes = notes_resp.json()["notes"]

                    # Fetch questions
                    q_resp = requests.get(f"{API_URL}/get-questions/{data['lecture_id']}", timeout=30)
                    if q_resp.status_code == 200:
                        st.session_state.questions = q_resp.json()["questions"]

                    st.success(f"Lecture processed! {data['total_questions']} questions generated.")
                else:
                    st.error(safe_error(resp))
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend. Wait 30 seconds and try again.")
            except requests.exceptions.Timeout:
                st.error("Request timed out. The server may be overloaded — please try again.")

    if st.session_state.lecture_id:
        st.divider()
        st.success("Active Lecture")
        st.code(st.session_state.lecture_id[:8] + "...", language=None)

# ---- Main Area: Tabs ----
if not st.session_state.lecture_id:
    st.info("Upload a lecture file from the sidebar to get started.")
else:
    tab_notes, tab_quiz, tab_chat, tab_analytics = st.tabs([
        "Study Notes", "Take Quiz", "Chat with AI", "Analytics"
    ])

    # ---- Tab 1: Study Notes ----
    with tab_notes:
        if st.session_state.notes:
            st.markdown(st.session_state.notes)
        else:
            st.warning("Notes not available.")

    # ---- Tab 2: Quiz ----
    with tab_quiz:

        # Regenerate button always visible at top
        col_r1, col_r2 = st.columns([3, 1])
        with col_r2:
            if st.button("🔄 Regenerate Quiz", use_container_width=True):
                with st.spinner("Generating new questions..."):
                    try:
                        resp = requests.post(
                            f"{API_URL}/regenerate-questions/{st.session_state.lecture_id}",
                            timeout=90
                        )
                        if resp.status_code == 200:
                            q_resp = requests.get(
                                f"{API_URL}/get-questions/{st.session_state.lecture_id}",
                                timeout=30
                            )
                            if q_resp.status_code == 200:
                                st.session_state.questions = q_resp.json()["questions"]
                                st.session_state.quiz_submitted = False
                                st.session_state.quiz_result = None
                                st.success("New questions generated!")
                                st.rerun()
                        else:
                            st.error(safe_error(resp))
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend. Try again.")
                    except requests.exceptions.Timeout:
                        st.error("Request timed out. Try again.")

        if not st.session_state.questions:
            st.warning("No questions available.")
        elif st.session_state.quiz_submitted and st.session_state.quiz_result:
            result = st.session_state.quiz_result
            score = result["score"]
            total = len(result["question_results"])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="score-card">
                    <h1>{score}/{total}</h1>
                    <p>Score</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                pct = round((score / total) * 100) if total else 0
                st.markdown(f"""
                <div class="score-card">
                    <h1>{pct}%</h1>
                    <p>Accuracy</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                grade = "A" if pct >= 90 else "B" if pct >= 75 else "C" if pct >= 60 else "D" if pct >= 40 else "F"
                st.markdown(f"""
                <div class="score-card">
                    <h1>{grade}</h1>
                    <p>Grade</p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            for i, qr in enumerate(result["question_results"]):
                q = st.session_state.questions[i]
                icon = "✅" if qr["is_correct"] else "❌"
                with st.expander(f"{icon} Q{i+1}: {q['question']}", expanded=not qr["is_correct"]):
                    st.write(f"**Your answer:** {st.session_state.get(f'ans_{i}', 'N/A')}")
                    st.write(f"**Correct answer:** {q['correct']}")
                    st.write(f"**Similarity:** {qr['similarity']}")
                    st.write(f"**Topic:** {qr['topic']}")

            if st.button("Retake Quiz"):
                st.session_state.quiz_submitted = False
                st.session_state.quiz_result = None
                st.rerun()
        else:
            with st.form("quiz_form"):
                st.subheader("Answer the following questions:")
                answers = {}
                for i, q in enumerate(st.session_state.questions):
                    st.markdown(f"**Q{i+1}. {q['question']}**")
                    choice = st.radio(
                        f"Select answer for Q{i+1}:",
                        options=["— Select an answer —"] + q["options"],
                        key=f"q_{i}",
                        label_visibility="collapsed"
                    )
                    answers[str(q["id"])] = "" if choice == "— Select an answer —" else choice
                    st.session_state[f"ans_{i}"] = choice

                submitted = st.form_submit_button("Submit Answers", type="primary", use_container_width=True)

                if submitted:
                    with st.spinner("Evaluating..."):
                        try:
                            resp = requests.post(
                                f"{API_URL}/submit-answers/{st.session_state.lecture_id}",
                                json={"answers": answers},
                                timeout=60
                            )
                            if resp.status_code == 200:
                                st.session_state.quiz_result = resp.json()
                                st.session_state.quiz_submitted = True
                                st.rerun()
                            else:
                                st.error(safe_error(resp))
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to backend. Try again.")
                        except requests.exceptions.Timeout:
                            st.error("Request timed out. Try again.")

    # ---- Tab 3: Chat with AI ----
    with tab_chat:
        st.subheader("Ask anything about the lecture")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])

        question = st.chat_input("Type your question about the lecture...")
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        resp = requests.post(
                            f"{API_URL}/chat/{st.session_state.lecture_id}",
                            json={"question": question},
                            timeout=60
                        )
                        if resp.status_code == 200:
                            answer = resp.json()["answer"]
                        else:
                            answer = f"Error: {safe_error(resp)}"
                    except requests.exceptions.ConnectionError:
                        answer = "Cannot connect to backend. Try again."
                    except requests.exceptions.Timeout:
                        answer = "Request timed out. Try again."

                st.write(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

    # ---- Tab 4: Analytics ----
    with tab_analytics:
        try:
            resp = requests.get(f"{API_URL}/analytics/{st.session_state.lecture_id}", timeout=30)
            if resp.status_code == 200:
                data = resp.json()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Submissions", data["total_submissions"])
                    st.metric("Overall Accuracy", f"{data['overall_accuracy']}%")
                with col2:
                    st.metric("Total Questions Answered", data["total_questions"])

                st.divider()
                st.subheader("Topic-wise Performance")

                topic_data = data["topic_wise_performance"]
                if topic_data:
                    topics = list(topic_data.keys())
                    correct_vals = [topic_data[t]["correct"] for t in topics]
                    total_vals = [topic_data[t]["total"] for t in topics]
                    accuracy_vals = [
                        round((topic_data[t]["correct"] / topic_data[t]["total"]) * 100)
                        if topic_data[t]["total"] > 0 else 0
                        for t in topics
                    ]

                    import pandas as pd
                    df = pd.DataFrame({
                        "Topic": topics,
                        "Correct": correct_vals,
                        "Total": total_vals,
                        "Accuracy %": accuracy_vals
                    })

                    st.bar_chart(df.set_index("Topic")["Accuracy %"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No topic data available yet.")

            elif resp.status_code == 404:
                st.info("No submissions yet. Take the quiz first!")
            else:
                st.error(safe_error(resp))
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Try again.")
