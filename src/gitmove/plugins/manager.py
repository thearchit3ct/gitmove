"""
GitMove Plugin System

Allows extending GitMove functionality through a flexible plugin architecture.
"""

import os
import importlib
import inspect
from typing import Dict, Any, Callable, List

class PluginManager:
    def __init__(self, plugin_dir: str = None):
        """
        Initialize plugin management system.
        
        Args:
            plugin_dir: Directory containing plugin modules
        """
        self.plugins: Dict[str, Any] = {}
        self.hooks: Dict[str, List[Callable]] = {
            'pre_branch_clean': [],
            'post_branch_clean': [],
            'pre_sync': [],
            'post_sync': [],
            'conflict_resolution': [],
            'branch_strategy': []
        }
        
        # Default plugin directory
        if plugin_dir is None:
            plugin_dir = os.path.join(
                os.path.expanduser("~"), 
                ".gitmove", 
                "plugins"
            )
        
        self.plugin_dir = plugin_dir
        os.makedirs(plugin_dir, exist_ok=True)
    
    def load_plugins(self):
        """
        Discover and load plugins from plugin directory.
        """
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"gitmove_plugins.{module_name}")
                    self._register_plugin_hooks(module)
                except ImportError as e:
                    print(f"Error loading plugin {module_name}: {e}")
    
    def _register_plugin_hooks(self, module):
        """
        Register hooks from a plugin module.
        
        Args:
            module: Imported plugin module
        """
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # Check for hook decorators
            if hasattr(func, '_gitmove_hook'):
                hook_type = func._gitmove_hook
                self.hooks[hook_type].append(func)
                self.plugins[name] = func
    
    def execute_hook(self, hook_type: str, *args, **kwargs):
        """
        Execute all registered hooks for a specific hook type.
        
        Args:
            hook_type: Type of hook to execute
            *args: Positional arguments to pass to hooks
            **kwargs: Keyword arguments to pass to hooks
        
        Returns:
            List of results from hook executions
        """
        results = []
        for hook in self.hooks.get(hook_type, []):
            try:
                result = hook(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error in {hook.__name__} hook: {e}")
        return results

def hook(hook_type: str):
    """
    Decorator to mark functions as GitMove plugin hooks.
    
    Args:
        hook_type: Type of hook (e.g., 'pre_branch_clean', 'post_sync')
    """
    def decorator(func):
        func._gitmove_hook = hook_type
        return func
    return decorator

# Example plugin usage
def example_plugin():
    """
    Example of how to create a GitMove plugin.
    """
    # Sample pre-branch clean hook
    @hook('pre_branch_clean')
    def validate_branch_cleanup(branches):
        """
        Custom validation before branch cleanup.
        
        Args:
            branches: List of branches to be cleaned
        
        Returns:
            Filtered list of branches or raises exception
        """
        # Custom logic to prevent cleaning certain branches
        return [
            branch for branch in branches 
            if not branch.startswith('temp_') and not branch.startswith('wip/')
        ]
    
    # Sample conflict resolution hook
    @hook('conflict_resolution')
    def custom_conflict_resolver(conflicting_files):
        """
        Custom conflict resolution strategy.
        
        Args:
            conflicting_files: List of files with conflicts
        
        Returns:
            Resolution strategy or None
        """
        # Implement custom conflict resolution logic
        pass

# Integration with core GitMove components
class GitMovePluginAwareComponent:
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
    
    def _apply_plugin_hooks(self, hook_type: str, *args, **kwargs):
        """
        Helper method to apply plugin hooks in core components.
        
        Args:
            hook_type: Type of hook to execute
            *args: Positional arguments for hooks
            **kwargs: Keyword arguments for hooks
        
        Returns:
            Modified arguments or results from hooks
        """
        hook_results = self.plugin_manager.execute_hook(hook_type, *args, **kwargs)
        
        # Allow plugins to modify arguments or provide alternative implementations
        if hook_results:
            # Use the last non-None result
            final_result = next((r for r in reversed(hook_results) if r is not None), None)
            return final_result
        
        return None