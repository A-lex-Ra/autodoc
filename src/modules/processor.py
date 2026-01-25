import git
from src.db_models import RepoMapping

class DiffProcessor:
    def get_diffs(self, mapping: RepoMapping, new_commit: str) -> list:
        """
        Retrieves the git diff between the last processed commit and the new commit.
        If last_processed_commit is empty, it might diff against an empty tree or just return recent changes.
        For simplicity, if empty, we might just look at the last commit or all files.
        """
        try:
            repo = git.Repo(mapping.source_path)
            
            if not mapping.last_processed_commit:
                # First run or reset: ideally we'd document everything. 
                # For this MVP, let's just get the diff of the HEAD commit itself (stats from parent).
                # Or, diff against the empty tree (full codebase). 
                # Let's try diffing against HEAD~1 (changes in latest commit)
                 if repo.head.commit.parents:
                    diff = repo.head.commit.diff("HEAD~1")
                 else:
                     # Initial commit
                    diff = [repo.git.show("HEAD")]
            else:
                diff = repo.commit(new_commit).diff(mapping.last_processed_commit)
            print(diff)
            return diff
        except Exception as e:
            print(f"Error getting diff for {mapping.source_path}: {e}")
            return ""
