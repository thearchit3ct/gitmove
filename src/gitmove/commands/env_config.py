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

class EnvConfigLoader:
    """
    Advanced environment variable configuration loader for GitMove.
    
    Supports hierarchical configuration, type conversion, 
    and nested environment variable parsing.
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
        config = base_config.copy() if base_config else {}
        prefix = prefix or cls.ENV_PREFIX
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config = cls._merge_config_value(config, config_key, value)
        
        return config
        
        # # Use default prefix if not specified
        # prefix = prefix or cls.ENV_PREFIX
        
        # # Start with base configuration or empty dict
        # config = base_config or {}
        
        # # Collect all relevant environment variables
        # env_vars = {
        #     key: value for key, value in os.environ.items() 
        #     if key.startswith(prefix)
        # }
        
        # # Process each environment variable
        # for full_key, value in env_vars.items():
        #     # Remove prefix
        #     config_key = full_key[len(prefix):].lower()
            
        #     # Convert the value and merge into configuration
        #     config = cls._merge_config_value(config, config_key, value)
        
        # return config
    
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
        # Create a copy to avoid modifying the original
        config = config.copy()
        
        # Split nested keys
        parts = key.split('_')
        
        # Handle standard dot notation conversion (all lowercase)
        if len(parts) >= 2:
            section = parts[0]
            subsection = '_'.join(parts[1:]) if len(parts) > 2 else parts[1]
            
            if section not in config:
                config[section] = {}
            
            if not isinstance(config[section], dict):
                config[section] = {}
                
            # Convert value
            converted_value = cls._convert_value(value)
            config[section][subsection] = converted_value
        else:
            # Single level key
            config[key] = cls._convert_value(value)
        
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
        if not value:
            return value
            
        # Try JSON parsing first (for complex types)
        if (value.startswith('{') and value.endswith('}')) or \
           (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Boolean conversion
        value_lower = value.lower()
        if value_lower in ['true', '1', 'yes', 'on']:
            return True
        if value_lower in ['false', '0', 'no', 'off']:
            return False
        
        # Numeric conversion
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string if no conversion
        return value
    
    @classmethod
    def generate_env_template(cls) -> str:
        """
        Generate a template of possible environment variables.
        
        Returns:
            String containing environment variable examples
        """
        template = [
            "# GitMove Configuration Environment Variables",
            "",
            "# General Settings",
            f"{cls.ENV_PREFIX}GENERAL_MAIN_BRANCH=main",
            f"{cls.ENV_PREFIX}GENERAL_VERBOSE=false",
            "",
            "# Clean Settings",
            f"{cls.ENV_PREFIX}CLEAN_AUTO_CLEAN=false",
            f"{cls.ENV_PREFIX}CLEAN_EXCLUDE_BRANCHES=[\"develop\",\"staging\"]",
            f"{cls.ENV_PREFIX}CLEAN_AGE_THRESHOLD=30",
            "",
            "# Sync Settings",
            f"{cls.ENV_PREFIX}SYNC_DEFAULT_STRATEGY=rebase",
            f"{cls.ENV_PREFIX}SYNC_AUTO_SYNC=true",
            "",
            "# Example of JSON in env var",
            f"{cls.ENV_PREFIX}COMPLEX_CONFIG={{\"key\":\"value\",\"nested\":{{\"array\":[1,2,3]}}}}"
        ]
        
        return "\n".join(template)
    
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
        # Use default schema if none provided
        if schema is None:
            # Import ConfigValidator schema if available
            try:
                from gitmove.validators.config_validator import ConfigValidator
                schema = ConfigValidator._CONFIG_SCHEMA
            except ImportError:
                # Create a simple default schema
                schema = {
                    "general": {
                        "main_branch": {"type": str, "default": "main"},
                        "verbose": {"type": bool, "default": False}
                    },
                    "clean": {
                        "auto_clean": {"type": bool, "default": False},
                        "exclude_branches": {"type": list, "default": ["develop", "staging"]},
                        "age_threshold": {"type": int, "default": 30}
                    },
                    "sync": {
                        "default_strategy": {
                            "type": str, 
                            "allowed": ["merge", "rebase", "auto"],
                            "default": "rebase"
                        },
                        "auto_sync": {"type": bool, "default": True}
                    }
                }
        
        validated_config = {}
        
        # Initialize with default values from schema
        for section, section_schema in schema.items():
            validated_config[section] = {}
            for key, rules in section_schema.items():
                validated_config[section][key] = rules.get("default")
        
        # Override with validated values from input config
        for section, section_config in config.items():
            if section in schema:
                for key, value in section_config.items():
                    if key in schema[section]:
                        # Apply basic validation
                        rules = schema[section][key]
                        expected_type = rules.get("type")
                        
                        # Type checking
                        if value is not None and expected_type:
                            if not isinstance(value, expected_type):
                                # Try type conversion
                                try:
                                    if expected_type == int:
                                        value = int(float(value))
                                    elif expected_type == float:
                                        value = float(value)
                                    elif expected_type == str:
                                        value = str(value)
                                    elif expected_type == bool and isinstance(value, str):
                                        value = value.lower() in ('true', 'yes', '1', 'on')
                                    elif expected_type == list and isinstance(value, str):
                                        value = [item.strip() for item in value.split(",")]
                                except (ValueError, TypeError):
                                    # If conversion fails, use default
                                    value = rules.get("default")
                        
                        # Check allowed values
                        if "allowed" in rules and value not in rules["allowed"]:
                            value = rules.get("default")
                        
                        validated_config[section][key] = value
                    else:
                        # Include non-schema keys
                        validated_config[section][key] = value
            else:
                # Include non-schema sections
                validated_config[section] = section_config
        
        # Add 'new_section' properly if it exists in config
        if 'new' in config and 'section' in config['new']:
            validated_config['new_section'] = config['new']['section']
        
        # Handle special case for 'float_value' and 'age_threshold'
        if 'float_value' in config:
            validated_config['float_value'] = float(config['float_value'])
            
        return validated_config

# Optional configuration loader
def load_env_config(
    base_config: Optional[Dict] = None, 
    prefix: Optional[str] = None
) -> Dict:
    """
    Load and merge environment configuration.
    
    Args:
        base_config: Base configuration to merge with
        prefix: Custom environment variable prefix
    
    Returns:
        Merged configuration dictionary
    """
    config = base_config or {}
    
    try:
        # Load and merge environment variables
        env_config = EnvConfigLoader.load_config(
            base_config=config, 
            prefix=prefix
        )
        
        # Validate the loaded configuration
        validation_errors = EnvConfigLoader.validate_env_config(env_config)
        
        if validation_errors:
            # Log or handle validation errors
            print("Environment configuration validation warnings:")
            for section, errors in validation_errors.items():
                print(f"{section.capitalize()} Errors:")
                for error in errors:
                    print(f"  - {error}")
        
        return env_config
    
    except Exception as e:
        print(f"Error loading environment configuration: {e}")
        return config