"""
Validateurs pour les dépôts Git.

Ce module fournit des fonctions pour valider l'état et la structure d'un dépôt Git
avant d'effectuer des opérations potentiellement dangereuses.
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple, Union

from git import Git, Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from gitmove.utils.logger import get_logger

logger = get_logger(__name__)

def validate_git_repo(repo: Optional[Repo]) -> bool:
    """
    Valide qu'un objet est bien un dépôt Git valide.
    
    Args:
        repo: Instance du dépôt Git à valider
        
    Returns:
        True si le dépôt est valide
        
    Raises:
        ValueError: Si le dépôt n'est pas valide
    """
    if repo is None:
        raise ValueError("Le dépôt Git spécifié est None")
    
    if not isinstance(repo, Repo):
        raise ValueError("L'objet fourni n'est pas une instance Repo valide")
    
    try:
        # Vérifier que c'est bien un dépôt Git (lève une exception sinon)
        if not repo.git_dir:
            raise ValueError("Le dépôt Git spécifié n'a pas de répertoire .git valide")
        
        # Vérifier que le dépôt a au moins une référence (commit)
        if len(list(repo.iter_commits(max_count=1))) == 0:
            raise ValueError("Le dépôt Git est vide (aucun commit)")
        
        return True
    except InvalidGitRepositoryError:
        raise ValueError("Le dépôt Git spécifié n'est pas valide")
    except Exception as e:
        raise ValueError(f"Erreur lors de la validation du dépôt Git: {str(e)}")

def validate_branch_exists(repo: Repo, branch_name: str, remote: bool = False) -> bool:
    """
    Vérifie si une branche existe dans le dépôt.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche à vérifier
        remote: Si True, vérifie les branches distantes
        
    Returns:
        True si la branche existe
        
    Raises:
        ValueError: Si la branche n'existe pas
    """
    if remote:
        # Vérifier les branches distantes
        remote_refs = [ref.name.replace("origin/", "") for ref in repo.remotes.origin.refs]
        if branch_name not in remote_refs:
            raise ValueError(f"La branche distante '{branch_name}' n'existe pas")
    else:
        # Vérifier les branches locales
        if branch_name not in [b.name for b in repo.heads]:
            raise ValueError(f"La branche locale '{branch_name}' n'existe pas")
    
    return True

def validate_clean_working_tree(repo: Repo, allow_untracked: bool = True) -> bool:
    """
    Vérifie si le répertoire de travail est propre (pas de changements non commités).
    
    Args:
        repo: Instance du dépôt Git
        allow_untracked: Si True, autorise les fichiers non suivis
        
    Returns:
        True si le répertoire de travail est propre
        
    Raises:
        ValueError: Si le répertoire de travail contient des changements non commités
    """
    git = Git(repo.working_dir)
    
    try:
        # Vérifier s'il y a des changements en attente
        status = repo.git.status(porcelain=True)
        
        if not status:
            return True
        
        # S'il y a des fichiers non suivis mais qu'ils sont autorisés
        if allow_untracked:
            # Filtrer les lignes commençant par "??" (fichiers non suivis)
            modified_lines = [line for line in status.splitlines() if not line.startswith("??")]
            if not modified_lines:
                return True
        
        raise ValueError(
            "Le répertoire de travail contient des changements non commités. "
            "Veuillez commiter ou stasher vos changements avant de continuer."
        )
    except GitCommandError as e:
        raise ValueError(f"Erreur lors de la vérification du répertoire de travail: {str(e)}")

def validate_branch_permission(
    repo: Repo, 
    branch_name: str, 
    protected_branches: Optional[List[str]] = None
) -> bool:
    """
    Vérifie si une branche est protégée contre les modifications.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche à vérifier
        protected_branches: Liste des noms ou patterns de branches protégées
        
    Returns:
        True si la branche peut être modifiée
        
    Raises:
        ValueError: Si la branche est protégée
    """
    if protected_branches is None:
        # Branches généralement protégées par défaut
        protected_branches = ["main", "master", "develop", "release/*"]
    
    # Vérifier si la branche correspond à un pattern protégé
    for pattern in protected_branches:
        if "*" in pattern:
            # Convertir le pattern Git en regex
            regex_pattern = pattern.replace("*", ".*")
            if re.match(f"^{regex_pattern}$", branch_name):
                raise ValueError(
                    f"La branche '{branch_name}' correspond au pattern protégé '{pattern}'. "
                    f"Opération non autorisée sur cette branche."
                )
        elif pattern == branch_name:
            raise ValueError(
                f"La branche '{branch_name}' est protégée. "
                f"Opération non autorisée sur cette branche."
            )
    
    return True

def validate_branch_naming(branch_name: str, allowed_patterns: Optional[List[str]] = None) -> bool:
    """
    Valide que le nom d'une branche suit les conventions de nommage.
    
    Args:
        branch_name: Nom de la branche à valider
        allowed_patterns: Liste des patterns autorisés (ex: 'feature/*', 'bugfix/*')
        
    Returns:
        True si le nom est valide
        
    Raises:
        ValueError: Si le nom ne suit pas les conventions
    """
    if allowed_patterns is None:
        # Patterns par défaut
        allowed_patterns = [
            "feature/*", 
            "bugfix/*", 
            "fix/*", 
            "hotfix/*", 
            "release/*", 
            "chore/*",
            "docs/*",
            "test/*",
            "refactor/*",
            "main",
            "master",
            "develop"
        ]
    
    # Vérifier les caractères valides
    if not re.match(r'^[a-zA-Z0-9_\-./]+$', branch_name):
        raise ValueError(
            f"Le nom de branche '{branch_name}' contient des caractères non autorisés. "
            f"Utilisez uniquement des lettres, chiffres, tirets, underscores et points."
        )
    
    # Vérifier la longueur
    if len(branch_name) > 100:
        raise ValueError(
            f"Le nom de branche '{branch_name}' est trop long (> 100 caractères). "
            f"Utilisez un nom plus court."
        )
    
    # Vérifier la correspondance avec les patterns autorisés
    if allowed_patterns:
        for pattern in allowed_patterns:
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                if branch_name.startswith(prefix):
                    return True
            elif branch_name == pattern:
                return True
        
        # Si on arrive ici, aucun pattern ne correspond
        raise ValueError(
            f"Le nom de branche '{branch_name}' ne suit pas les conventions de nommage. "
            f"Patterns autorisés: {', '.join(allowed_patterns)}"
        )
    
    return True

def validate_safe_operation(
    repo: Repo, 
    operation: str, 
    target_branch: str, 
    force: bool = False
) -> bool:
    """
    Vérifie si une opération est sécurisée à effectuer sur une branche.
    
    Args:
        repo: Instance du dépôt Git
        operation: Type d'opération ('delete', 'force_push', etc.)
        target_branch: Branche cible de l'opération
        force: Si True, ignore certaines vérifications
        
    Returns:
        True si l'opération est sécurisée
        
    Raises:
        ValueError: Si l'opération n'est pas sécurisée
    """
    current_branch = repo.active_branch.name
    
    # Opérations spécifiques
    if operation == "delete":
        # Vérifier qu'on n'essaie pas de supprimer la branche courante
        if target_branch == current_branch:
            raise ValueError(
                f"Impossible de supprimer la branche courante '{target_branch}'. "
                f"Veuillez d'abord basculer sur une autre branche."
            )
        
        # Vérifier que la branche n'est pas protégée
        validate_branch_permission(repo, target_branch)
        
    elif operation == "force_push":
        # Vérifier que la branche n'est pas protégée
        validate_branch_permission(repo, target_branch)
        
    elif operation == "rebase":
        # Vérifier que le répertoire de travail est propre
        validate_clean_working_tree(repo, allow_untracked=False)
        
    elif operation == "reset":
        # Opération très dangereuse
        if not force:
            raise ValueError(
                f"L'opération 'reset' est potentiellement destructrice. "
                f"Utilisez l'option 'force' pour confirmer."
            )
    
    return True

def check_repo_state(repo: Repo) -> Dict:
    """
    Vérifie l'état général du dépôt et renvoie un rapport.
    
    Args:
        repo: Instance du dépôt Git
        
    Returns:
        Dictionnaire contenant l'état du dépôt
    """
    git = Git(repo.working_dir)
    state = {}
    
    try:
        # Branche courante
        state["current_branch"] = repo.active_branch.name
    except Exception:
        state["current_branch"] = "HEAD detached"
    
    # Répertoire de travail propre ?
    try:
        status = repo.git.status(porcelain=True)
        state["is_clean"] = not status
        state["has_untracked"] = any(line.startswith("??") for line in status.splitlines() if status)
        state["has_staged"] = any(line.startswith(" M") for line in status.splitlines() if status)
        state["has_modified"] = any(line.startswith("M ") for line in status.splitlines() if status)
    except GitCommandError:
        state["is_clean"] = False
        state["error"] = "Impossible de vérifier l'état du répertoire"
    
    # Vérifier le stash
    try:
        stash_list = git.stash("list")
        state["has_stashed"] = bool(stash_list)
        state["stash_count"] = len(stash_list.splitlines()) if stash_list else 0
    except GitCommandError:
        state["has_stashed"] = False
        state["stash_count"] = 0
    
    # Vérifier la connexion au dépôt distant
    try:
        remote_url = git.remote("get-url", "origin")
        state["has_remote"] = bool(remote_url)
        state["remote_url"] = remote_url if remote_url else None
    except GitCommandError:
        state["has_remote"] = False
        state["remote_url"] = None
    
    # Vérifier l'état des branches par rapport au remote
    if state.get("has_remote"):
        try:
            git.fetch("--quiet")
            current = state["current_branch"]
            ahead_behind = git.rev_list("--left-right", "--count", f"origin/{current}...{current}")
            behind, ahead = map(int, ahead_behind.split())
            state["behind_commits"] = behind
            state["ahead_commits"] = ahead
        except GitCommandError:
            state["behind_commits"] = 0
            state["ahead_commits"] = 0
    
    return state