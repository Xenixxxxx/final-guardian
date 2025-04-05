import json
import os

import requests

import streamlit as st
from streamlit_lottie import st_lottie
from streamlit_lottie import st_lottie_spinner

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
print(f"Using API base: {API_BASE}")


def load_lottie(filepath: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load Lottie file: {e}")
        return None


lottie_generating = load_lottie("assets/Animation - 1743834053019.json")
lottie_exam = load_lottie("assets/Animation - 1743835691341.json")
lottie_tutor = load_lottie("assets/Animation - 1743836610229.json")

st.set_page_config(page_title="FinalGuardian", layout="centered", initial_sidebar_state="expanded")

col1, col2 = st.columns([5, 1])

with col1:
    st.title("FinalGuardian - Your AI Exam Preparation Companion")

with col2:
    if lottie_exam:
        st_lottie(lottie_exam, width=150, key="ai_intro")

st.write(
    "<span style='color:gray'>Welcome to FinalGuardian, your ultimate AI-powered tool to help you prepare for exams efficiently. Upload your study notes, generate quizzes, check you understanding and chat with an AI tutor.",
    unsafe_allow_html=True)
st.write(" ")

tabs = st.tabs([" Generate Quiz   |", " Chat with Tutor   |", "Test Connection"])

# ==== Generate Quiz ====
with tabs[0]:
    # ---- Upload notes ----
    st.header("1. Upload your study notes")
    uploaded_file = st.file_uploader("Upload .txt or .pdf file", type=["txt", "pdf"])
    if uploaded_file and st.button("Upload and Index"):
        res = requests.post(f"{API_BASE}/upload", files={"file": uploaded_file})
        st.success(res.json().get("message"))

    #  ---- Generate quiz ----
    st.header("2. Generate quiz")
    topic = st.text_input("Enter a topic keyword (e.g. 'data cleaning')")
    if topic:
        if "quiz_submitted" not in st.session_state:
            st.session_state.quiz_submitted = False

        generate_button = st.button("Generate Quiz")

        if generate_button:
            with st_lottie_spinner(lottie_generating, key="generating", height=80):
                try:
                    res = requests.post(f"{API_BASE}/generate-quiz", data={"topic": topic})
                    if res.status_code == 429:
                        st.error("Too many requests. Please wait and try again.")
                    elif res.status_code == 400:
                        st.error("No notes found related to this keyword. Please upload your notes first.")
                    elif res.status_code != 200:
                        st.error(f"Server error: {res.text}")
                    else:
                        data = res.json()
                        st.session_state.questions = data.get("questions", [])
                        st.session_state.user_answers = ["" for _ in st.session_state.questions]
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

    # ---- Answer the questions ----
    if "questions" in st.session_state and st.session_state.questions:
        st.header("3. Answer the questions")
        for i, q in enumerate(st.session_state.questions):
            lines = q['question'].splitlines()
            question_text = lines[0]
            options = lines[1:] if len(lines) > 1 else []

            st.markdown(f"**{question_text}**")
            for opt in options:
                st.markdown(f"{opt}")

            st.session_state.user_answers[i] = st.text_input(f"Your answer to Q{i + 1}",
                                                             value=st.session_state.user_answers[i])

        if st.button("Submit All Answers"):
            payload = {
                "answers": [
                    {
                        "question": q["question"],
                        "correct_answer": q["answer"],
                        "user_answer": st.session_state.user_answers[i]
                    }
                    for i, q in enumerate(st.session_state.questions)
                ]
            }
            with st_lottie_spinner(lottie_generating, key="generating", height=80):
                res = requests.post(f"{API_BASE}/evaluate-all", json=payload)
                st.session_state.evaluation = res.json().get("results", [])

    if "evaluation" in st.session_state:
        st.header("Evaluation Results")
        for item in st.session_state.evaluation:
            st.markdown(f"**{item['question']}**")
            formatted_result = item['result']['content'].replace('\n', '<br>')
            st.markdown(
                f"<div style='background-color:#f5f5f5;padding:10px;border-radius:6px'>{formatted_result}</div>",
                unsafe_allow_html=True)

# ==== Chat with Tutor ====
with tabs[1]:
    with tabs[1]:
        st.header("Chat with your AI Tutor")
        if lottie_tutor:
            st_lottie(lottie_tutor, width=250, key="tutor")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_message = st.chat_input("Ask anything about your notes...")
        if user_message:
            st.session_state.chat_history.append({"role": "user", "content": user_message})
            with st.chat_message("user"):
                st.markdown(user_message)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        res = requests.post(f"{API_BASE}/chat", json={"message": user_message})
                        reply = res.json().get("response", "Sorry, I couldn't respond.")
                    except Exception as e:
                        reply = f"Error: {e}"
                    st.markdown(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})

# === Ping Backend Button for Connection Test ===
with tabs[2]:
    with st.expander("Connection Test", expanded=False):
        if st.button("Ping Backend", help="Test connection to backend server"):
            try:
                st.write(f'Pinging {API_BASE}...')
                response = requests.get(f"{API_BASE}/ping")
                st.success(f"{response.json()['message']}")
            except Exception as e:
                st.error(f"Failed to connect: {e}")
