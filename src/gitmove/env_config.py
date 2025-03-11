"""
Enhanced Environment Variable Configuration Loader for GitMove

Provides advanced environment variable configuration management with:
- Hierarchical configuration
- Type conversion
- Nested configuration support
- Secure credential handling
- Validation and templating
"""

import os
import sys
import json
import base64
import hashlib
import re
from typing import Dict, Any, Optional, Union, List

import yaml
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class EnvConfigManager:
    """
    Advanced environment variable configuration manager.
    
    Supports complex configuration loading, type conversion, 
    and secure credential management.
    """
    
    # Prefix for GitMove-specific environment variables
    ENV_PREFIX = "GITMOVE_"
    
    # Configuration for type conversion and validation
    TYPE_MAPPING = {
        'str': str,
        'int': int,
        'float': float,
        'bool': lambda x: x.lower() in ['true', '1', 'yes', 'on'],
        'list': lambda x: json.loads(x) if x.startswith('[') else x.split(','),
        'dict': json.loads,
        'json': json.loads
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize EnvConfigManager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.console = Console()
        self.config_path = config_path or self._get_default_config_path()
        self.secrets_manager = SecretsManager()
    
    @classmethod
    def _get_default_config_path(cls) -> str:
        """
        Get the default configuration file path.
        
        Returns:
            Path to the default environment configuration file
        """
        if os.name == 'nt':  # Windows
            return os.path.expanduser(r"~\.gitmove\env_config.yaml")
        else:  # Unix-like systems
            return os.path.expanduser("~/.config/gitmove/env_config.yaml")
    
    def load_env_config(self) -> Dict[str, Any]:
        """
        Load environment configuration from multiple sources.
        
        Returns:
            Merged configuration dictionary
        """
        # Sources (in order of precedence)
        config_sources = [
            self._load_config_file(),  # Lowest priority
            self._load_environment_vars(),  # Higher priority
            self._load_secrets()  # Highest priority
        ]
        
        # Merge configurations
        merged_config = {}
        for source in config_sources:
            merged_config.update(source)
        
        return merged_config
    
    def _load_config_file(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary from file
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return self._process_config(yaml.safe_load(f) or {})
        except (yaml.YAMLError, IOError) as e:
            self.console.print(f"[yellow]Warning: Could not load config file: {e}[/yellow]")
        
        return {}
    
    def _load_environment_vars(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Returns:
            Configuration dictionary from environment variables
        """
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                # Remove prefix and convert to nested dict
                config_key = key[len(self.ENV_PREFIX):].lower()
                env_config = self._merge_nested_config(
                    env_config, 
                    self._parse_env_var(config_key, value)
                )
        
        return env_config
    
    def _load_secrets(self) -> Dict[str, Any]:
        """
        Load sensitive configuration from secure storage.
        
        Returns:
            Secrets dictionary
        """
        return self.secrets_manager.get_all_secrets()
    
    def _parse_env_var(self, key: str, value: str) -> Dict[str, Any]:
        """
        Parse and convert an environment variable.
        
        Args:
            key: Configuration key
            value: Configuration value
        
        Returns:
            Parsed configuration dictionary
        """
        # Split nested keys
        parts = key.split('_')
        
        # Determine type (optional type prefix)
        type_match = re.match(r'^(str|int|float|bool|list|dict|json)_(.+)', parts[0])
        if type_match:
            var_type, first_part = type_match.groups()
            parts[0] = first_part
            
            # Convert value
            try:
                converted_value = self.TYPE_MAPPING[var_type](value)
            except (ValueError, json.JSONDecodeError):
                self.console.print(f"[yellow]Warning: Could not convert {key} to {var_type}[/yellow]")
                converted_value = value
        else:
            # Default to string
            converted_value = value
        
        # Build nested dictionary
        config = converted_value
        for part in reversed(parts[:-1]):
            config = {part: config}
        
        return config
    
    def _merge_nested_config(self, base: Dict, update: Dict) -> Dict:
        """
        Recursively merge nested configurations.
        
        Args:
            base: Base configuration dictionary
            update: Configuration to merge
        
        Returns:
            Merged configuration dictionary
        """
        for key, value in update.items():
            if isinstance(value, dict):
                base[key] = self._merge_nested_config(base.get(key, {}), value)
            else:
                base[key] = value
        return base
    
    def _process_config(self, config: Dict) -> Dict:
        """
        Process and validate loaded configuration.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            Processed configuration dictionary
        """
        # Placeholder for more advanced configuration processing
        # Could include validation, type conversion, etc.
        return config
    
    def validate_config(self, config: Dict) -> List[str]:
        """
        Validate configuration against predefined rules.
        
        Args:
            config: Configuration to validate
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Example validation rules (can be expanded)
        if 'sync' in config:
            if config['sync'].get('strategy') not in ['merge', 'rebase', 'auto']:
                errors.append("Invalid sync strategy")
        
        if 'clean' in config:
            age_threshold = config['clean'].get('age_threshold', 0)
            if not isinstance(age_threshold, int) or age_threshold < 0:
                errors.append("Invalid branch age threshold")
        
        return errors

class SecretsManager:
    """
    Secure secrets management for GitMove.
    
    Provides encrypted storage and retrieval of sensitive configuration.
    """
    
    def __init__(self, secrets_path: Optional[str] = None):
        """
        Initialize SecretsManager.
        
        Args:
            secrets_path: Optional path to secrets file
        """
        self.console = Console()
        self.secrets_path = secrets_path or self._get_default_secrets_path()
    
    @classmethod
    def _get_default_secrets_path(cls) -> str:
        """
        Get the default secrets storage path.
        
        Returns:
            Path to the default secrets file
        """
        if os.name == 'nt':  # Windows
            return os.path.expanduser(r"~\.gitmove\secrets.enc")
        else:  # Unix-like systems
            return os.path.expanduser("~/.config/gitmove/secrets.enc")
    
    def set_secret(self, key: str, value: str):
        """
        Securely store a secret.
        
        Args:
            key: Secret key
            value: Secret value
        """
        # Get encryption key from environment or generate
        encryption_key = self._get_encryption_key()
        
        # Encrypt the secret
        encrypted_value = self._encrypt(value, encryption_key)
        
        # Load existing secrets
        secrets = self._load_secrets()
        secrets[key] = encrypted_value
        
        # Save updated secrets
        self._save_secrets(secrets)
        
        self.console.print(f"[green]Secret '{key}' stored securely[/green]")
    
    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieve a secret.
        
        Args:
            key: Secret key to retrieve
        
        Returns:
            Decrypted secret value or None
        """
        secrets = self._load_secrets()
        
        if key not in secrets:
            return None
        
        # Get encryption key
        encryption_key = self._get_encryption_key()
        
        # Decrypt and return
        try:
            return self._decrypt(secrets[key], encryption_key)
        except Exception:
            self.console.print(f"[red]Could not decrypt secret '{key}'[/red]")
            return None
    
    def _get_encryption_key(self) -> bytes:
        """
        Get or generate an encryption key.
        
        Returns:
            Encryption key
        """
        # Priority: 
        # 1. Explicit environment variable
        # 2. Derived from system/user identifier
        key_env = os.environ.get('GITMOVE_ENCRYPTION_KEY')
        if key_env:
            return hashlib.sha256(key_env.encode()).digest()
        
        # Derive key from system/user identifier
        identifier = f"{os.getuid()}:{os.getlogin()}"
        return hashlib.sha256(identifier.encode()).digest()
    
    def _encrypt(self, value: str, key: bytes) -> str:
        """
        Encrypt a value.
        
        Args:
            value: Value to encrypt
            key: Encryption key
        
        Returns:
            Base64 encoded encrypted value
        """
        from cryptography.fernet import Fernet
        
        # Use Fernet symmetric encryption
        f = Fernet(base64.urlsafe_b64encode(key))
        encrypted = f.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt(self, encrypted_value: str, key: bytes) -> str:
        """
        Decrypt a value.
        
        Args:
            encrypted_value: Base64 encoded encrypted value
            key: Encryption key
        
        Returns:
            Decrypted value
        """
        from cryptography.fernet import Fernet
        
        f = Fernet(base64.urlsafe_b64encode(key))
        decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_value))
        return decrypted.decode()
    
    def _load_secrets(self) -> Dict[str, str]:
        """
        Load encrypted secrets from file.
        
        Returns:
            Dictionary of encrypted secrets
        """
        try:
            if os.path.exists(self.secrets_path):
                with open(self.secrets_path, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        
        return {}
    
    def _save_secrets(self, secrets: Dict[str, str]):
        """
        Save encrypted secrets to file.
        
        Args:
            secrets: Dictionary of encrypted secrets
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.secrets_path), exist_ok=True)
        
        with open(self.secrets_path, 'w') as f:
            json.dump(secrets, f)

def register_env_commands(cli):
    """
    Register environment-related commands to GitMove CLI.
    
    Args:
        cli: Click CLI object
    """
    @cli.group()
    def env():
        """Environment configuration management commands."""
        pass
    
    @env.command('list')
    def list_env_vars():
        """List all GitMove-related environment variables."""
        console = Console()
        
        # Create a table to display environment variables
        table = Table(title="GitMove Environment Variables")
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="magenta")
        
        # Find and display GitMove-specific environment variables
        for key, value in os.environ.items():
            if key.startswith(EnvConfigManager.ENV_PREFIX):
                # Mask sensitive values
                masked_value = value[:3] + '*' * (len(value) - 6) + value[-3:] if len(value) > 6 else '*' * len(value)
                table.add_row(key, masked_value)
        
        console.print(table)
    
    @env.command('set')
    @click.argument('key')
    @click.argument('value')
    @click.option('--type', type=click.Choice(['str', 'int', 'float', 'bool', 'list', 'dict']), default='str')
    @click.option('--secret', is_flag=True, help='Store as a secure secret')
    def set_env_var(key, value, type, secret):
        """Set an environment variable or secret."""
        console = Console()
        
        # Prepare full key name
        full_key = f"{EnvConfigManager.ENV_PREFIX}{type}_{key}".upper()
        
        if secret:
            # Use SecretsManager for sensitive data
            secrets_manager = SecretsManager()
            secrets_manager.set_secret(full_key, value)
        else:
            # Set as environment variable
            os.environ[full_key] = value
            console.print(f"[green]Environment variable {full_key} set[/green]")
    
    @env.command('get')
    @click.argument('key')
    def get_env_var(key):
        """Retrieve an environment variable or secret."""
        console = Console()
        
        # Try as environment variable first
        full_key = f"{EnvConfigManager.ENV_PREFIX}{key}".upper()
        
        # Check environment variables
        env_value = os.environ.get(full_key)
        if env_value:
            console.print(f"[blue]Environment Variable:[/blue] {env_value}")
            return
        
        # Try as secret
        secrets_manager = SecretsManager()
        secret_value = secrets_manager.get_secret(full_key)
        
        if secret_value:
            console.print(f"[green]Secret retrieved successfully[/green]")
        else:
            console.print(f"[red]No value found for {key}[/red]")
    
    @env.command('validate')
    @click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
    def validate_env_config(config):
        """Validate environment configuration."""
        console = Console()
        config_manager = EnvConfigManager(config)
        
        try:
            # Load and validate configuration
            env_config = config_manager.load_env_config()
            errors = config_manager.validate_config(env_config)
            
            if errors:
                console.print(Panel(
                    "\n".join(errors),
                    title="Configuration Validation Errors",
                    border_style="red"
                ))
                sys.exit(1)
            else:
                console.print(Panel(
                    "Environment configuration is valid.",
                    title="Validation Result",
                    border_style="green"
                ))
        
        except Exception as e:
            console.print(f"[red]Error validating configuration: {e}[/red]")
            sys.exit(1)
    
    @env.command('template')
    @click.option('--output', '-o', type=click.Path(), help='Output path for environment configuration template')
    def generate_env_template(output):
        """Generate an environment configuration template."""
        console = Console()
        
        # Generate a comprehensive environment configuration template
        template = {
            "general": {
                "main_branch": "main",
                "verbose": False
            },
            "clean": {
                "auto_clean": False,
                "exclude_branches": ["develop", "staging"],
                "age_threshold": 30
            },
            "sync": {
                "default_strategy": "rebase",
                "auto_sync": True
            },
            "advice": {
                "rebase_threshold": 5,
                "force_merge_patterns": ["feature/*"],
                "force_rebase_patterns": ["fix/*"]
            }
        }
        
        # Generate environment variable examples
        env_var_examples = []
        for section, settings in template.items():
            for key, value in settings.items():
                # Generate example environment variable names
                var_types = ['str', 'int', 'bool', 'list']
                for var_type in var_types:
                    env_var = f"{EnvConfigManager.ENV_PREFIX}{var_type.upper()}_{section.upper()}_{key.upper()}"
                    example_value = (
                        f"Example: {env_var}={json.dumps(value) if isinstance(value, (list, dict)) else str(value)}"
                    )
                    env_var_examples.append(example_value)
        
        # Prepare output
        template_content = {
            "environment_variables": env_var_examples,
            "yaml_configuration": template
        }
        
        # Write to file or print to console
        if output:
            with open(output, 'w') as f:
                yaml.dump(template_content, f, default_flow_style=False)
            console.print(f"[green]Environment configuration template saved to {output}[/green]")
        else:
            console.print(Panel(
                yaml.dump(template_content, default_flow_style=False),
                title="Environment Configuration Template",
                border_style="blue"
            ))

# Utility function for global configuration
def configure_from_environment():
    """
    Apply global configuration from environment variables.
    
    This function can be called during GitMove initialization
    to set up global settings based on environment configuration.
    """
    config_manager = EnvConfigManager()
    
    try:
        # Load configuration from environment
        env_config = config_manager.load_env_config()
        
        # Apply global settings
        if 'general' in env_config:
            # Set verbose mode
            if env_config['general'].get('verbose', False):
                import logging
                logging.basicConfig(level=logging.DEBUG)
            
            # Other global settings can be added here
        
        return env_config
    
    except Exception as e:
        print(f"Error configuring from environment: {e}")
        return {}

# Optional: Environment variable migration helper
def migrate_legacy_env_vars():
    """
    Migrate legacy environment variable formats to new GitMove standard.
    
    Helps users transition between different environment variable naming conventions.
    """
    console = Console()
    migrations = {}
    
    # Example migration rules
    legacy_mappings = {
        'GITMOVE_MAIN_BRANCH': f'{EnvConfigManager.ENV_PREFIX}STR_GENERAL_MAIN_BRANCH',
        'GITMOVE_VERBOSE': f'{EnvConfigManager.ENV_PREFIX}BOOL_GENERAL_VERBOSE'
    }
    
    for old_key, new_key in legacy_mappings.items():
        if old_key in os.environ:
            # Migrate value
            os.environ[new_key] = os.environ[old_key]
            del os.environ[old_key]
            migrations[old_key] = new_key
    
    if migrations:
        console.print("[yellow]Environment Variable Migration:[/yellow]")
        for old, new in migrations.items():
            console.print(f"  {old} -> {new}")
    
    return migrations

# Dependencies suggestion
def suggest_dependencies():
    """
    Suggest additional dependencies for enhanced environment configuration.
    
    Returns:
        List of recommended packages
    """
    return [
        "python-dotenv",  # For .env file support
        "cryptography",   # For advanced encryption
        "pyyaml",         # For YAML configuration support
    ]

# Main entry point for environment configuration management
def init_env_config():
    """
    Initialize environment configuration for GitMove.
    
    Performs initial setup, migration, and configuration loading.
    """
    # Migrate legacy environment variables
    migrate_legacy_env_vars()
    
    # Load and apply configuration
    return configure_from_environment()

# Optional CLI command to check dependencies
def check_env_dependencies(cli):
    """
    Add a command to check and suggest additional dependencies.
    
    Args:
        cli: Click CLI object
    """
    @cli.command('check-env-deps')
    def check_dependencies():
        """Check and suggest environment configuration dependencies."""
        console = Console()
        recommended_deps = suggest_dependencies()
        
        table = Table(title="Recommended Environment Configuration Dependencies")
        table.add_column("Package", style="cyan")
        table.add_column("Status", style="green")
        
        for dep in recommended_deps:
            try:
                __import__(dep.split('==')[0])
                status = "✅ Installed"
            except ImportError:
                status = "❌ Not Installed"
            
            table.add_row(dep, status)
        
        console.print(table)
        console.print("\n[blue]Tip:[/blue] Install with 'pip install " + " ".join(recommended_deps) + "'")

# Update the main CLI initialization
def register_environment_commands(cli):
    """
    Register all environment-related commands to the main CLI.
    
    Args:
        cli: Click CLI object
    """
    register_env_commands(cli)
    check_env_dependencies(cli)