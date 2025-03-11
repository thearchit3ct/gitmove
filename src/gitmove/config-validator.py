"""
Enhanced Configuration Validation for GitMove

Provides advanced configuration validation with detailed error reporting
and environment variable support.
"""

import os
import re
from typing import Any, Dict, List, Optional, Union

import toml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

class ConfigValidator:
    """
    Advanced configuration validator for GitMove.
    
    Provides comprehensive configuration validation with:
    - Detailed error reporting
    - Environment variable interpolation
    - Schema-based validation
    - Configuration recommendation
    """
    
    # Configuration schema defining validation rules
    _CONFIG_SCHEMA = {
        "general": {
            "main_branch": {
                "type": str,
                "required": True,
                "pattern": r'^[a-zA-Z0-9_\-./]+$',
                "default": "main"
            },
            "verbose": {
                "type": bool,
                "default": False
            }
        },
        "clean": {
            "auto_clean": {
                "type": bool,
                "default": False
            },
            "exclude_branches": {
                "type": list,
                "item_type": str,
                "default": ["develop", "staging"]
            },
            "age_threshold": {
                "type": int,
                "min": 1,
                "max": 365,
                "default": 30
            }
        },
        "sync": {
            "default_strategy": {
                "type": str,
                "allowed": ["merge", "rebase", "auto"],
                "default": "rebase"
            },
            "auto_sync": {
                "type": bool,
                "default": True
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ConfigValidator.
        
        Args:
            config_path: Path to the configuration file
        """
        self.console = Console()
        self.config_path = config_path or self._get_default_config_path()
        self.env_prefix = "GITMOVE_"
    
    @classmethod
    def _get_default_config_path(cls) -> str:
        """
        Get the default configuration file path.
        
        Returns:
            Path to the default configuration file
        """
        if os.name == 'nt':  # Windows
            return os.path.expanduser(r"~\.gitmove\config.toml")
        else:  # Unix-like systems
            return os.path.expanduser("~/.config/gitmove/config.toml")
    
    def interpolate_env_vars(self, config: Dict) -> Dict:
        """
        Interpolate environment variables into configuration.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            Configuration with environment variables expanded
        """
        def _interpolate(value):
            if isinstance(value, str):
                # Replace ${ENV_VAR} or $ENV_VAR with environment variable
                return re.sub(
                    r'\$\{?(\w+)\}?', 
                    lambda m: os.environ.get(m.group(1), m.group(0)), 
                    value
                )
            elif isinstance(value, dict):
                return {k: _interpolate(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_interpolate(item) for item in value]
            return value
        
        return _interpolate(config)
    
    def validate_config(self, config: Optional[Dict] = None) -> Dict:
        """
        Validate configuration against predefined schema.
        
        Args:
            config: Configuration dictionary to validate
        
        Returns:
            Validated and normalized configuration
        """
        if config is None:
            config = self._load_config()
        
        # Interpolate environment variables
        config = self.interpolate_env_vars(config)
        
        errors = []
        warnings = []
        normalized_config = {}
        
        def _validate_section(schema: Dict, section_config: Dict, section_name: str):
            for key, rules in schema.items():
                value = section_config.get(key, rules.get('default'))
                
                # Check if required
                if rules.get('required', False) and value is None:
                    errors.append(f"Missing required configuration: {section_name}.{key}")
                    continue
                
                # Type checking
                if value is not None:
                    if not isinstance(value, rules['type']):
                        errors.append(f"Invalid type for {section_name}.{key}. "
                                      f"Expected {rules['type'].__name__}, got {type(value).__name__}")
                    
                    # Additional type-specific validations
                    if rules['type'] == str and 'pattern' in rules:
                        if not re.match(rules['pattern'], str(value)):
                            errors.append(f"Invalid format for {section_name}.{key}")
                    
                    if rules['type'] == int:
                        if 'min' in rules and value < rules['min']:
                            errors.append(f"{section_name}.{key} must be at least {rules['min']}")
                        if 'max' in rules and value > rules['max']:
                            errors.append(f"{section_name}.{key} must be at most {rules['max']}")
                    
                    if rules['type'] == list and 'item_type' in rules:
                        for item in value:
                            if not isinstance(item, rules['item_type']):
                                errors.append(f"Invalid item type in {section_name}.{key}")
                    
                    # Allowed values
                    if 'allowed' in rules and value not in rules['allowed']:
                        errors.append(f"Invalid value for {section_name}.{key}. "
                                      f"Allowed values: {rules['allowed']}")
                
                # Store normalized value
                normalized_config.setdefault(section_name, {})[key] = value or rules.get('default')
        
        # Validate each section
        for section, schema in self._CONFIG_SCHEMA.items():
            section_config = config.get(section, {})
            _validate_section(schema, section_config, section)
        
        # Check for unknown sections/keys
        for section in config:
            if section not in self._CONFIG_SCHEMA:
                warnings.append(f"Unknown configuration section: {section}")
        
        # Report results
        if errors or warnings:
            self._display_validation_results(errors, warnings)
        
        return normalized_config
    
    def _display_validation_results(self, errors: List[str], warnings: List[str]):
        """
        Display validation results using Rich for beautiful formatting.
        
        Args:
            errors: List of validation errors
            warnings: List of validation warnings
        """
        if errors:
            error_panel = Panel(
                Text("\n".join(errors), style="bold red"),
                title="Configuration Errors",
                border_style="red"
            )
            self.console.print(error_panel)
        
        if warnings:
            warning_panel = Panel(
                Text("\n".join(warnings), style="bold yellow"),
                title="Configuration Warnings",
                border_style="yellow"
            )
            self.console.print(warning_panel)
        
        if errors:
            raise ValueError("Invalid configuration detected")
    
    def _load_config(self) -> Dict:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                return toml.load(f)
        except FileNotFoundError:
            # Return empty dict if no config file
            return {}
        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML configuration: {e}")
    
    def generate_sample_config(self, output_path: Optional[str] = None) -> str:
        """
        Generate a sample configuration file.
        
        Args:
            output_path: Path to save the sample configuration
        
        Returns:
            Sample configuration as a string
        """
        sample_config = {
            section: {
                key: rules.get('default', None)
                for key, rules in schema.items()
            }
            for section, schema in self._CONFIG_SCHEMA.items()
        }
        
        config_str = toml.dumps(sample_config)
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(config_str)
        
        return config_str
    
    def recommend_configuration(self, current_config: Dict) -> Dict:
        """
        Provide configuration recommendations based on current settings.
        
        Args:
            current_config: Current configuration
        
        Returns:
            Dictionary of recommendations
        """
        recommendations = {}
        
        # Example recommendations
        if current_config.get('general', {}).get('verbose', False):
            recommendations['verbose_mode'] = (
                "Verbose mode is enabled. This may impact performance. "
                "Consider disabling in production."
            )
        
        if not current_config.get('sync', {}).get('auto_sync', False):
            recommendations['auto_sync'] = (
                "Auto sync is disabled. This may lead to outdated branches. "
                "Consider enabling auto_sync."
            )
        
        if current_config.get('clean', {}).get('age_threshold', 30) > 90:
            recommendations['branch_cleanup'] = (
                "Branch age threshold is quite high. Old branches may accumulate. "
                "Consider lowering the age_threshold."
            )
        
        return recommendations

# CLI Integration
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