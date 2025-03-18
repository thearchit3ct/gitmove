"""
Standardized Configuration Validation for GitMove

Provides comprehensive configuration validation with detailed error reporting,
environment variable support, and extended schema validation.

"""

import os
import re
import sys
from typing import Any, Dict, List, Optional, Union, Set, Tuple
import toml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

class ConfigValidator:
    """
    Standardized configuration validator for GitMove.
    
    Provides a unified approach to configuration validation with:
    - Detailed error reporting
    - Environment variable interpolation
    - Comprehensive schema-based validation
    - Configuration recommendations
    - Sensible defaults
    """
    
    # Configuration schema defining validation rules for all sections

    _CONFIG_SCHEMA = {
        "general": {
            "main_branch": {
                "type": str,
                "required": True,
                "pattern": r'^[a-zA-Z0-9_\-./]+$',
                "default": "main",
                "description": "Main branch of the repository"
            },
            "verbose": {
                "type": bool,
                "default": False,
                "description": "Enable verbose logging"

            }
        },
        "clean": {
            "auto_clean": {
                "type": bool,
                "default": False,
                "description": "Automatically clean merged branches"
            },
            "exclude_branches": {
                "type": list,
                "item_type": str,
                "default": ["develop", "staging"],
                "description": "Branches to exclude from cleanup operations"
            },
            "age_threshold": {
                "type": int,
                "min": 1,
                "max": 365,
                "default": 30,
                "description": "Minimum age in days for branches to be eligible for cleanup"
            }
        },
        "sync": {
            "default_strategy": {
                "type": str,
                "allowed": ["merge", "rebase", "auto"],
                "default": "rebase",
                "description": "Default synchronization strategy"
            },
            "auto_sync": {
                "type": bool,
                "default": True,
                "description": "Enable automatic synchronization"
            },
            "sync_frequency": {
                "type": str,
                "allowed": ["hourly", "daily", "weekly", "manual"],
                "default": "daily",
                "description": "Frequency of automatic synchronization"
            }
        },
        "advice": {
            "rebase_threshold": {
                "type": int,
                "min": 1,
                "max": 50,
                "default": 5,
                "description": "Maximum number of commits for recommending rebase"
            },
            "consider_branch_age": {
                "type": bool,
                "default": True,
                "description": "Consider branch age when providing strategy advice"
            },
            "force_merge_patterns": {
                "type": list,
                "item_type": str,
                "default": ["feature/*", "release/*"],
                "description": "Branch patterns that should always use merge"
            },
            "force_rebase_patterns": {
                "type": list,
                "item_type": str,
                "default": ["fix/*", "chore/*"],
                "description": "Branch patterns that should always use rebase"
            }
        },
        "conflict_detection": {
            "pre_check_enabled": {
                "type": bool,
                "default": True,
                "description": "Enable conflict detection before operations"
            },
            "show_diff": {
                "type": bool,
                "default": True,
                "description": "Show diff details for potential conflicts"
            },
            "allowed_conflict_threshold": {
                "type": int,
                "min": 0,
                "max": 100,
                "default": 3,
                "description": "Maximum number of allowed conflicts before warning"
            }
        },
        "security": {
            "protected_branches": {
                "type": list,
                "item_type": str,
                "default": ["main", "master", "develop", "release/*"],
                "description": "Branches protected from destructive operations"
            },
            "require_validation": {
                "type": bool,
                "default": True,
                "description": "Require validation before critical operations"
            }
        },
        "plugins": {
            "enabled": {
                "type": bool,
                "default": True,
                "description": "Enable plugin system"
            },
            "plugin_dir": {
                "type": str,
                "default": "~/.gitmove/plugins",
                "description": "Directory containing plugins"
            },
            "allowed_plugins": {
                "type": list,
                "item_type": str,
                "default": [],
                "description": "List of allowed plugins (empty = all allowed)"
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
            """Validate a specific configuration section."""
            section_data = {}
            for key, rules in schema.items():
                value = section_config.get(key, rules.get('default'))
                
                # Check if required
                if rules.get('required', False) and value is None:
                    errors.append(f"Missing required configuration: {section_name}.{key}")
                    continue
                
                # Type checking
                if value is not None:
                    # Check main type
                    if not isinstance(value, rules['type']):
                        errors.append(f"Invalid type for {section_name}.{key}. "
                                      f"Expected {rules['type'].__name__}, got {type(value).__name__}")
                    
                    # Additional type-specific validations
                    if rules['type'] == str and 'pattern' in rules:
                        if not re.match(rules['pattern'], str(value)):
                            errors.append(f"Invalid format for {section_name}.{key}. "
                                          f"Must match pattern: {rules['pattern']}")
                    
                    if rules['type'] == int:
                        if 'min' in rules and value < rules['min']:
                            errors.append(f"{section_name}.{key} must be at least {rules['min']}")
                        if 'max' in rules and value > rules['max']:
                            errors.append(f"{section_name}.{key} must be at most {rules['max']}")
                    
                    if rules['type'] == list:
                        if 'item_type' in rules:
                            for idx, item in enumerate(value):
                                if not isinstance(item, rules['item_type']):
                                    errors.append(f"Invalid item type at position {idx} in {section_name}.{key}. "
                                                 f"Expected {rules['item_type'].__name__}, got {type(item).__name__}")
                    
                    # Allowed values
                    if 'allowed' in rules and value not in rules['allowed']:
                        errors.append(f"Invalid value for {section_name}.{key}. "
                                      f"Allowed values: {', '.join(rules['allowed'])}")
                
                # Store normalized value
                section_data[key] = value if value is not None else rules.get('default')
            
            # Add validated section to normalized config
            normalized_config[section_name] = section_data

        
        # Validate each section
        for section, schema in self._CONFIG_SCHEMA.items():
            section_config = config.get(section, {})
            _validate_section(schema, section_config, section)
        
        # Check for unknown sections or keys
        for section, content in config.items():
            if section not in self._CONFIG_SCHEMA:
                warnings.append(f"Unknown configuration section: {section}")
                continue
                
            if isinstance(content, dict):
                for key in content:
                    if key not in self._CONFIG_SCHEMA[section]:
                        warnings.append(f"Unknown configuration key: {section}.{key}")
        
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
        Generate a sample configuration file with descriptions.
        
        Args:
            output_path: Path to save the sample configuration
        
        Returns:
            Sample configuration as a string
        """
        sample_config_lines = []
        
        for section, schema in self._CONFIG_SCHEMA.items():
            sample_config_lines.append(f"# {section.capitalize()} Settings")
            sample_config_lines.append(f"[{section}]")
            
            for key, rules in schema.items():
                # Add description as comment if available
                if 'description' in rules:
                    sample_config_lines.append(f"# {rules['description']}")
                
                # Format the default value according to its type
                default = rules.get('default')
                
                if rules['type'] == str:
                    default_str = f'"{default}"' if default is not None else '""'
                elif rules['type'] == list:
                    if default:
                        default_str = str(default).replace("'", '"')
                    else:
                        default_str = "[]"
                else:
                    default_str = str(default).lower() if isinstance(default, bool) else str(default)
                
                sample_config_lines.append(f"{key} = {default_str}")
                
                # Add allowed values as comment if available
                if 'allowed' in rules:
                    allowed_str = ', '.join([f'"{v}"' if rules['type'] == str else str(v) for v in rules['allowed']])
                    sample_config_lines.append(f"# Allowed values: {allowed_str}")
                
                # Add range as comment if available
                if rules['type'] == int and 'min' in rules and 'max' in rules:
                    sample_config_lines.append(f"# Range: {rules['min']} to {rules['max']}")
                
                sample_config_lines.append("")
            
            sample_config_lines.append("")
        
        # Convert to string
        config_str = "\n".join(sample_config_lines)
        
        # Write to file if output path is provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(config_str)
        
        return config_str
    
    def recommend_configuration(self, current_config: Dict) -> Dict[str, str]:
        """
        Provide configuration recommendations based on current settings.
        
        Args:
            current_config: Current configuration
        
        Returns:
            Dictionary of recommendations
        """
        recommendations = {}
        
        # General recommendations
        if current_config.get('general', {}).get('verbose', False):
            recommendations['verbose_mode'] = (
                "Verbose mode is enabled. This may impact performance. "
                "Consider disabling in production environments."
            )
        
        # Clean recommendations
        age_threshold = current_config.get('clean', {}).get('age_threshold', 30)
        if age_threshold > 90:
            recommendations['branch_cleanup'] = (
                f"Branch age threshold is quite high ({age_threshold} days). "
                "Old branches may accumulate. Consider lowering the age_threshold."
            )
        elif age_threshold < 7:
            recommendations['branch_cleanup_short'] = (
                f"Branch age threshold is very short ({age_threshold} days). "
                "This may lead to premature branch cleanup."
            )
        
        # Sync recommendations
        if not current_config.get('sync', {}).get('auto_sync', True):
            recommendations['auto_sync'] = (
                "Auto sync is disabled. This may lead to outdated branches. "
                "Consider enabling auto_sync for better branch management."
            )
        
        # Conflict detection recommendations
        if not current_config.get('conflict_detection', {}).get('pre_check_enabled', True):
            recommendations['conflict_detection'] = (
                "Pre-conflict checking is disabled. This may lead to unexpected conflicts. "
                "Consider enabling pre_check_enabled for smoother workflow."
            )
        
        # Security recommendations
        protected_branches = current_config.get('security', {}).get('protected_branches', [])
        if not protected_branches or len(protected_branches) < 2:
            recommendations['protected_branches'] = (
                "Few or no protected branches configured. Consider protecting "
                "important branches like 'main', 'master', and 'develop'."
            )
        
        return recommendations
    
    def diff_configs(self, config1: Dict, config2: Dict) -> Dict[str, Any]:
        """
        Compare two configurations and return differences.
        
        Args:
            config1: First configuration
            config2: Second configuration
            
        Returns:
            Dictionary of differences
        """
        differences = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # Get all keys from both configs
        all_sections = set(list(config1.keys()) + list(config2.keys()))
        
        for section in all_sections:
            # Check if section exists in both configs
            if section not in config1:
                differences["added"][section] = config2[section]
                continue
                
            if section not in config2:
                differences["removed"][section] = config1[section]
                continue
            
            # Compare keys within the section
            section_keys1 = set(config1[section].keys())
            section_keys2 = set(config2[section].keys())
            
            # Find added keys
            for key in section_keys2 - section_keys1:
                if section not in differences["added"]:
                    differences["added"][section] = {}
                differences["added"][section][key] = config2[section][key]
            
            # Find removed keys
            for key in section_keys1 - section_keys2:
                if section not in differences["removed"]:
                    differences["removed"][section] = {}
                differences["removed"][section][key] = config1[section][key]
            
            # Find changed keys
            for key in section_keys1 & section_keys2:
                if config1[section][key] != config2[section][key]:
                    if section not in differences["changed"]:
                        differences["changed"][section] = {}
                    differences["changed"][section][key] = {
                        "old": config1[section][key],
                        "new": config2[section][key]
                    }
        
        return differences
    
    def merge_configs(self, base_config: Dict, override_config: Dict) -> Dict:
        """
        Merge two configurations with override taking precedence.
        
        Args:
            base_config: Base configuration
            override_config: Override configuration that takes precedence
            
        Returns:
            Merged configuration
        """
        merged_config = {}
        
        # Start with a deep copy of base_config
        import copy
        merged_config = copy.deepcopy(base_config)
        
        # Merge override_config
        for section, section_data in override_config.items():
            if not isinstance(section_data, dict):
                # If it's not a dictionary, simply override
                merged_config[section] = section_data
                continue
                
            # Create section if it doesn't exist
            if section not in merged_config:
                merged_config[section] = {}
            
            # Merge keys in the section
            for key, value in section_data.items():
                merged_config[section][key] = value
        
        return merged_config
    
    def get_schema_section(self, section: Optional[str] = None) -> Dict:
        """
        Get the validation schema for a specific section or all sections.
        
        Args:
            section: Section name or None for all sections
            
        Returns:
            Dictionary of validation rules
        """
        if section is None:
            return self._CONFIG_SCHEMA
        
        if section not in self._CONFIG_SCHEMA:
            raise ValueError(f"Unknown configuration section: {section}")
        
        return {section: self._CONFIG_SCHEMA[section]}

