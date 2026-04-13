from langchain_openai import OpenAIEmbeddings
from app.config import settings


def get_embedding_function() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,
    )
