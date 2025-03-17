"""
GitMove - Gestionnaire de branches Git intelligent
"""

__version__ = "0.2.0"
__author__ = "Thearchit3ct"
__email__ = "thearchit3ct@outlook.com"

from gitmove.core.branch_manager import BranchManager
from gitmove.core.conflict_detector import ConflictDetector
from gitmove.core.sync_manager import SyncManager
from gitmove.core.strategy_advisor import StrategyAdvisor
from gitmove.config import Config
from gitmove.plugins import PluginManager, hook
from gitmove.env_config import EnvConfigLoader
from gitmove.validators.config_validator import ConfigValidator

__all__ = [
    "BranchManager",
    "ConflictDetector",
    "SyncManager",
    "StrategyAdvisor",
    "Config",
    "PluginManager",
    "hook",
    "EnvConfigLoader",
    "ConfigValidator",
]

# Point d'entrée pour les utilisateurs de l'API
def get_manager(repo_path=None):
    """
    Crée et retourne un gestionnaire GitMove configuré pour le dépôt spécifié.
    
    Args:
        repo_path: Chemin vers le dépôt Git. Si None, utilise le répertoire courant.
        
    Returns:
        Un dictionnaire contenant les gestionnaires principaux de GitMove.
    """
    from gitmove.utils.git_commands import get_repo
    from gitmove.validators.git_repo_validator import validate_git_repo
    
    # Valider et obtenir le dépôt
    repo = get_repo(repo_path)
    validate_git_repo(repo)
    
    # Charger la configuration
    config = Config.load(repo_path)
    
    # Initialiser les gestionnaires
    branch_manager = BranchManager(repo, config)
    conflict_detector = ConflictDetector(repo, config)
    sync_manager = SyncManager(repo, config)
    strategy_advisor = StrategyAdvisor(repo, config)
    
    return {
        "branch_manager": branch_manager,
        "conflict_detector": conflict_detector,
        "sync_manager": sync_manager,
        "strategy_advisor": strategy_advisor,
        "config": config,
        "repo": repo,
    }