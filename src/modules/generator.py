import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.callbacks.base import CallbackManagerMixin
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage
from langchain_community.agent_toolkits import FileManagementToolkit
from src.core.llm import LLMFactory
from src.core.logger import get_logger
from src.db_models import RepoMapping
from src.core.events import DocumentationGeneratedEvent
from typing import Dict, List, Any

from pathlib import Path

logger = get_logger(__name__)


class ToolMixin(CallbackManagerMixin):
    def on_tool_start(
            self,
            serialized: dict[str, Any],
            input_str: str,
            *,
            tags: list[str] | None = None,
            metadata: dict[str, Any] | None = None,
            inputs: dict[str, Any] | None = None,
            **kwargs: Any,
    ) -> Any:
        logger.info("tool called, input: %s", input_str)


tool_callback = ToolMixin()


@tool
def list_repo_files(root: str) -> List[str]:
    """List all files in the repository. I recommend to check './src'"""
    logger.info("list_repo_files called with arg root: %s", root)
    return [
        str(p) for p in Path(root).rglob("*")
        if p.is_file()
    ]


@tool
def read_repo_file(path: str) -> str:
    """Read a repository file and return its contents. Relative paths recommended."""
    logger.info("read_repo_file called with arg path: %s", path)
    try:
        return Path(path).read_text()
    except Exception as e:
        return f"ERROR: {e}"


@tool
def emit_documentation_patches(patches: Dict[str, str]) -> Dict[str, str]:
    """
    Final tool.
    Use this to emit documentation updates.
    Keys are doc file paths, values are full markdown contents.
    """
    return patches


class DocumentationGenerator:
    def __init__(self, provider: str = "ollama", model: str = "gpt-oss:20b"):
        self.llm = LLMFactory.create_llm(provider, model)
        self.parser = JsonOutputParser()

        # We instruct the model to return a JSON object where keys are filenames and values are markdown content.
        self.prompt = """
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
            """

    def generate(self, diffs: list, mapping: RepoMapping, commit_hash: str) -> DocumentationGeneratedEvent:
        """
        Generates documentation patches based on the diff.
        """
        try:
            print(f"Generating docs for repo {mapping.id}, commit {commit_hash}...")
            docs_toolkit = FileManagementToolkit(
                root_dir=str(Path(mapping.docs_path))
            )
            tools = docs_toolkit.get_tools()
            tools.append(list_repo_files)
            tools.append(read_repo_file)
            agent = create_agent(model=self.llm, system_prompt=self.prompt.format(diff=str(diffs)))
            # Invoke the chain
            result = agent.invoke({"messages": []}, config={"callbacks": [tool_callback]})
            print(result['messages'][0].content)
            return DocumentationGeneratedEvent(
                repo_id=mapping.id,
                commit_hash=commit_hash,
                patches=json.loads(result['messages'][0].content)
            )
        except Exception as e:
            print(f"Error generating documentation: {e}")
            # Return empty event on failure to keep pipeline moving (or re-raise if we want retry logic)
            return DocumentationGeneratedEvent(
                repo_id=mapping.id,
                commit_hash=commit_hash,
                patches={}
            )
