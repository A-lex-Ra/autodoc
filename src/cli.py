import typer
import uvicorn
from sqlmodel import Session, select
from src.database import create_db_and_tables, engine
from src.models import RepoMapping
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

if __name__ == "__main__":
    app()
