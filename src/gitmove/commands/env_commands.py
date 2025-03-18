"""
CLI commands for environment variable configuration in GitMove.

This module provides CLI commands for working with environment variables,
separating command registration from the environment configuration logic.
"""

import os
import sys
import click

from gitmove.commands.env_config import EnvConfigLoader

def register_env_config_commands(cli):
    """
    Register environment configuration-related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    @cli.group()
    def env():
        """Environment configuration management commands."""
        pass
    
    @env.command('generate-template')
    @click.option('--output', '-o', type=click.Path(), help='Output path for environment variable template')
    def generate_template(output):
        """Generate an environment variable configuration template."""
        template = EnvConfigLoader.generate_env_template()
        
        if output:
            with open(output, 'w') as f:
                f.write(template)
            click.echo(f"Environment variable template saved to {output}")
        else:
            click.echo(template)
    
    @env.command('validate')
    @click.option('--prefix', default='GITMOVE_', help='Environment variable prefix')
    def validate_env_config(prefix):
        """Validate current environment configuration."""
        # Load configuration from environment
        config = EnvConfigLoader.load_config(prefix=prefix)
        
        # Validate the configuration
        errors = EnvConfigLoader.validate_env_config(config)
        
        if not errors:
            click.echo("Environment configuration is valid.")
        else:
            click.echo("Environment configuration validation failed:")
            for section, section_errors in errors.items():
                click.echo(f"\n{section.capitalize()} Errors:")
                for error in section_errors:
                    click.echo(f"  - {error}")
                sys.exit(1)
    
    @env.command('list')
    def list_env_vars():
        """List all GitMove-related environment variables."""
        gitmove_vars = {
            key: value for key, value in os.environ.items() 
            if key.startswith(EnvConfigLoader.ENV_PREFIX)
        }
        
        if not gitmove_vars:
            click.echo("No GitMove-related environment variables found.")
        else:
            click.echo("GitMove Environment Variables:")
            for key, value in sorted(gitmove_vars.items()):
                click.echo(f"{key}: {value}")
                
    return env  # Return the group for use in other modules