from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class RepoMapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_path: str = Field(index=True)
    docs_path: str
    name: Optional[str] = None
    last_processed_commit: str = Field(default="")
    is_active: bool = Field(default=True)
    ai_provider: str = Field(default="ollama")
    ai_model: str = Field(default="gpt-oss:20b")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProcessingLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mapping_id: int = Field(foreign_key="repomapping.id")
    commit_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str
    summary: Optional[str] = None
    patches: Optional[str] = None # JSON string of generated patches
