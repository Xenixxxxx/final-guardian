from langchain.prompts import PromptTemplate
from config import llm

MAX_CONTEXT_LENGTH = 1000

DEFAULT_TEMPLATE = """
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

SINGLE_QA_TEMPLATE = """
You are a university tutor. Based on the content below, generate 1 short answer question.

Instructions:
- Do NOT include multiple choice questions.
- Include the correct answer after the question.
- Use the following format:

Q1: ...
A1: ...

Content:
{context}
"""

def generate_quiz_from_docs(docs, single_quiz=False):
    all_text = ""
    for doc in docs:
        if len(all_text) + len(doc.page_content) > MAX_CONTEXT_LENGTH:
            break
        all_text += doc.page_content + "\n"

    if not all_text.strip():
        raise ValueError("No content found to generate quiz.")

    template = SINGLE_QA_TEMPLATE if single_quiz else DEFAULT_TEMPLATE
    prompt = PromptTemplate(input_variables=["context"], template=template)
    question_chain = prompt | llm

    result = question_chain.invoke({"context": all_text})
    return result
