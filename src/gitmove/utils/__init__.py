"""
Utilitaires pour le projet GitMove.

Ce package contient des fonctions utilitaires utilisées dans tout le projet.
"""

from gitmove.utils.git_commands import (
    get_repo,
    get_current_branch,
    get_main_branch,
    is_branch_merged,
    get_branch_last_commit_date,
    get_branch_age,
    get_branch_commit_count,
    get_tracking_branch,
    get_branch_divergence,
    get_common_ancestor,
    get_modified_files,
    fetch_updates,
    delete_local_branch,
    delete_remote_branch,
    merge_branch,
    rebase_branch,
)

from gitmove.utils.logger import (
    setup_logger,
    get_logger,
    set_verbose_mode,
    set_quiet_mode,
)

__all__ = [
    # Git commands
    "get_repo",
    "get_current_branch",
    "get_main_branch",
    "is_branch_merged",
    "get_branch_last_commit_date",
    "get_branch_age",
    "get_branch_commit_count",
    "get_tracking_branch",
    "get_branch_divergence",
    "get_common_ancestor",
    "get_modified_files",
    "fetch_updates",
    "delete_local_branch",
    "delete_remote_branch",
    "merge_branch",
    "rebase_branch",
    
    # Logger
    "setup_logger",
    "get_logger",
    "set_verbose_mode",
    "set_quiet_mode",
]