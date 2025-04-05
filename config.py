import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

load_dotenv(override=True)

llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
    deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
)

embedding = AzureOpenAIEmbeddings(
    deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_version=os.getenv("AZURE_EMBEDDING_VERSION")
)
