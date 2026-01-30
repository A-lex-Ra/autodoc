import git

from src.db_models import RepoMapping
_EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

class DiffProcessor:
    def get_diffs(self, mapping: RepoMapping, new_commit: str) -> list:
        """
        Retrieves the git diff between the last processed commit and the new commit.
        If last_processed_commit is empty, diffs against empty tree (shows full codebase).
        """
        try:
            repo = git.Repo(mapping.source_path)

            if not mapping.last_processed_commit:
                # First run: diff against empty tree
                base = git.NULL_TREE
            else:
                base = mapping.last_processed_commit

            try:
                diffs = repo.commit(new_commit).diff(base, create_patch=True, R=True)
                return list(map(str, diffs))
            except git.exc.GitCommandError as e:
                # Handle rebase, force push, or missing commit
                print(f"Warning: Could not diff {base}..{new_commit}: {e}")
                print("Falling back to empty tree diff")
                diffs = repo.commit(new_commit).diff(git.NULL_TREE, create_patch=True, R=True)
                return list(map(str, diffs))

        except Exception as e:
            print(f"Error getting diff for {mapping.source_path}: {e}")
            return []
