"""Git Integration Tool - BUG FIXED"""
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GitError(Exception):
    """Custom exception for Git operations."""
    pass


class GitTool:
    """Git integration for Forge with proper error handling."""
    
    def __init__(self, working_dir: Path, branch_prefix: str = "forge/", commit_prefix: str = "[Forge]"):
        self.working_dir = working_dir
        self.branch_prefix = branch_prefix
        self.commit_prefix = commit_prefix
        self.logger = logging.getLogger("forge.tools.git")
    
    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command safely."""
        cmd = ["git"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if check and result.returncode != 0:
                raise GitError(f"Git command failed: {result.stderr.strip()}")
            return result
        except subprocess.TimeoutExpired:
            raise GitError("Git command timed out")
        except FileNotFoundError:
            raise GitError("Git is not installed")
    
    def is_repo(self) -> bool:
        """Check if working directory is a git repository."""
        try:
            result = self._run_git("rev-parse", "--git-dir", check=False)
            return result.returncode == 0
        except GitError:
            return False
    
    def is_detached_head(self) -> bool:
        """Check if repository is in detached HEAD state."""
        try:
            result = self._run_git("symbolic-ref", "-q", "HEAD", check=False)
            return result.returncode != 0
        except GitError:
            return True
    
    def get_current_branch(self) -> str | None:
        """Get current branch name, handling detached HEAD."""
        try:
            if self.is_detached_head():
                # In detached HEAD, get the commit hash instead
                result = self._run_git("rev-parse", "--short", "HEAD")
                return f"detached-{result.stdout.strip()}"
            
            result = self._run_git("branch", "--show-current")
            branch = result.stdout.strip()
            return branch if branch else None
        except GitError as e:
            self.logger.warning(f"Could not get current branch: {e}")
            return None
    
    def has_uncommitted_changes(self) -> bool:
        """Check for uncommitted changes."""
        try:
            result = self._run_git("status", "--porcelain")
            return bool(result.stdout.strip())
        except GitError:
            return False
    
    def create_branch(self, name: str) -> bool:
        """Create a new branch with the forge prefix."""
        branch_name = f"{self.branch_prefix}{name}"
        try:
            # Handle detached HEAD by creating branch from current commit
            if self.is_detached_head():
                self.logger.info("Creating branch from detached HEAD state")
            
            self._run_git("checkout", "-b", branch_name)
            self.logger.info(f"Created branch: {branch_name}")
            return True
        except GitError as e:
            self.logger.error(f"Failed to create branch: {e}")
            return False
    
    def checkout_branch(self, name: str, create: bool = False) -> bool:
        """Checkout a branch."""
        try:
            if create:
                self._run_git("checkout", "-b", name)
            else:
                self._run_git("checkout", name)
            self.logger.info(f"Checked out branch: {name}")
            return True
        except GitError as e:
            self.logger.error(f"Failed to checkout branch: {e}")
            return False
    
    def stage_files(self, files: list[str] | None = None) -> bool:
        """Stage files for commit."""
        try:
            if files:
                self._run_git("add", *files)
            else:
                self._run_git("add", "-A")
            return True
        except GitError as e:
            self.logger.error(f"Failed to stage files: {e}")
            return False
    
    def commit(self, message: str) -> bool:
        """Create a commit with the forge prefix."""
        full_message = f"{self.commit_prefix} {message}"
        try:
            # Check if there are staged changes
            result = self._run_git("diff", "--cached", "--quiet", check=False)
            if result.returncode == 0:
                self.logger.info("No staged changes to commit")
                return True
            
            self._run_git("commit", "-m", full_message)
            self.logger.info(f"Created commit: {full_message[:50]}...")
            return True
        except GitError as e:
            self.logger.error(f"Failed to commit: {e}")
            return False
    
    def get_diff(self, staged: bool = False) -> str:
        """Get diff of changes."""
        try:
            if staged:
                result = self._run_git("diff", "--cached")
            else:
                result = self._run_git("diff")
            return result.stdout
        except GitError as e:
            self.logger.error(f"Failed to get diff: {e}")
            return ""
    
    def get_log(self, count: int = 10) -> list[dict[str, str]]:
        """Get recent commit log."""
        try:
            result = self._run_git(
                "log",
                f"-{count}",
                "--pretty=format:%H|%s|%an|%ad",
                "--date=short",
            )
            
            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3],
                        })
            return commits
        except GitError as e:
            self.logger.error(f"Failed to get log: {e}")
            return []
    
    def stash(self) -> bool:
        """Stash current changes."""
        try:
            self._run_git("stash", "push", "-m", "Forge auto-stash")
            self.logger.info("Stashed changes")
            return True
        except GitError as e:
            self.logger.error(f"Failed to stash: {e}")
            return False
    
    def stash_pop(self) -> bool:
        """Pop stashed changes."""
        try:
            self._run_git("stash", "pop")
            self.logger.info("Popped stash")
            return True
        except GitError as e:
            self.logger.error(f"Failed to pop stash: {e}")
            return False
    
    def reset_hard(self, ref: str = "HEAD") -> bool:
        """Hard reset to a reference."""
        try:
            self._run_git("reset", "--hard", ref)
            self.logger.info(f"Reset to {ref}")
            return True
        except GitError as e:
            self.logger.error(f"Failed to reset: {e}")
            return False
