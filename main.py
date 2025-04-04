import re
import os
import shutil

from chains.answer_evaluator import evaluate_answer
from chains.doc_loader import load_and_split_document
from chains.quiz_gen import generate_quiz_from_docs
from config import llm
from vectorstore.chroma import create_chroma_index, load_chroma_index
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, Request
from langchain.tools import Tool
from langchain.agents import AgentType, initialize_agent
from fastapi.responses import JSONResponse
from openai import RateLimitError

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    docs = load_and_split_document(file_location)
    create_chroma_index(docs)

    return {"message": "File uploaded and processed successfully", "filename": file.filename}


@app.post("/generate-quiz")
async def generate_quiz(topic: str = Form(...)):
    index = load_chroma_index()
    docs = index.similarity_search(topic, k=10)
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
    results = []
    for item in payload.answers:
        result = evaluate_answer(item.question, item.correct_answer, item.user_answer)
        results.append({
            "question": item.question,
            "result": result
        })
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
