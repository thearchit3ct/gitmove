"""
Core de GitMove - Composants principaux du gestionnaire de branches intelligent.

Ce package contient les classes principales qui implémentent les fonctionnalités
centrales de GitMove : gestion des branches, détection de conflits, 
synchronisation et conseils de stratégie.
"""

from gitmove.core.branch_manager import BranchManager
from gitmove.core.conflict_detector import ConflictDetector
from gitmove.core.sync_manager import SyncManager
from gitmove.core.strategy_advisor import StrategyAdvisor

# Version du module core
__version__ = "0.1.0"

# Exporter les classes principales
__all__ = [
    "BranchManager",
    "ConflictDetector", 
    "SyncManager",
    "StrategyAdvisor",
    "initialize_managers",
]

def initialize_managers(repo, config):
    """
    Initialise et renvoie toutes les instances des gestionnaires core.
    
    Cette fonction centralise la création des gestionnaires pour faciliter
    leur utilisation ensemble et garantir qu'ils partagent les mêmes
    instances de dépôt et de configuration.
    
    Args:
        repo: Instance du dépôt Git
        config: Configuration de GitMove
        
    Returns:
        Dictionnaire contenant les instances des gestionnaires
    """
    branch_manager = BranchManager(repo, config)
    conflict_detector = ConflictDetector(repo, config)
    sync_manager = SyncManager(repo, config)
    strategy_advisor = StrategyAdvisor(repo, config)
    
    return {
        "branch_manager": branch_manager,
        "conflict_detector": conflict_detector,
        "sync_manager": sync_manager,
        "strategy_advisor": strategy_advisor,
    }

# Initialisation des dépendances
# Ce bloc s'exécute lors de l'importation du package
try:
    # Log d'initialisation
    from gitmove.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.debug("Initialisation du module core de GitMove")
    
    # Vérifier les dépendances
    import git
    if git.__version__ < "3.1.0":
        logger.warning("La version de GitPython (%s) est ancienne. Il est recommandé d'utiliser "
                     "la version 3.1.0 ou supérieure.", git.__version__)
        
except ImportError as e:
    import warnings
    warnings.warn(f"Erreur lors de l'initialisation du module core: {str(e)}")