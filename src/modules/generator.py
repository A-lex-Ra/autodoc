import json
import re
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage
from langchain_community.agent_toolkits import FileManagementToolkit

from src import config
from src.core.llm import LLMFactory
from src.core.logger import get_logger
from src.db_models import RepoMapping
from src.core.events import DocumentationGeneratedEvent
from typing import Dict, List, Any

from pathlib import Path

logger = get_logger(__name__)


class ToolMixin(BaseCallbackHandler):
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
        logger.info("tool callback %s called, input: %s", str(metadata), input_str)


tool_callback = ToolMixin()


# @tool
# def emit_documentation_patches(patches: Dict[str, str]) -> Dict[str, str]:
#     """
#     Final tool.
#     Use this to emit documentation updates.
#     Keys are doc file paths, values are full markdown contents.
#     """
#     return patches


def parse_json_string(raw_str: str) -> Dict[str, str]:
    """Parse JSON, remove ```json/``` and spaces"""
    cleaned = re.sub(r'```\w*', '', raw_str).strip()
    return json.loads(cleaned)


class DocumentationGenerator:
    def __init__(self, provider: str = "ollama", model: str = "gpt-oss:20b"):
        self.llm = LLMFactory.create_llm(provider, model)
        self.parser = JsonOutputParser()

        # We instruct the model to return a JSON object where keys are filenames and values are markdown content.
        self.prompt = """
            You are an expert technical writer.
            Analyze the following git diff and generate or update the documentation.
            
            Please call tools to navigate, and at the end return ONLY a valid JSON object.
            The keys should be the file paths of the documentation files (e.g., "modules/auth.md", "README.md").
            The values should be the full markdown content for those files.
            
            If the diff implies a new feature, create a new doc file.
            If it modifies existing logic, update the corresponding doc file.
            
            GIT DIFF:
            {diff}
            
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

            @tool
            def list_repo_files(dir_path: str) -> List[str]:
                """List all files and directories in the repository (one level only, non-recursive). I recommend to check './src'"""
                root_path = Path(dir_path)
                if not root_path.is_absolute():
                    root_path = Path(mapping.source_path)/root_path

                if not root_path.exists():
                    logger.warning("Path does not exist: %s", dir_path)
                    return []

                if not root_path.is_dir():
                    logger.warning("Path is not a directory: %s", dir_path)
                    return []

                ignore_dirs = getattr(config, 'IGNORE_DIRS', set())

                result = []
                for item in root_path.iterdir():
                    # Skip dot-marked and ignored folders
                    if item.name.startswith('.') and item.name not in {'.gitignore', '.env'}:
                        continue
                    if item.name in ignore_dirs:
                        continue

                    if item.is_file():
                        result.append(item.name)
                    elif item.is_dir():
                        result.append(f"{item.name}/")

                logger.info("list_repo_files called with arg dir_path: %s\nresult: %s", dir_path, str(result))
                return sorted(result)

            @tool
            def read_repo_file(path: str) -> str:
                """Read a repository file and return its contents. Relative paths recommended."""
                logger.info("read_repo_file called with arg dir_path: %s", path)
                try:
                    if not path.is_absolute():
                        path = Path(mapping.source_path)/path
                    result = Path(path).read_text()
                    logger.info("read_repo_file called with arg dir_path: %s\nresult: %s", path, str(result))
                    return result
                except Exception as e:
                    return f"ERROR: {e}"

            tools = docs_toolkit.get_tools()
            tools.append(list_repo_files)
            tools.append(read_repo_file)
            agent = create_agent(model=self.llm, tools=tools, system_prompt=self.prompt.format(diff=str(diffs)))
            # Invoke the chain
            result = agent.invoke({"messages": []}, config={"callbacks": [tool_callback]})
            print(result['messages'][0].content)
            return DocumentationGeneratedEvent(
                repo_id=mapping.id,
                commit_hash=commit_hash,
                patches=parse_json_string(result['messages'][0].content)
            )
        except Exception as e:
            print(f"Error generating documentation: {e}")
            # Return empty event on failure to keep pipeline moving (or re-raise if we want retry logic)
            return DocumentationGeneratedEvent(
                repo_id=mapping.id,
                commit_hash=commit_hash,
                patches={}
            )
