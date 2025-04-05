import os

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_and_split_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        loader = TextLoader(file_path, encoding='utf-8')
    elif ext == ".pdf":
        loader = PyPDFLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    docs = splitter.split_documents(documents)
    docs = [d for d in docs if d.page_content.strip()]

    if not docs:
        raise ValueError("Empty document after splitting.")

    print(f"Successfully loaded {len(docs)} chunks from {file_path}.")
    print(f"First chunk: {docs[0].page_content[:100]}...")  # Print the first 100 characters of the first chunk

    return docs
