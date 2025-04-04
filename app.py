import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="FinalGuardian", layout="centered")
st.title("FinalGuardian - AI Quiz Trainer")

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
    if "disable_generate" not in st.session_state:
        st.session_state.disable_generate = False

    generate_button = st.button("Generate Quiz", disabled=st.session_state.disable_generate)

    if generate_button:
        st.session_state.disable_generate = True
        with st.spinner("Generating quiz..."):
            try:
                res = requests.post(f"{API_BASE}/generate-quiz", data={"topic": topic})
                if res.status_code == 429:
                    st.error("Too many requests. Please wait and try again.")
                elif res.status_code != 200:
                    st.error(f"Server error: {res.text}")
                else:
                    data = res.json()
                    st.session_state.questions = data.get("questions", [])
                    st.session_state.user_answers = ["" for _ in st.session_state.questions]
            except Exception as e:
                st.error(f"Unexpected error: {e}")
            finally:
                st.session_state.disable_generate = False

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
        with st.spinner("Evaluating answers..."):
            res = requests.post(f"{API_BASE}/evaluate-all", json=payload)
            st.session_state.evaluation = res.json().get("results", [])

if "evaluation" in st.session_state:
    st.header("Evaluation Results")
    for item in st.session_state.evaluation:
        st.markdown(f"**{item['question']}**")
        # st.code(item['result']['content'], language="markdown")
        formatted_result = item['result']['content'].replace('\n', '<br>')
        st.markdown(f"<div style='background-color:#f5f5f5;padding:10px;border-radius:6px'>{formatted_result}</div>",
                    unsafe_allow_html=True)
