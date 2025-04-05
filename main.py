import asyncio
import hashlib
import re
import os
import shutil

from vectorstore.chroma import create_chroma_index, load_chroma_index
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, Request
from langchain.tools import Tool
from langchain.agents import AgentType, initialize_agent
from fastapi.responses import JSONResponse
from openai import RateLimitError

from chains.answer_evaluator import evaluate_answer
from chains.doc_loader import load_and_split_document
from chains.quiz_gen import generate_quiz_from_docs
from config import llm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HASH_FILE = "temp/uploaded_hashes.txt"


@app.get("/ping")
def ping():
    return {"message": "pong"}


def compute_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def load_uploaded_hashes():
    if not os.path.exists(HASH_FILE):
        return set()
    with open(HASH_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_uploaded_hashes(new_hashes: set):
    with open(HASH_FILE, "a") as f:
        for h in new_hashes:
            f.write(h + "\n")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    documents = load_and_split_document(file_path)

    uploaded_hashes = load_uploaded_hashes()
    new_docs = []
    new_hashes = set()

    for doc in documents:
        hash_ = compute_hash(doc.page_content)
        if hash_ not in uploaded_hashes:
            doc.metadata["hash"] = hash_
            new_docs.append(doc)
            new_hashes.add(hash_)

    if new_docs:
        print(f"New documents to add: {len(new_docs)}")
        create_chroma_index(new_docs)
        save_uploaded_hashes(new_hashes)
        return {"message": f"Uploaded successfully."}
    else:
        print("All documents already exist. Skipped upload.")
        return {"message": "All content already exists in database."}


@app.post("/generate-quiz")
async def generate_quiz(topic: str = Form(...)):
    index = load_chroma_index()
    docs = index.similarity_search(topic, k=10)

    if not docs or all(not doc.page_content.strip() for doc in docs):
        return JSONResponse(status_code=400, content={
            "error": "No notes found related to this keyword. Please upload your notes first."
        })

    quiz_response = generate_quiz_from_docs(docs)
    quiz_text = quiz_response.content if hasattr(quiz_response, "content") else quiz_response

    pattern = r"Q\d+:.*?(?=Q\d+:|\Z)"
    raw_questions = re.findall(pattern, quiz_text, re.DOTALL)

    questions = []
    for i, q in enumerate(raw_questions):
        match = re.search(r"(Q\d+:.*?)\n(A\d+:.*?)\n?\Z", q.strip(), re.DOTALL)
        if match:
            questions.append({
                "id": i,
                "question": match.group(1).strip(),
                "answer": match.group(2).strip()
            })
    return {"questions": questions}


class AnswerItem(BaseModel):
    question: str
    correct_answer: str
    user_answer: str


class AnswerSet(BaseModel):
    answers: list[AnswerItem]


@app.post("/evaluate-all")
async def evaluate_all(payload: AnswerSet):
    async def eval_one(item):
        return await asyncio.to_thread(
            lambda: {
                "question": item.question,
                "result": evaluate_answer(item.question, item.correct_answer, item.user_answer)
            }
        )

    tasks = [eval_one(item) for item in payload.answers]
    results = await asyncio.gather(*tasks)
    return {"results": results}


def simple_retrieval(query: str):
    print(f"Query: {query}")
    retriever = load_chroma_index().as_retriever()
    docs = retriever.invoke(query)
    print(f"Retrieved {len(docs)} documents.")
    text = "\n\n".join([doc.page_content for doc in docs])
    print(f'length of text: {len(text)}')
    return text[:500]  # due to token limit, only use the first 500 characters in this demo


retrieval_tool = Tool.from_function(
    name="noteguide_qa",
    description="Use this tool to answer questions based on the uploaded study notes.",
    func=simple_retrieval
)

quiz_tool = Tool.from_function(
    name="quiz_generator",
    description="Use this to generate test questions from the notes based on a given topic.",
    func=lambda q: generate_quiz_from_docs(load_chroma_index().similarity_search(q, k=3), True).content,
)

tools = [retrieval_tool, quiz_tool]

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    # memory=memory,
    verbose=True,
)


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")
    if not user_input:
        return JSONResponse(status_code=400, content={"error": "Missing user input."})

    try:
        response = agent_executor.invoke(user_input)
        print(f"Response: {response}")

        if isinstance(response, dict) and "output" in response:
            return {"response": response["output"]}
        return {"response": response}
    except RateLimitError as e:
        return {"response": "Rate limit exceeded. Please wait and try again."}
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
