import typer
import uvicorn
from sqlmodel import Session, select
from src.database import create_db_and_tables, engine
from src.db_models import RepoMapping, ProcessingLog
import os

app = typer.Typer()

@app.command()
def init_db():
    create_db_and_tables()
    print("Database initialized.")

@app.command()
def register(source: str, docs: str, name: str = None):
    """
    Register a new repository to watch.
    """
    if not os.path.exists(source):
        print(f"Error: Source path {source} does not exist.")
        return
    
    with Session(engine) as session:
        mapping = RepoMapping(source_path=source, docs_path=docs, name=name or os.path.basename(source))
        session.add(mapping)
        session.commit()
        print(f"Registered {mapping.name} (ID: {mapping.id})")

@app.command()
def list():
    """
    List all registered repositories.
    """
    with Session(engine) as session:
        mappings = session.exec(select(RepoMapping)).all()
        for m in mappings:
            print(f"[{m.id}] {m.name}: {m.source_path} -> {m.docs_path} (Last: {m.last_processed_commit[:7]})")

@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """
    Start the API server and the Watcher daemon.
    """
    uvicorn.run("src.api:app", host=host, port=port, reload=True)

@app.command()
def logs(mapping_id: int, limit: int = 5):
    """
    Show recent processing logs for a mapping.
    """
    with Session(engine) as session:
        logs = session.exec(select(ProcessingLog).where(ProcessingLog.mapping_id == mapping_id).order_by(ProcessingLog.timestamp.desc()).limit(limit)).all()
        if not logs:
            print(f"No logs found for mapping {mapping_id}")
            return
        
        for log in logs:
            print(f"[{log.timestamp}] Status: {log.status} | Commit: {log.commit_hash[:7]} | Summary: {log.summary}")
            if log.patches:
                print(f"  Patches: {log.patches[:100]}...") # Truncate for display

if __name__ == "__main__":
    app()
