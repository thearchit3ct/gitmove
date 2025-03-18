"""
Exceptions personnalisées pour GitMove.

Ce module définit une hiérarchie d'exceptions spécifiques à GitMove
pour permettre une meilleure gestion et récupération des erreurs.
"""

class GitMoveError(Exception):
    """Exception de base pour toutes les erreurs de GitMove."""
    
    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialise une exception GitMove.
        
        Args:
            message: Message d'erreur
            original_error: Exception d'origine qui a causé cette erreur
        """
        self.message = message
        self.original_error = original_error
        super().__init__(message)
    
    def __str__(self) -> str:
        """Représentation en chaîne de l'exception."""
        if self.original_error:
            return f"{self.message} (Causé par: {type(self.original_error).__name__}: {str(self.original_error)})"
        return self.message

# Erreurs de configuration
class ConfigError(GitMoveError):
    """Erreur liée à la configuration."""
    pass

class InvalidConfigError(ConfigError):
    """Configuration invalide."""
    pass

class MissingConfigError(ConfigError):
    """Configuration manquante."""
    pass

# Erreurs Git
class GitError(GitMoveError):
    """Erreur liée à Git."""
    pass

class InvalidRepositoryError(GitError):
    """Dépôt Git invalide."""
    pass

class BranchError(GitError):
    """Erreur liée aux branches."""
    pass

class MissingBranchError(BranchError):
    """Branche manquante."""
    pass

class ProtectedBranchError(BranchError):
    """Opération interdite sur une branche protégée."""
    pass

class DirtyWorkingTreeError(GitError):
    """Répertoire de travail contenant des modifications non commitées."""
    pass

class MergeConflictError(GitError):
    """Conflit de fusion."""
    pass

class SyncError(GitError):
    """Erreur lors de la synchronisation."""
    pass

# Erreurs d'opération
class OperationError(GitMoveError):
    """Erreur lors d'une opération."""
    pass

class AbortedOperationError(OperationError):
    """Opération annulée par l'utilisateur."""
    pass

class PermissionError(OperationError):
    """Opération non autorisée."""
    pass

class RecoveryError(OperationError):
    """Erreur lors de la récupération après une défaillance."""
    pass

# Erreurs de plugin
class PluginError(GitMoveError):
    """Erreur liée aux plugins."""
    pass

class PluginLoadError(PluginError):
    """Erreur lors du chargement d'un plugin."""
    pass

class PluginExecutionError(PluginError):
    """Erreur lors de l'exécution d'un plugin."""
    pass

# Utilitaires pour la gestion des exceptions
def convert_git_error(git_error, message=None):
    """
    Convertit une erreur Git en exception GitMove appropriée.
    
    Args:
        git_error: Exception Git d'origine
        message: Message d'erreur personnalisé
    
    Returns:
        Exception GitMove appropriée
    """
    from git.exc import GitCommandError, InvalidGitRepositoryError
    
    error_msg = message or str(git_error)
    
    if isinstance(git_error, InvalidGitRepositoryError):
        return InvalidRepositoryError(error_msg, git_error)
    
    if isinstance(git_error, GitCommandError):
        # Analyser le message d'erreur pour déterminer le type d'erreur
        error_text = str(git_error)
        
        if "conflict" in error_text.lower():
            return MergeConflictError(error_msg, git_error)
        elif "not a valid object name" in error_text or "did not match any file(s) known to git" in error_text:
            return MissingBranchError(error_msg, git_error)
        elif "working tree clean" not in error_text and "changes not staged" in error_text:
            return DirtyWorkingTreeError(error_msg, git_error)
        elif "refusing to pull" in error_text or "refusing to merge" in error_text:
            return SyncError(error_msg, git_error)
        
    if message:
        return GitError(f"{error_msg} (Causé par: {git_error})")
    else:
        return GitError(f"{git_error}")