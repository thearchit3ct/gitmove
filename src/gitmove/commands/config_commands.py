"""
CLI commands for configuration management in GitMove.

This module provides CLI commands for working with GitMove configuration,
separating command registration from the configuration validation logic.
"""

import os
import sys
import click
from rich.console import Console

from gitmove.validators.config_validator import ConfigValidator

def register_config_commands(cli):
    """
    Register configuration-related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    @cli.group()
    def config():
        """Configuration management commands."""
        pass
    
    @config.command()
    @click.option('--output', '-o', type=click.Path(), help='Output path for sample config')
    def generate(output):
        """Generate a sample configuration file."""
        validator = ConfigValidator()
        sample_config = validator.generate_sample_config(output)
        
        if not output:
            click.echo(sample_config)
        else:
            click.echo(f"Sample configuration saved to {output}")
    
    @config.command()
    @click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
    def validate(config):
        """Validate configuration file."""
        validator = ConfigValidator(config)
        try:
            validated_config = validator.validate_config()
            click.echo("Configuration is valid.")
            
            # Display recommendations
            recommendations = validator.recommend_configuration(validated_config)
            if recommendations:
                click.echo("\nRecommendations:")
                for key, recommendation in recommendations.items():
                    click.echo(f"- {recommendation}")
        except ValueError as e:
            click.echo(str(e))
            sys.exit(1)
    
    return config  # Return the config group for use in CLI or extensions