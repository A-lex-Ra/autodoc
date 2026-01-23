from sqlmodel import Session
from src.models import RepoMapping, ProcessingLog
from src.modules.watcher import RepositoryWatcher
from src.modules.processor import DiffProcessor
from src.modules.generator import DocumentationGenerator
from src.modules.writer import FileWriter
from datetime import datetime

class PipelineOrchestrator:
    def __init__(self, session: Session):
        self.session = session
        self.watcher = RepositoryWatcher()
        self.processor = DiffProcessor()
        # In a real app, provider/model might come from config
        self.generator = DocumentationGenerator() 
        self.writer = FileWriter()

    def run(self):
        """
        Main loop iteration. checks all active mappings.
        """
        mappings = self.session.query(RepoMapping).filter(RepoMapping.is_active == True).all()
        for mapping in mappings:
            self.process_mapping(mapping)

    def process_mapping(self, mapping: RepoMapping):
        # 1. Check for changes
        new_commit = self.watcher.check_for_updates(mapping)
        if not new_commit:
            return

        print(f"Detected updates for {mapping.name} ({mapping.source_path})...")

        try:
            # 2. Get Diff
            diff = self.processor.get_diff(mapping, new_commit)
            if not diff.strip():
                print("Diff is empty, skipping.")
                self._update_state(mapping, new_commit, "SKIPPED", "Empty diff")
                return

            # 3. Generate Docs
            # The output here is an Event
            doc_event = self.generator.generate(diff, mapping, new_commit)
            
            # 4. Write
            self.writer.write(mapping, doc_event)

            # 5. Update State
            self._update_state(mapping, new_commit, "SUCCESS", f"Generated {len(doc_event.patches)} files")
        
        except Exception as e:
            print(f"Pipeline failed for {mapping.name}: {e}")
            self._update_state(mapping, new_commit, "FAILED", str(e))

    def _update_state(self, mapping: RepoMapping, commit: str, status: str, summary: str):
        mapping.last_processed_commit = commit
        mapping.updated_at = datetime.utcnow()
        
        log = ProcessingLog(
            mapping_id=mapping.id,
            commit_hash=commit,
            status=status,
            summary=summary
        )
        self.session.add(log)
        self.session.add(mapping)
        self.session.commit()
