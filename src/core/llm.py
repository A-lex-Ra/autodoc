from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from os import getenv
from dotenv import load_dotenv

class LLMFactory:
    @staticmethod
    def create_llm(provider: str = "ollama", model: str = "gpt-oss:20b") -> BaseChatModel:
        if provider == "ollama":
            return ChatOllama(model=model)
        if provider == "openrouter":
            return ChatOpenAI(
                api_key=getenv("OR_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model=model
            )
        # Future extension for other providers
        raise ValueError(f"Unsupported provider: {provider}")
