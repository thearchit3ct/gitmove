"""
Gestionnaire de récupération pour GitMove.

Ce module fournit des mécanismes pour sauvegarder l'état du dépôt
avant des opérations critiques et restaurer cet état en cas d'échec.
"""

import os
import tempfile
import shutil
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from contextlib import contextmanager

from git import Repo, Git
from git.exc import GitCommandError

from gitmove.utils.logger import get_logger
from gitmove.exceptions import RecoveryError, GitError, convert_git_error

logger = get_logger(__name__)

class RecoveryManager:
    """
    Gestionnaire de récupération d'état pour les opérations Git.
    
    Permet de sauvegarder et restaurer l'état du dépôt Git.
    """
    
    def __init__(self, repo: Repo):
        """
        Initialise le gestionnaire de récupération.
        
        Args:
            repo: Instance du dépôt Git
        """
        self.repo = repo
        self.git = Git(repo.working_dir)
        self.recovery_actions = []
        self.saved_states = {}
        self.stash_index = None
    
    def save_state(self, name: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Sauvegarde l'état actuel du dépôt.
        
        Args:
            name: Nom unique pour cet état
            callback: Fonction de rappel qui retourne des données supplémentaires
            
        Returns:
            État sauvegardé
        """
        state = {
            "timestamp": time.time(),
            "current_branch": None,
            "stash_created": False,
            "stash_id": None,
            "head_commit": None,
            "custom_data": None
        }
        
        try:
            # Récupérer la branche courante
            try:
                state["current_branch"] = self.repo.active_branch.name
            except (TypeError, AttributeError):
                # HEAD détaché
                state["current_branch"] = None
            
            # Récupérer le commit HEAD actuel
            state["head_commit"] = self.repo.head.commit.hexsha
            
            # Si le répertoire de travail n'est pas propre, créer un stash
            if self.repo.is_dirty(untracked_files=True):
                msg = f"GitMove recovery point: {name}"
                result = self.git.stash("save", "--include-untracked", msg)
                
                # Récupérer l'ID du stash s'il a été créé
                if not result.startswith("No local changes to save"):
                    state["stash_created"] = True
                    state["stash_id"] = self._get_last_stash_id()
            
            # Exécuter le callback si présent
            if callback:
                state["custom_data"] = callback()
            
            # Stocker l'état
            self.saved_states[name] = state
            logger.debug(f"État sauvegardé: {name}")
            
            return state
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'état: {str(e)}")
            return state
    
    def restore_state(self, name: str, force: bool = False) -> bool:
        """
        Restaure un état précédemment sauvegardé.
        
        Args:
            name: Nom de l'état à restaurer
            force: Si True, force la restauration même en cas de conflits
            
        Returns:
            True si la restauration a réussi
            
        Raises:
            RecoveryError: Si la restauration échoue
        """
        if name not in self.saved_states:
            raise RecoveryError(f"État inconnu: {name}")
        
        state = self.saved_states[name]
        logger.info(f"Restauration de l'état: {name}")
        
        try:
            # Revenir au commit HEAD
            if state["head_commit"]:
                try:
                    self.git.reset("--hard", state["head_commit"])
                    logger.debug(f"Reset à {state['head_commit']}")
                except GitCommandError as e:
                    logger.error(f"Erreur lors du reset: {str(e)}")
                    if not force:
                        raise convert_git_error(e, "Impossible de revenir au commit précédent")
            
            # Revenir à la branche originale
            if state["current_branch"]:
                try:
                    self.git.checkout(state["current_branch"])
                    logger.debug(f"Checkout de {state['current_branch']}")
                except GitCommandError as e:
                    logger.error(f"Erreur lors du checkout: {str(e)}")
                    if not force:
                        raise convert_git_error(e, f"Impossible de revenir à la branche {state['current_branch']}")
            
            # Appliquer le stash si nécessaire
            if state["stash_created"] and state["stash_id"]:
                try:
                    self.git.stash("apply", state["stash_id"])
                    logger.debug(f"Stash appliqué: {state['stash_id']}")
                    
                    # Supprimer le stash
                    self.git.stash("drop", state["stash_id"])
                except GitCommandError as e:
                    logger.error(f"Erreur lors de l'application du stash: {str(e)}")
                    if not force:
                        raise convert_git_error(e, "Impossible d'appliquer le stash")
            
            # Supprimer l'état restauré
            del self.saved_states[name]
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {str(e)}")
            if isinstance(e, GitError):
                raise
            raise RecoveryError(f"Erreur lors de la restauration: {str(e)}", e)
    
    def _get_last_stash_id(self) -> Optional[str]:
        """
        Récupère l'ID du dernier stash créé.
        
        Returns:
            ID du stash ou None
        """
        try:
            stash_list = self.git.stash("list")
            if stash_list:
                # Le format est "stash@{0}: ..."
                stash_id = stash_list.splitlines()[0].split(":")[0].strip()
                return stash_id
        except GitCommandError:
            pass
        return None
    
    def register_recovery_action(self, action: Callable, *args, **kwargs):
        """
        Enregistre une action de récupération à exécuter en cas d'erreur.
        
        Args:
            action: Fonction à exécuter
            *args: Arguments pour la fonction
            **kwargs: Arguments nommés pour la fonction
        """
        self.recovery_actions.append((action, args, kwargs))
    
    def execute_recovery_actions(self):
        """
        Exécute toutes les actions de récupération enregistrées.
        """
        errors = []
        for action, args, kwargs in reversed(self.recovery_actions):
            try:
                action(*args, **kwargs)
            except Exception as e:
                errors.append(str(e))
        
        if errors:
            logger.error(f"Erreurs lors de la récupération: {', '.join(errors)}")
            return False
        return True
    
    @contextmanager
    def safe_operation(self, name: str, recovery_callback: Optional[Callable] = None):
        """
        Contexte pour exécuter une opération avec sauvegarde et restauration automatique.
        
        Args:
            name: Nom de l'opération
            recovery_callback: Fonction à appeler après la restauration en cas d'erreur
        """
        # Sauvegarder l'état actuel
        self.save_state(name)
        
        try:
            # Exécuter l'opération
            yield
        except Exception as e:
            # En cas d'erreur, restaurer l'état
            logger.warning(f"Erreur durant l'opération {name}: {str(e)}")
            try:
                self.restore_state(name)
                logger.info(f"État restauré avec succès pour: {name}")
                
                # Exécuter le callback de récupération si présent
                if recovery_callback:
                    recovery_callback()
                
                # Exécuter les actions de récupération enregistrées
                self.execute_recovery_actions()
            except Exception as recovery_error:
                logger.error(f"Erreur lors de la restauration: {str(recovery_error)}")
            
            # Propager l'erreur originale
            raise