"""
Advanced Environment Variable Configuration Support for GitMove

Provides comprehensive environment variable configuration management with:
- Dynamic configuration loading
- Type conversion
- Nested configuration support
- Validation and security features
"""

import os
import re
import json
import typing
from typing import Any, Dict, List, Optional, Union


class EnvConfigManager:
    """
    Gestionnaire de configuration par variables d'environnement pour GitMove.
    
    Utilise le ConfigValidator pour garantir la cohérence avec le reste du système.
    """
    
    # Prefix for GitMove-specific environment variables
    ENV_PREFIX = "GITMOVE_"
    
    @classmethod
    def load_config(
        cls, 
        base_config: Optional[Dict] = None, 
        prefix: Optional[str] = None
    ) -> Dict:
        """
        Load configuration from environment variables.
        
        Args:
            base_config: Base configuration to merge with environment variables
            prefix: Custom prefix for environment variables
        
        Returns:
            Merged configuration dictionary
        """
        # Use default prefix if not specified
        prefix = prefix or cls.ENV_PREFIX
        
        # Start with base configuration or empty dict
        config = base_config or {}
        
        # Collect all relevant environment variables
        env_vars = {
            key: value for key, value in os.environ.items() 
            if key.startswith(prefix)
        }
        
        # Process each environment variable
        for full_key, value in env_vars.items():
            # Remove prefix
            config_key = full_key[len(prefix):].lower()
            
            # Convert the value and merge into configuration
            config = cls._merge_config_value(config, config_key, value)
        
        return config
    
    @classmethod
    def _merge_config_value(cls, config: Dict, key: str, value: str) -> Dict:
        """
        Merge a configuration value into the existing configuration.
        
        Args:
            config: Existing configuration dictionary
            key: Configuration key (potentially nested)
            value: Configuration value
        
        Returns:
            Updated configuration dictionary
        """
        # Split nested keys
        parts = key.lower().split('_')
        
        # Traverse or create nested structure
        current = config
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        
        # Convert and set the final value
        converted_value = cls._convert_value(value)
        current[parts[-1]] = converted_value
        
        return config
    
    @classmethod
    def _convert_value(cls, value: str) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value: Environment variable value
        
        Returns:
            Converted value
        """
        # Trim whitespace
        value = value.strip()
        
        # Try JSON parsing first (for complex types)
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Boolean conversions
        lower_value = value.lower()
        if lower_value in ['true', '1', 'yes', 'on']:
            return True
        if lower_value in ['false', '0', 'no', 'off']:
            return False
        
        # Numeric conversions
        try:
            # Try integer first
            return int(value)
        except ValueError:
            try:
                # Then try float
                return float(value)
            except ValueError:
                pass
        
        # Return as string if no conversion
        return value
    
    @classmethod
    def generate_env_template(
        cls, 
        config_schema: Optional[Dict] = None, 
        include_descriptions: bool = True
    ) -> str:
        """
        Generate a template of environment variables based on a configuration schema.
        
        Args:
            config_schema: Configuration schema to generate template from
            include_descriptions: Include descriptions for each variable
        
        Returns:
            String containing environment variable template
        """
        # Default schema if not provided
        if config_schema is None:
            config_schema = {
                'general': {
                    'main_branch': {
                        'type': 'string',
                        'description': 'Default main branch name',
                        'example': 'main'
                    },
                    'verbose': {
                        'type': 'boolean',
                        'description': 'Enable verbose logging',
                        'example': 'false'
                    }
                },
                'sync': {
                    'default_strategy': {
                        'type': 'string',
                        'description': 'Default sync strategy',
                        'example': 'rebase'
                    },
                    'auto_sync': {
                        'type': 'boolean',
                        'description': 'Enable automatic synchronization',
                        'example': 'true'
                    }
                }
            }
        
        # Generate environment variable template
        env_template = ["# GitMove Configuration Environment Variables", ""]
        
        def _process_config_section(section_name: str, section_config: Dict):
            """Process a configuration section."""
            for key, details in section_config.items():
                # Construct full environment variable name
                env_var = f"{cls.ENV_PREFIX}{section_name.upper()}_{key.upper()}"
                
                # Add description if requested
                if include_descriptions and isinstance(details, dict):
                    if details.get('description'):
                        env_template.append(f"# {details['description']}")
                    
                    # Add example if available
                    if details.get('example'):
                        env_template.append(f"# Example: {details['example']}")
                
                # Add environment variable placeholder
                env_template.append(f"{env_var}=")
                env_template.append("")
        
        # Process each section in the schema
        for section_name, section_config in config_schema.items():
            env_template.append(f"# {section_name.capitalize()} Configuration")
            _process_config_section(section_name, section_config)
        
        return "\n".join(env_template)
    
    @classmethod
    def validate_env_config(
        cls, 
        config: Dict, 
        schema: Optional[Dict] = None
    ) -> Dict[str, List[str]]:
        """
        Validate environment-loaded configuration against a schema.
        
        Args:
            config: Configuration dictionary to validate
            schema: Validation schema
        
        Returns:
            Dictionary of validation errors
        """
        # Default validation schema
        if schema is None:
            schema = {
                'general': {
                    'main_branch': {
                        'type': str,
                        'pattern': r'^[a-zA-Z0-9_\-./]+$'
                    },
                    'verbose': {
                        'type': bool
                    }
                },
                'sync': {
                    'default_strategy': {
                        'type': str,
                        'allowed': ['merge', 'rebase', 'auto']
                    },
                    'auto_sync': {
                        'type': bool
                    }
                }
            }
        
        errors = {}
        
        def _validate_section(section_name: str, section_config: Dict, section_schema: Dict):
            """Validate a specific configuration section."""
            section_errors = []
            
            for key, rules in section_schema.items():
                value = section_config.get(key)
                
                # Skip if value not present
                if value is None:
                    continue
                
                # Type checking
                if 'type' in rules and not isinstance(value, rules['type']):
                    section_errors.append(
                        f"Invalid type for {section_name}.{key}. "
                        f"Expected {rules['type'].__name__}, got {type(value).__name__}"
                    )
                
                # Pattern validation for strings
                if (rules.get('type') == str and 
                    'pattern' in rules and 
                    not re.match(rules['pattern'], str(value))):
                    section_errors.append(
                        f"Invalid format for {section_name}.{key}. "
                        f"Must match pattern: {rules['pattern']}"
                    )
                
                # Allowed values
                if 'allowed' in rules and value not in rules['allowed']:
                    section_errors.append(
                        f"Invalid value for {section_name}.{key}. "
                        f"Allowed values: {rules['allowed']}"
                    )
            
            return section_errors
        
        # Validate each section
        for section_name, section_schema in schema.items():
            section_config = config.get(section_name, {})
            section_errors = _validate_section(section_name, section_config, section_schema)
            
            if section_errors:
                errors[section_name] = section_errors
        
        return errors

# Optional configuration loader
@staticmethod
def load_env_config(base_config: Optional[Dict] = None) -> Dict:
    """
    Charge la configuration depuis les variables d'environnement.
    
    Args:
        base_config: Configuration de base à enrichir
        
    Returns:
        Configuration enrichie
    """
    # Import ici pour éviter les importations circulaires
    from gitmove.validators.config_validator import ConfigValidator
    
    # Obtenir un validateur pour accéder au schéma
    validator = ConfigValidator()
    
    # Charger depuis les variables d'environnement
    env_config = EnvConfigManager.load_config(base_config=base_config)
    
    # Valider et normaliser la configuration
    try:
        normalized_config = validator.validate_config(env_config)
        return normalized_config
    except ValueError:
        # En cas d'erreur de validation, on retourne la configuration de base
        # ou une configuration vide si aucune n'a été fournie
        return base_config or {}
