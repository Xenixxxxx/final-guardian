from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from config import llm

evaluation_prompt = PromptTemplate(
    input_variables=["question", "correct_answer", "user_answer"],
    template="""
You are a strict but fair exam grader.  
Please evaluate the student's answer to the following question:

Question:
{question}

Correct Answer:
{correct_answer}

Student's Answer:
{user_answer}

Instructions:
- Indicate whether the answer is correct or not (Correct / Incorrect).
- Provide a short explanation why.

Respond in the following format:

Result: Correct / Incorrect  
Explanation: ...
"""
)

evaluation_chain = evaluation_prompt | llm


def evaluate_answer(question, correct_answer, user_answer):
    result = evaluation_chain.invoke({
        "question": question,
        "correct_answer": correct_answer,
        "user_answer": user_answer
    })
    return result
