"""
Command modules for GitMove CLI.

This package contains all command modules for the GitMove CLI,
organized by functionality.
"""

from gitmove.commands.config_commands import register_config_commands
from gitmove.commands.cicd_commands import register_cicd_commands, generate_ci_config
from gitmove.commands.env_commands import register_env_config_commands
# Import other command modules as they are implemented
# from gitmove.commands.branch_commands import register_branch_commands
# from gitmove.commands.sync_commands import register_sync_commands

__all__ = [
    'register_config_commands',
    'register_cicd_commands',
    'generate_ci_config',
    'register_env_config_commands',
    # Add other command registration functions as they are implemented
]