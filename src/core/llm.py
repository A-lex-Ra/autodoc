from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel

class LLMFactory:
    @staticmethod
    def create_llm(provider: str = "ollama", model: str = "gpt-oss:20b") -> BaseChatModel:
        if provider == "ollama":
            return ChatOllama(model=model)
        # Future extension for other providers
        raise ValueError(f"Unsupported provider: {provider}")
