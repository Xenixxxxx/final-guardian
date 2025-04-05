# FinalGuardian - Your AI Exam Preparation Companion

FinalGuardian is an AI-powered exam assistant that helps you generate practice quizzes from your own study notes and get instant feedback. Powered by OpenAI and LangChain.

📚 Upload your notes  
🧠 Generate quiz questions  
📝 Answer and get feedback  
🤖 Chat with your AI tutor

---

## 🧰 Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **AI**: Azure OpenAI GPT + Embeddings
- **Retrieval**: LangChain + ChromaDB
- **Chatbot**: LangChain Agent with Tool-Calling
- **Deployment**: Streamlit + Render

---

## 🚀 Try it now!

You’ll get your personal AI quiz app in minutes!


### Step 1 - Clone the repository

**[Click here to deploy your own version](https://github.com/Xenixxxxx/final-guardian/fork)**  

### Step 2 - Set up your environment
copy .env.example to .env and fill in your OpenAI API settings

### Step 3 - install the required packages
```bash
pip install -r requirements.txt
```

### Step 4 - Start the backend server
```bash
uvicorn main:app --reload
```

### Step 5 - Start the frontend
```bash
streamlit run app.py
```





