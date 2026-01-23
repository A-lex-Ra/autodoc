import git
from src.models import RepoMapping
from typing import Optional

class RepositoryWatcher:
    def check_for_updates(self, mapping: RepoMapping) -> Optional[str]:
        """
        Checks if valid new commits exist in the source repo.
        Returns the HEAD commit hash if it differs from the last processed commit.
        """
        try:
            repo = git.Repo(mapping.source_path)
            if repo.bare:
                return None
            
            head_commit = repo.head.commit.hexsha
            
            if head_commit != mapping.last_processed_commit:
                return head_commit
            return None
        except Exception as e:
            print(f"Error watching repo {mapping.source_path}: {e}")
            return None
