"""
Utilitaires pour les commandes Git

Ce module fournit des fonctions de bas niveau pour interagir avec les dépôts Git.
Ces fonctions sont utilisées par les autres modules du projet GitMove.
"""

import os
import re
import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

from git import Git, Repo
from git.exc import GitCommandError

def get_repo(path: Optional[str] = None) -> Repo:
    """
    Obtient une instance du dépôt Git.
    
    Args:
        path: Chemin vers le dépôt Git. Si None, utilise le répertoire courant.
        
    Returns:
        Instance du dépôt Git
        
    Raises:
        ValueError: Si le chemin spécifié n'est pas un dépôt Git valide
    """
    if path is None:
        path = os.getcwd()
    
    try:
        return Repo(path, search_parent_directories=True)
    except Exception as e:
        raise ValueError(f"Impossible de trouver un dépôt Git valide dans {path}: {str(e)}")

def get_current_branch(repo: Repo) -> str:
    """
    Obtient le nom de la branche courante.
    
    Args:
        repo: Instance du dépôt Git
        
    Returns:
        Nom de la branche courante
    """
    try:
        return repo.active_branch.name
    except Exception as e:
        # Si HEAD est détaché, on renvoie l'ID du commit
        return repo.git.rev_parse("HEAD", short=True)

def get_main_branch(repo: Repo) -> str:
    """
    Détermine la branche principale du dépôt.
    
    Args:
        repo: Instance du dépôt Git
        
    Returns:
        Nom de la branche principale (main ou master)
    """
    # Vérifier les branches principales courantes
    main_candidates = ["main", "master"]
    
    for candidate in main_candidates:
        if candidate in [b.name for b in repo.heads]:
            return candidate
    
    # Si aucune ne correspond, tenter de déduire à partir de l'origine
    try:
        origin_head = repo.git.symbolic_ref("refs/remotes/origin/HEAD", quiet=True).split("/")[-1]
        if origin_head:
            return origin_head
    except GitCommandError:
        pass
    
    # Par défaut, utiliser la première branche
    if repo.heads:
        return repo.heads[0].name
    
    # Fallback
    return "main"

def is_branch_merged(
    repo: Repo, 
    branch_name: str, 
    target_branch: str = "main", 
    is_remote: bool = False
) -> bool:
    """
    Vérifie si une branche a été fusionnée dans une autre.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche à vérifier
        target_branch: Nom de la branche cible
        is_remote: Indique si la branche est distante
        
    Returns:
        True si la branche est fusionnée, False sinon
    """
    git = Git(repo.working_dir)
    
    branch_ref = f"origin/{branch_name}" if is_remote else branch_name
    target_ref = f"origin/{target_branch}" if is_remote else target_branch
    
    # Vérifier si la branche existe
    branches = [b.name for b in repo.heads]
    remote_branches = [ref.name.replace("origin/", "") for ref in repo.remotes.origin.refs]
    
    if is_remote and branch_name not in remote_branches:
        return False
    
    if not is_remote and branch_name not in branches:
        return False
    
    try:
        # Vérifier si le dernier commit de la branche est accessible depuis la branche cible
        last_commit = git.rev_parse(branch_ref)
        merged_branches = git.branch("--contains", last_commit, "-a")
        
        # Vérifier si la branche cible est dans la liste des branches contenant ce commit
        target_pattern = re.compile(r'(\s|origin/)' + re.escape(target_branch) + r'($|\s)')
        return bool(target_pattern.search(merged_branches))
    except GitCommandError:
        return False

def get_branch_last_commit_date(repo: Repo, branch_name: str) -> str:
    """
    Obtient la date du dernier commit sur une branche.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche
        
    Returns:
        Date du dernier commit au format YYYY-MM-DD
    """
    try:
        git = Git(repo.working_dir)
        date_str = git.log(branch_name, "-1", "--format=%cd", "--date=short")
        return date_str.strip()
    except GitCommandError:
        return "Inconnue"

def get_branch_age(repo: Repo, branch_name: str) -> int:
    """
    Calcule l'âge d'une branche en jours.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche
        
    Returns:
        Âge de la branche en jours
    """
    try:
        date_str = get_branch_last_commit_date(repo, branch_name)
        if date_str == "Inconnue":
            return 0
        
        last_commit_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        days = (datetime.datetime.now() - last_commit_date).days
        return max(0, days)  # Éviter les valeurs négatives
    except Exception:
        return 0

def get_branch_commit_count(repo: Repo, branch_name: str, base_branch: Optional[str] = None) -> int:
    """
    Compte le nombre de commits dans une branche.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche
        base_branch: Branche de base pour le comptage. Si None, compte tous les commits.
        
    Returns:
        Nombre de commits
    """
    try:
        git = Git(repo.working_dir)
        
        if base_branch:
            # Compter uniquement les commits propres à cette branche
            merge_base = git.merge_base(branch_name, base_branch)
            count_str = git.rev_list("--count", f"{merge_base}..{branch_name}")
        else:
            # Compter tous les commits
            count_str = git.rev_list("--count", branch_name)
        
        return int(count_str.strip())
    except Exception:
        return 0

def get_tracking_branch(repo: Repo, branch_name: str) -> Optional[str]:
    """
    Obtient la branche distante suivie par une branche locale.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche locale
        
    Returns:
        Nom de la branche distante ou None
    """
    try:
        git = Git(repo.working_dir)
        
        for line in git.branch("-vv").split("\n"):
            # Rechercher la ligne correspondant à la branche
            if f" {branch_name} " in line or line.startswith(f"* {branch_name}"):
                # Rechercher la branche distante entre crochets
                match = re.search(r'\[(.*?)(?::.*)?\]', line)
                if match:
                    return match.group(1)
        
        return None
    except GitCommandError:
        return None

def get_branch_divergence(repo: Repo, branch_name: str, target_branch: str) -> Tuple[int, int]:
    """
    Calcule la divergence entre deux branches.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche source
        target_branch: Nom de la branche cible
        
    Returns:
        Tuple (ahead, behind) indiquant le nombre de commits d'avance et de retard
    """
    try:
        git = Git(repo.working_dir)
        
        # Trouver l'ancêtre commun
        merge_base = git.merge_base(branch_name, target_branch)
        
        # Compter les commits spécifiques à chaque branche
        ahead = int(git.rev_list("--count", f"{merge_base}..{branch_name}").strip())
        behind = int(git.rev_list("--count", f"{merge_base}..{target_branch}").strip())
        
        return ahead, behind
    except GitCommandError:
        return 0, 0

def get_common_ancestor(repo: Repo, branch1: str, branch2: str) -> Optional[str]:
    """
    Trouve l'ancêtre commun entre deux branches.
    
    Args:
        repo: Instance du dépôt Git
        branch1: Nom de la première branche
        branch2: Nom de la deuxième branche
        
    Returns:
        SHA de l'ancêtre commun ou None
    """
    try:
        git = Git(repo.working_dir)
        return git.merge_base(branch1, branch2).strip()
    except GitCommandError:
        return None

def get_modified_files(repo: Repo, since_commit: str, until_commit: str) -> Set[str]:
    """
    Obtient la liste des fichiers modifiés entre deux commits.
    
    Args:
        repo: Instance du dépôt Git
        since_commit: Commit de départ
        until_commit: Commit d'arrivée
        
    Returns:
        Ensemble des fichiers modifiés
    """
    try:
        git = Git(repo.working_dir)
        diff_output = git.diff("--name-only", f"{since_commit}..{until_commit}")
        
        # Renvoyer un ensemble pour éviter les doublons
        return set(diff_output.strip().split("\n")) if diff_output.strip() else set()
    except GitCommandError:
        return set()

def fetch_updates(repo: Repo) -> bool:
    """
    Récupère les dernières mises à jour du dépôt distant.
    
    Args:
        repo: Instance du dépôt Git
        
    Returns:
        True si la récupération a réussi, False sinon
    """
    try:
        git = Git(repo.working_dir)
        git.fetch("--all", "--prune")
        return True
    except GitCommandError:
        return False

def delete_local_branch(repo: Repo, branch_name: str, force: bool = False) -> bool:
    """
    Supprime une branche locale.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche à supprimer
        force: Si True, force la suppression même si la branche n'est pas fusionnée
        
    Returns:
        True si la suppression a réussi, False sinon
    """
    try:
        git = Git(repo.working_dir)
        delete_option = "-D" if force else "-d"
        git.branch(delete_option, branch_name)
        return True
    except GitCommandError:
        return False

def delete_remote_branch(
    repo: Repo, 
    branch_name: str, 
    remote_name: str = "origin"
) -> bool:
    """
    Supprime une branche distante.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche à supprimer
        remote_name: Nom du dépôt distant
        
    Returns:
        True si la suppression a réussi, False sinon
    """
    try:
        git = Git(repo.working_dir)
        git.push(remote_name, "--delete", branch_name)
        return True
    except GitCommandError:
        return False

def merge_branch(repo: Repo, source_branch: str, target_branch: Optional[str] = None) -> Dict:
    """
    Fusionne une branche dans la branche courante ou dans une branche spécifiée.
    
    Args:
        repo: Instance du dépôt Git
        source_branch: Nom de la branche source à fusionner
        target_branch: Nom de la branche cible. Si None, utilise la branche courante.
        
    Returns:
        Dictionnaire contenant le résultat de la fusion
    """
    current_branch = get_current_branch(repo)
    target = target_branch or current_branch
    git = Git(repo.working_dir)
    
    # Vérifier si on doit changer de branche
    branch_changed = False
    
    try:
        # Changer de branche si nécessaire
        if current_branch != target:
            git.checkout(target)
            branch_changed = True
        
        # Effectuer la fusion
        git.merge(source_branch, "--no-ff")
        
        return {
            "success": True,
            "message": f"Fusion de '{source_branch}' dans '{target}' réussie",
            "branch_changed": branch_changed
        }
    except GitCommandError as e:
        # En cas d'erreur, annuler la fusion
        try:
            git.merge("--abort")
        except GitCommandError:
            pass
        
        return {
            "success": False,
            "error": str(e),
            "branch_changed": branch_changed
        }
    finally:
        # Revenir à la branche d'origine si nécessaire
        if branch_changed:
            try:
                git.checkout(current_branch)
            except GitCommandError:
                pass

def rebase_branch(repo: Repo, base_branch: str, target_branch: Optional[str] = None) -> Dict:
    """
    Rebase une branche sur une autre.
    
    Args:
        repo: Instance du dépôt Git
        base_branch: Nom de la branche de base
        target_branch: Nom de la branche à rebaser. Si None, utilise la branche courante.
        
    Returns:
        Dictionnaire contenant le résultat du rebase
    """
    current_branch = get_current_branch(repo)
    target = target_branch or current_branch
    git = Git(repo.working_dir)
    
    # Vérifier si on doit changer de branche
    branch_changed = False
    
    try:
        # Changer de branche si nécessaire
        if current_branch != target:
            git.checkout(target)
            branch_changed = True
        
        # Effectuer le rebase
        git.rebase(base_branch)
        
        return {
            "success": True,
            "message": f"Rebase de '{target}' sur '{base_branch}' réussi",
            "branch_changed": branch_changed
        }
    except GitCommandError as e:
        # En cas d'erreur, annuler le rebase
        try:
            git.rebase("--abort")
        except GitCommandError:
            pass
        
        return {
            "success": False,
            "error": str(e),
            "branch_changed": branch_changed
        }
    finally:
        # Revenir à la branche d'origine si nécessaire
        if branch_changed:
            try:
                git.checkout(current_branch)
            except GitCommandError:
                pass