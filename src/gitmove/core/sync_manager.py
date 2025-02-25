"""
Gestionnaire de synchronisation Git pour GitMove.

Ce module fournit des fonctionnalités pour :
- Synchroniser une branche avec la branche principale
- Vérifier l'état de synchronisation
- Choisir la stratégie optimale pour la synchronisation
"""

import os
from typing import Dict, List, Optional, Tuple, Union

from git import Git, Repo
from git.exc import GitCommandError

from gitmove.config import Config
from gitmove.utils.git_commands import (
    get_current_branch,
    get_branch_divergence,
    fetch_updates,
    merge_branch,
    rebase_branch,
)
from gitmove.utils.logger import get_logger
from gitmove.core.conflict_detector import ConflictDetector

logger = get_logger(__name__)

class SyncManager:
    """
    Gestionnaire de synchronisation Git.
    """
    
    def __init__(self, repo: Repo, config: Config):
        """
        Initialise le gestionnaire de synchronisation.
        
        Args:
            repo: Instance du dépôt Git
            config: Configuration de GitMove
        """
        self.repo = repo
        self.config = config
        self.git = Git(repo.working_dir)
        self.main_branch = config.get_value("general.main_branch", "main")
        self.default_strategy = config.get_value("sync.default_strategy", "rebase")
        self.conflict_detector = ConflictDetector(repo, config)
    
    def check_sync_status(self, branch_name: Optional[str] = None) -> Dict:
        """
        Vérifie l'état de synchronisation d'une branche avec la branche principale.
        
        Args:
            branch_name: Nom de la branche à vérifier. Si None, utilise la branche courante.
            
        Returns:
            Dictionnaire contenant l'état de synchronisation
        """
        if branch_name is None:
            branch_name = get_current_branch(self.repo)
        
        if branch_name == self.main_branch:
            return {
                "is_synced": True,
                "branch": branch_name,
                "target": self.main_branch,
                "ahead_commits": 0,
                "behind_commits": 0,
                "message": "La branche est la branche principale"
            }
        
        # D'abord, s'assurer que nous avons les dernières mises à jour
        try:
            fetch_updates(self.repo)
        except GitCommandError as e:
            logger.warning(f"Erreur lors de la récupération des mises à jour: {str(e)}")
        
        # Calculer la divergence
        ahead, behind = get_branch_divergence(self.repo, branch_name, self.main_branch)
        
        status = {
            "is_synced": behind == 0,
            "branch": branch_name,
            "target": self.main_branch,
            "ahead_commits": ahead,
            "behind_commits": behind,
        }
        
        if behind == 0:
            status["message"] = "La branche est à jour avec la branche principale"
        else:
            status["message"] = f"La branche est en retard de {behind} commit(s) par rapport à la branche principale"
            
            if ahead > 0:
                status["message"] += f" et en avance de {ahead} commit(s)"
        
        return status
    
    def sync_with_main(
        self, 
        branch_name: Optional[str] = None, 
        strategy: str = "auto"
    ) -> Dict:
        """
        Synchronise une branche avec la branche principale.
        
        Args:
            branch_name: Nom de la branche à synchroniser. Si None, utilise la branche courante.
            strategy: Stratégie à utiliser ('merge', 'rebase' ou 'auto')
            
        Returns:
            Dictionnaire contenant les résultats de la synchronisation
        """
        if branch_name is None:
            branch_name = get_current_branch(self.repo)
        
        # Vérifier si la branche est déjà à jour
        sync_status = self.check_sync_status(branch_name)
        
        if sync_status["is_synced"]:
            return {
                "status": "up-to-date",
                "branch": branch_name,
                "target": self.main_branch,
                "message": "La branche est déjà à jour avec la branche principale"
            }
        
        # Choisir la stratégie si 'auto'
        if strategy == "auto":
            strategy = self._determine_sync_strategy(branch_name, self.main_branch)
        
        # Vérifier les conflits potentiels avant la synchronisation
        conflicts = self.conflict_detector.detect_conflicts(branch_name, self.main_branch)
        
        if conflicts["has_conflicts"]:
            return {
                "status": "conflicts",
                "branch": branch_name,
                "target": self.main_branch,
                "strategy": strategy,
                "conflicts": conflicts,
                "message": f"{len(conflicts['conflicting_files'])} conflit(s) potentiel(s) détecté(s)"
            }
        
        # Sauvegarder la branche actuelle
        current_branch = get_current_branch(self.repo)
        
        try:
            # S'assurer d'être sur la bonne branche
            if current_branch != branch_name:
                self.git.checkout(branch_name)
            
            # Effectuer la synchronisation
            if strategy == "merge":
                result = merge_branch(self.repo, self.main_branch)
            else:  # rebase
                result = rebase_branch(self.repo, self.main_branch)
            
            if result["success"]:
                return {
                    "status": "synchronized",
                    "branch": branch_name,
                    "target": self.main_branch,
                    "strategy": strategy,
                    "message": f"Synchronisation réussie avec la stratégie '{strategy}'"
                }
            else:
                return {
                    "status": "failed",
                    "branch": branch_name,
                    "target": self.main_branch,
                    "strategy": strategy,
                    "error": result["error"],
                    "message": f"Échec de la synchronisation: {result['error']}"
                }
        
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {str(e)}")
            return {
                "status": "error",
                "branch": branch_name,
                "target": self.main_branch,
                "strategy": strategy,
                "error": str(e),
                "message": f"Erreur lors de la synchronisation: {str(e)}"
            }
        
        finally:
            # Revenir à la branche d'origine si nécessaire
            if current_branch != branch_name and current_branch in [b.name for b in self.repo.heads]:
                try:
                    self.git.checkout(current_branch)
                except GitCommandError as e:
                    logger.error(f"Erreur lors du retour à la branche d'origine: {str(e)}")
    
    def _determine_sync_strategy(self, branch_name: str, target_branch: str) -> str:
        """
        Détermine la stratégie optimale pour la synchronisation.
        
        Args:
            branch_name: Nom de la branche à synchroniser
            target_branch: Nom de la branche cible
            
        Returns:
            Stratégie recommandée ('merge' ou 'rebase')
        """
        # Utiliser la stratégie par défaut configurée
        strategy = self.default_strategy
        
        # Si le default_strategy est déjà soit "merge" soit "rebase", le retourner directement
        if strategy in ["merge", "rebase"]:
            return strategy
        
        # Sinon, calculer la stratégie optimale
        try:
            # 1. Nombre de commits en avance
            ahead, behind = get_branch_divergence(self.repo, branch_name, target_branch)
            
            # Règle : Si peu de commits en avance, préférer le rebase
            rebase_threshold = self.config.get_value("advice.rebase_threshold", 5)
            
            if ahead <= rebase_threshold:
                return "rebase"
            
            # 2. Type de branche
            force_merge_patterns = self.config.get_value("advice.force_merge_patterns", [])
            force_rebase_patterns = self.config.get_value("advice.force_rebase_patterns", [])
            
            # Vérifier si la branche correspond à un pattern spécifique
            import fnmatch
            
            for pattern in force_merge_patterns:
                if fnmatch.fnmatch(branch_name, pattern):
                    return "merge"
            
            for pattern in force_rebase_patterns:
                if fnmatch.fnmatch(branch_name, pattern):
                    return "rebase"
            
            # 3. Conflits potentiels
            conflicts = self.conflict_detector.detect_conflicts(branch_name, target_branch)
            
            if conflicts["has_conflicts"]:
                # En cas de conflits nombreux ou graves, préférer le merge
                high_severity = sum(1 for c in conflicts.get("conflicting_files", []) 
                                   if c.get("severity") == "Élevée")
                
                if high_severity > 0 or len(conflicts.get("conflicting_files", [])) > 3:
                    return "merge"
            
            # Par défaut, utiliser rebase pour un historique plus propre
            return "rebase"
            
        except Exception as e:
            logger.error(f"Erreur lors de la détermination de la stratégie: {str(e)}")
            # En cas d'erreur, revenir à la stratégie par défaut
            return "merge" if self.default_strategy not in ["merge", "rebase"] else self.default_strategy
    
    def schedule_sync(self, frequency: str = "daily") -> Dict:
        """
        Planifie une synchronisation automatique.
        
        Note: Cette méthode ne fait que renvoyer les paramètres qui seraient utilisés.
        L'implémentation réelle nécessiterait un mécanisme de planification externe.
        
        Args:
            frequency: Fréquence de synchronisation ('hourly', 'daily', 'weekly')
            
        Returns:
            Dictionnaire contenant les paramètres de planification
        """
        auto_sync = self.config.get_value("sync.auto_sync", False)
        
        if not auto_sync:
            return {
                "status": "disabled",
                "message": "La synchronisation automatique est désactivée"
            }
        
        return {
            "status": "scheduled",
            "frequency": frequency,
            "target": self.main_branch,
            "strategy": self.default_strategy,
            "message": f"Synchronisation planifiée avec fréquence '{frequency}'"
        }