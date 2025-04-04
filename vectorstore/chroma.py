from langchain_chroma import Chroma
from dotenv import load_dotenv

from config import embedding

load_dotenv()

CHROMA_PATH = "vectorstore/chroma_db"


def create_chroma_index(documents):
    texts = [doc.page_content for doc in documents if doc.page_content.strip()]
    if not texts:
        raise ValueError("No valid texts found in documents.")

    vectorstore = Chroma.from_texts(
        texts,
        embedding=embedding,
        persist_directory=CHROMA_PATH
    )
    return vectorstore

def load_chroma_index():
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding)
