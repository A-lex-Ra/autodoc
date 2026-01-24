import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.core.llm import LLMFactory
from src.models import RepoMapping
from src.core.events import DocumentationGeneratedEvent
from typing import Dict

class DocumentationGenerator:
    def __init__(self, provider: str = "ollama", model: str = "gpt-oss:20b"):
        self.llm = LLMFactory.create_llm(provider, model)
        self.parser = JsonOutputParser()
        
        # We instruct the model to return a JSON object where keys are filenames and values are markdown content.
        self.prompt = PromptTemplate(
            template="""
            You are an expert technical writer. 
            Analyze the following git diff and generate or update the documentation.
            
            Return ONLY a valid JSON object.
            The keys should be the file paths of the documentation files (e.g., "modules/auth.md", "README.md").
            The values should be the full markdown content for those files.
            
            If the diff implies a new feature, create a new doc file.
            If it modifies existing logic, update the corresponding doc file.
            
            GIT DIFF:
            {diff}
            
            JSON OUTPUT:
            """,
            input_variables=["diff"],
        )
        self.chain = self.prompt | self.llm | self.parser

    def generate(self, diff: str, mapping: RepoMapping, commit_hash: str) -> DocumentationGeneratedEvent:
        """
        Generates documentation patches based on the diff.
        """
        try:
            print(f"Generating docs for repo {mapping.id}, commit {commit_hash}...")
            # Invoke the chain
            result: Dict[str, str] = self.chain.invoke({"diff": diff})
            
            return DocumentationGeneratedEvent(
                repo_id=mapping.id,
                commit_hash=commit_hash,
                patches=result
            )
        except Exception as e:
            print(f"Error generating documentation: {e}")
            # Return empty event on failure to keep pipeline moving (or re-raise if we want retry logic)
            return DocumentationGeneratedEvent(
                repo_id=mapping.id,
                commit_hash=commit_hash,
                patches={}
            )
