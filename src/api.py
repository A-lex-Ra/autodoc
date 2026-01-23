from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from contextlib import asynccontextmanager
import asyncio
from typing import List

from src.database import get_session, create_db_and_tables, engine
from src.models import RepoMapping, ProcessingLog
from src.modules.pipeline import PipelineOrchestrator

# Global flag to control the generic watcher loop
watcher_running = True

async def watcher_loop():
    """
    Background task that runs the pipeline periodically.
    """
    print("Starting watcher loop...")
    while watcher_running:
        with Session(engine) as session:
            orchestrator = PipelineOrchestrator(session)
            # Run synchronously inside the loop, or make orchestrator async.
            # For simplicity, we run the synchronous run() method.
            # In a heavy app, run_in_executor would be better.
            try:
                orchestrator.run()
            except Exception as e:
                print(f"Error in watcher loop: {e}")
        
        await asyncio.sleep(60) # check every 60 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Start the watcher loop in the background
    task = asyncio.create_task(watcher_loop())
    yield
    # Cleanup
    global watcher_running
    watcher_running = False
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/mappings/", response_model=RepoMapping)
def create_mapping(mapping: RepoMapping, session: Session = Depends(get_session)):
    session.add(mapping)
    session.commit()
    session.refresh(mapping)
    return mapping

@app.get("/mappings/", response_model=List[RepoMapping])
def read_mappings(session: Session = Depends(get_session)):
    mappings = session.exec(select(RepoMapping)).all()
    return mappings

@app.delete("/mappings/{mapping_id}")
def delete_mapping(mapping_id: int, session: Session = Depends(get_session)):
    mapping = session.get(RepoMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    session.delete(mapping)
    session.commit()
    return {"ok": True}

@app.post("/trigger/{mapping_id}")
def trigger_mapping(mapping_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    mapping = session.get(RepoMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    def process_now():
        with Session(engine) as s:
            # Re-fetch to be safe or pass detached object if orchestrator handles it
            m = s.get(RepoMapping, mapping_id)
            if m:
                PipelineOrchestrator(s).process_mapping(m)
    
    background_tasks.add_task(process_now)
    return {"message": "Processing triggered"}
