import os
from src.core.events import DocumentationGeneratedEvent
from src.db_models import RepoMapping

class FileWriter:
    def write(self, mapping: RepoMapping, event: DocumentationGeneratedEvent):
        """
        Writes the generated patches to the destination docs folder.
        """
        if not event.patches:
            print("No patches to write.")
            return

        base_path = mapping.docs_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        for rel_path, content in event.patches.items():
            full_path = os.path.join(base_path, rel_path)
            
            # Ensure subdirectories exist
            dir_name = os.path.dirname(full_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
            
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Written {full_path}")
            except Exception as e:
                print(f"Failed to write {full_path}: {e}")
