from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

class BaseEvent(BaseModel):
    timestamp: datetime = datetime.now()
    event_type: str

class DocumentationGeneratedEvent(BaseEvent):
    event_type: str = "documentation_generated"
    repo_id: int
    commit_hash: str
    # Use a dictionary to map file paths to new content (patches)
    # e.g. {"docs/intro.md": "# Introduction\n..."}
    patches: Dict[str, str] 
    
class SourceChangedEvent(BaseEvent):
    event_type: str = "source_changed"
    repo_id: int
    commit_hash: str
    previous_hash: str
