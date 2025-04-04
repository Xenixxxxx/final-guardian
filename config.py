import os

import azure.identity
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.agents.agent_types import AgentType
from langchain.agents import initialize_agent

load_dotenv(override=True)

token_provider = azure.identity.get_bearer_token_provider(
    azure.identity.DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
    azure_ad_token_provider=token_provider,
)

agent_executor = initialize_agent(
    tools=[
    ],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
)

embedding = AzureOpenAIEmbeddings(
    deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_version=os.getenv("AZURE_EMBEDDING_VERSION")
)
