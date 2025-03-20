"""
Gestionnaire de branches Git pour GitMove.

Ce module fournit des fonctionnalités pour :
- Lister les branches
- Nettoyer les branches fusionnées
- Obtenir des informations détaillées sur les branches
"""

import os
import datetime
from typing import Dict, List, Optional, Tuple, Union

from git import Git, Repo
from git.exc import GitCommandError

from gitmove.config import Config
from gitmove.utils.git_commands import (
    get_current_branch,
    is_branch_merged,
    get_branch_last_commit_date,
    delete_branch,
    get_tracking_branch,
)
from gitmove.utils.logger import get_logger

logger = get_logger(__name__)

class BranchManager:
    """
    Gestionnaire de branches Git.
    """
    
    def __init__(self, repo: Repo, config: Config):
        """
        Initialise le gestionnaire de branches.
        
        Args:
            repo: Instance du dépôt Git
            config: Configuration de GitMove
        """
        self.repo = repo
        self.config = config
        self.git = Git(repo.working_dir)
        self.main_branch = config.get_value("general.main_branch", "main")
    
    def get_current_branch(self) -> str:
        """
        Récupère le nom de la branche courante.
        
        Returns:
            Nom de la branche courante
        """
        return get_current_branch(self.repo)
    
    def list_branches(self, include_remote: bool = False) -> List[Dict]:
        """
        Liste toutes les branches du dépôt.
        
        Args:
            include_remote: Inclure les branches distantes
            
        Returns:
            Liste de dictionnaires contenant les informations sur les branches
        """
        branches = []
        
        # Branches locales
        for branch in self.repo.heads:
            branch_info = self._get_branch_info(branch.name, False)
            branches.append(branch_info)
        
        # Branches distantes
        if include_remote:
            for ref in self.repo.remotes.origin.refs:
                # Ignorer HEAD et les branches déjà listées en local
                if ref.name == "origin/HEAD":
                    continue
                
                branch_name = ref.name.replace("origin/", "")
                if any(b["name"] == branch_name for b in branches):
                    continue
                
                branch_info = self._get_branch_info(branch_name, True)
                branches.append(branch_info)
        
        return branches
    
    def _get_branch_info(self, branch_name: str, is_remote: bool = False) -> Dict:
        """
        Récupère les informations détaillées sur une branche.
        
        Args:
            branch_name: Nom de la branche
            is_remote: Indique si la branche est distante
            
        Returns:
            Dictionnaire contenant les informations sur la branche
        """
        ref_name = f"origin/{branch_name}" if is_remote else branch_name
        
        try:
            last_commit_date = get_branch_last_commit_date(self.repo, ref_name)
            tracking = None
            
            if not is_remote:
                tracking = get_tracking_branch(self.repo, branch_name)
            
            merged = is_branch_merged(self.repo, branch_name, self.main_branch, is_remote)
            
            return {
                "name": branch_name,
                "is_remote": is_remote,
                "last_commit_date": last_commit_date,
                "tracking": tracking,
                "is_merged": merged,
                "is_main": branch_name == self.main_branch,
            }
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des informations sur la branche {branch_name}: {str(e)}")
            return {
                "name": branch_name,
                "is_remote": is_remote,
                "last_commit_date": "Inconnue",
                "tracking": None,
                "is_merged": False,
                "is_main": branch_name == self.main_branch,
            }
    
    def find_merged_branches(
        self, 
        include_remote: bool = False, 
        excluded_branches: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Trouve les branches qui ont été fusionnées dans la branche principale.
        
        Args:
            include_remote: Inclure les branches distantes
            excluded_branches: Liste des branches à exclure
            
        Returns:
            Liste des branches fusionnées
        """
        if excluded_branches is None:
            excluded_branches = self.config.get_value("clean.exclude_branches", [])
        
        # Convertir en ensemble pour des recherches plus rapides
        excluded_set = set(excluded_branches or [])
        
        # Ajouter la branche principale aux branches exclues
        excluded_set.add(self.main_branch)
        
        branches = self.list_branches(include_remote)
        merged_branches = []
        
        age_threshold = self.config.get_value("clean.age_threshold", 30)
        threshold_date = (
            datetime.datetime.now() - datetime.timedelta(days=age_threshold)
        ).strftime("%Y-%m-%d")
        
        for branch in branches:
            if (
                branch["is_merged"] and
                branch["name"] not in excluded_set and
                not branch["is_main"]
            ):
                # Vérifier l'âge de la branche si nous avons une date valide
                if branch["last_commit_date"] != "Inconnue":
                    if branch["last_commit_date"] < threshold_date:
                        merged_branches.append(branch)
                else:
                    # Si la date est inconnue, nous l'incluons quand même
                    merged_branches.append(branch)
        
        return merged_branches
    
    def clean_merged_branches(
        self, 
        branches: Optional[List[Dict]] = None, 
        include_remote: bool = False
    ) -> Dict:
        """
        Nettoie les branches fusionnées.
        
        Args:
            branches: Liste des branches à nettoyer. Si None, nettoie toutes les branches fusionnées.
            include_remote: Inclure les branches distantes
            
        Returns:
            Dictionnaire contenant les résultats du nettoyage
        """
        if branches is None:
            branches = self.find_merged_branches(include_remote)
        
        cleaned_branches = []
        failed_branches = []
        
        for branch in branches:
            branch_name = branch["name"]
            is_remote = branch["is_remote"]
            
            try:
                if is_remote:
                    if include_remote:
                        delete_branch(self.repo, branch_name, remote=True)
                        cleaned_branches.append(f"origin/{branch_name}")
                else:
                    delete_branch(self.repo, branch_name)
                    cleaned_branches.append(branch_name)
                    
                    # Si nous nettoyons également les branches distantes et que la branche a un tracking
                    if include_remote and branch.get("tracking"):
                        remote_name = branch["tracking"].split("/")[0]
                        remote_branch = branch["tracking"].split("/", 1)[1]
                        try:
                            delete_branch(self.repo, remote_branch, remote= True, remote_name=remote_name)
                            cleaned_branches.append(branch["tracking"])
                        except GitCommandError:
                            failed_branches.append(branch["tracking"])
            
            except GitCommandError as e:
                logger.error(f"Erreur lors de la suppression de la branche {branch_name}: {str(e)}")
                failed_branches.append(branch_name)
        
        return {
            "cleaned_branches": cleaned_branches,
            "cleaned_count": len(cleaned_branches),
            "failed_branches": failed_branches,
            "failed_count": len(failed_branches),
        }
    
    def get_branch_status(self, branch_name: Optional[str] = None) -> Dict:
        """
        Récupère le statut d'une branche par rapport à la branche principale.
        
        Args:
            branch_name: Nom de la branche. Si None, utilise la branche courante.
            
        Returns:
            Dictionnaire contenant le statut de la branche
        """
        if branch_name is None:
            branch_name = self.get_current_branch()
        
        # Vérifier si la branche existe
        if branch_name not in [b.name for b in self.repo.heads]:
            raise ValueError(f"La branche '{branch_name}' n'existe pas.")
        
        # Obtenir les informations sur la branche
        branch_info = self._get_branch_info(branch_name)
        
        # Obtenir la divergence avec la branche principale
        ahead, behind = self._get_branch_divergence(branch_name, self.main_branch)
        
        return {
            "name": branch_name,
            "is_main": branch_name == self.main_branch,
            "is_merged": branch_info["is_merged"],
            "last_commit_date": branch_info["last_commit_date"],
            "tracking": branch_info["tracking"],
            "ahead_commits": ahead,
            "behind_commits": behind,
        }
    
    def _get_branch_divergence(self, branch, target_branch):
        """
        Obtenir le nombre de commits d'avance et de retard entre deux branches.
        
        Args:
            branch: Nom de la branche à comparer
            target_branch: Nom de la branche cible (souvent main)
        
        Returns:
            Tuple (ahead, behind) avec le nombre de commits
        """
        try:
            # Trouver l'ancêtre commun
            common_ancestor = self.git.merge_base(branch, target_branch)
            
            # Compter les commits en avance
            ahead_output = self.git.rev_list('--count', f'{target_branch}..{branch}')
            ahead = int(ahead_output.strip())
            
            # Compter les commits en retard
            behind_output = self.git.rev_list('--count', f'{branch}..{target_branch}')
            behind = int(behind_output.strip())
            
            return ahead, behind
        except Exception as e:
            print(f"Erreur lors du calcul de la divergence: {e}")
            return 0, 0