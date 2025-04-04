from langchain.prompts import PromptTemplate
from config import llm

MAX_CONTEXT_LENGTH = 1000

quiz_prompt = PromptTemplate(
    input_variables=["context"],
    template="""
You are a university exam question writer. Based on the content below, generate 3 questions:

Instructions:
- Include 2 multiple choice questions and 1 short answer question.
- Each question must include the correct answer.
- Use the following format:

Q1: ...
A1: ...
Q2: ...
A2: ...
Q3: ...
A3: ...

Content:
{context}
"""
)

question_chain = quiz_prompt | llm

def generate_quiz_from_docs(docs):
    all_text = ""
    for doc in docs:
        if len(all_text) + len(doc.page_content) > MAX_CONTEXT_LENGTH:
            break
        all_text += doc.page_content + "\n"

    if not all_text.strip():
        raise ValueError("No content found to generate quiz.")

    result = question_chain.invoke({"context": all_text})
    return result
