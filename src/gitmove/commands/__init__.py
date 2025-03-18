"""
Command modules for GitMove CLI.

This package contains all command modules for the GitMove CLI,
organized by functionality.
"""

def register_config_commands(cli):
    """
    Register configuration-related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    from gitmove.commands.config_commands import register_config_commands as _register
    return _register(cli)

def register_cicd_commands(cli):
    """
    Register CI/CD related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    from gitmove.commands.cicd_commands import register_cicd_commands as _register
    return _register(cli)

def generate_ci_config(cli):
    """
    CLI command to detect and generate CI configuration.
    
    Args:
        cli: Click CLI group
    """
    from gitmove.commands.cicd_commands import generate_ci_config as _generate
    return _generate(cli)

def register_env_config_commands(cli):
    """
    Register environment configuration-related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    from gitmove.commands.env_commands import register_env_config_commands as _register
    return _register(cli)

def register_sync_commands(cli):
    """
    Register sync-related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    from gitmove.commands.sync_commands import register_sync_commands as _register
    return _register(cli)

__all__ = [
    'register_config_commands',
    'register_cicd_commands',
    'generate_ci_config',
    'register_env_config_commands',
    'register_sync_commands',
]