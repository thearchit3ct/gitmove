"""
Utilitaires pour les commandes Git

Ce module fournit des fonctions de bas niveau pour interagir avec les dépôts Git.
Ces fonctions sont utilisées par les autres modules du projet GitMove.
"""

import os
import re
import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from git import Git, Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from gitmove.utils.logger import get_logger
from gitmove.utils.recovery_manager import RecoveryManager
from gitmove.exceptions import (
    GitError, InvalidRepositoryError, BranchError, 
    MissingBranchError, DirtyWorkingTreeError, MergeConflictError,
    SyncError, OperationError, convert_git_error
)

def get_repo(path: Optional[str] = None) -> Repo:
    """
    Obtient une instance du dépôt Git avec gestion des erreurs.
    
    Args:
        path: Chemin vers le dépôt Git. Si None, utilise le répertoire courant.
        
    Returns:
        Instance du dépôt Git
        
    Raises:
        InvalidRepositoryError: Si le chemin spécifié n'est pas un dépôt Git valide
    """
    if path is None:
        path = os.getcwd()
    
    try:
        return Repo(path, search_parent_directories=True)
    except InvalidGitRepositoryError as e:
        raise InvalidRepositoryError(
            f"Impossible de trouver un dépôt Git valide dans {path}", 
            original_error=e
        )
    except Exception as e:
        raise GitError(f"Erreur lors de l'accès au dépôt Git: {str(e)}", original_error=e)

def safe_git_command(func: Callable) -> Callable:
    """
    Décorateur pour exécuter des commandes Git avec gestion des erreurs.
    
    Args:
        func: Fonction à décorer
        
    Returns:
        Fonction décorée
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GitCommandError as e:
            raise convert_git_error(e)
        except Exception as e:
            if isinstance(e, GitError):
                raise
            raise GitError(f"Erreur lors de l'exécution de la commande Git: {str(e)}", original_error=e)
    
    return wrapper

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
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

@safe_git_command
def fetch_updates(repo: Repo, remote: str = "origin", prune: bool = True) -> bool:
    """
    Récupère les dernières mises à jour du dépôt distant avec récupération en cas d'erreur.
    
    Args:
        repo: Instance du dépôt Git
        remote: Nom du dépôt distant
        prune: Si True, supprime les références disparues
        
    Returns:
        True si la récupération a réussi
    """
    git = Git(repo.working_dir)
    recovery = RecoveryManager(repo)
    
    with recovery.safe_operation("fetch"):
        if prune:
            git.fetch(remote, "--prune")
        else:
            git.fetch(remote)
        return True

@safe_git_command
def delete_branch(
    repo: Repo, 
    branch_name: str, 
    force: bool = False, 
    remote: bool = False,
    remote_name: str = "origin"
) -> bool:
    """
    Supprime une branche locale ou distante avec vérifications de sécurité.
    
    Args:
        repo: Instance du dépôt Git
        branch_name: Nom de la branche à supprimer
        force: Si True, force la suppression même si la branche n'est pas fusionnée
        remote: Si True, supprime la branche distante
        remote_name: Nom du dépôt distant
        
    Returns:
        True si la suppression a réussi
    """
    from gitmove.utils.git_commands import get_current_branch
    
    git = Git(repo.working_dir)
    recovery = RecoveryManager(repo)
    
    # Vérifier que la branche existe
    if remote:
        remote_refs = [ref.name.replace(f"{remote_name}/", "") for ref in repo.remotes[remote_name].refs]
        if branch_name not in remote_refs:
            raise MissingBranchError(f"La branche distante '{branch_name}' n'existe pas")
    else:
        if branch_name not in [b.name for b in repo.heads]:
            raise MissingBranchError(f"La branche locale '{branch_name}' n'existe pas")
    
    # Vérifier que ce n'est pas la branche courante
    current_branch = get_current_branch(repo)
    if not remote and branch_name == current_branch:
        raise BranchError(
            f"Impossible de supprimer la branche courante '{branch_name}'. "
            f"Veuillez d'abord basculer sur une autre branche."
        )
    
    # Sauvegarder l'état pour une éventuelle récupération
    # Bien que la suppression ne puisse pas être annulée, d'autres opérations pourraient l'être
    recovery.save_state("pre_delete_branch")
    
    try:
        if remote:
            git.push(remote_name, "--delete", branch_name)
            logger.info(f"Branche distante supprimée: {branch_name}")
        else:
            delete_option = "-D" if force else "-d"
            git.branch(delete_option, branch_name)
            logger.info(f"Branche locale supprimée: {branch_name}")
        return True
    except GitCommandError as e:
        error_text = str(e)
        
        # Messages d'erreur plus explicites pour des cas spécifiques
        if "not fully merged" in error_text:
            raise BranchError(
                f"La branche '{branch_name}' n'est pas entièrement fusionnée. "
                f"Utilisez l'option 'force' pour forcer la suppression."
            )
        elif "Couldn't find remote ref" in error_text:
            raise MissingBranchError(f"La branche distante '{branch_name}' n'existe pas")
        
        raise convert_git_error(e)

@safe_git_command
def merge_branch(
    repo: Repo, 
    source_branch: str, 
    target_branch: Optional[str] = None,
    no_ff: bool = True,
    message: Optional[str] = None
) -> Dict:
    """
    Fusionne une branche dans la branche courante avec récupération en cas d'erreur.
    
    Args:
        repo: Instance du dépôt Git
        source_branch: Nom de la branche source à fusionner
        target_branch: Nom de la branche cible. Si None, utilise la branche courante.
        no_ff: Si True, crée toujours un commit de fusion
        message: Message de commit personnalisé
        
    Returns:
        Dictionnaire contenant le résultat de la fusion
    """
    from gitmove.utils.git_commands import get_current_branch
    
    current_branch = get_current_branch(repo)
    target = target_branch or current_branch
    git = Git(repo.working_dir)
    recovery = RecoveryManager(repo)
    
    # Vérifier si on doit changer de branche
    branch_changed = False
    
    with recovery.safe_operation("merge"):
        # Sauvegarder l'état actuel
        recovery.save_state("pre_merge")
        
        try:
            # Changer de branche si nécessaire
            if current_branch != target:
                git.checkout(target)
                branch_changed = True
            
            # Construire les arguments de la commande merge
            merge_args = []
            if no_ff:
                merge_args.append("--no-ff")
            if message:
                merge_args.extend(["-m", message])
            merge_args.append(source_branch)
            
            # Effectuer la fusion
            git.merge(*merge_args)
            
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
            
            error = convert_git_error(e, f"Erreur lors de la fusion de {source_branch} dans {target}")
            
            # Si c'est un conflit, donner plus d'informations
            if isinstance(error, MergeConflictError):
                error.message += ". Résolvez les conflits avant de continuer."
            
            raise error
        finally:
            # Revenir à la branche d'origine si nécessaire
            if branch_changed:
                try:
                    git.checkout(current_branch)
                except GitCommandError as e:
                    logger.error(f"Erreur lors du retour à la branche d'origine: {str(e)}")

@safe_git_command
def rebase_branch(
    repo: Repo, 
    base_branch: str, 
    target_branch: Optional[str] = None
) -> Dict:
    """
    Rebase une branche sur une autre avec récupération en cas d'erreur.
    
    Args:
        repo: Instance du dépôt Git
        base_branch: Nom de la branche de base
        target_branch: Nom de la branche à rebaser. Si None, utilise la branche courante.
        
    Returns:
        Dictionnaire contenant le résultat du rebase
    """
    from gitmove.utils.git_commands import get_current_branch
    
    current_branch = get_current_branch(repo)
    target = target_branch or current_branch
    git = Git(repo.working_dir)
    recovery = RecoveryManager(repo)
    
    # Vérifier si on doit changer de branche
    branch_changed = False
    
    with recovery.safe_operation("rebase"):
        # Sauvegarder l'état actuel
        recovery.save_state("pre_rebase")
        
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
            
            error = convert_git_error(e, f"Erreur lors du rebase de {target} sur {base_branch}")
            
            # Si c'est un conflit, donner plus d'informations
            if isinstance(error, MergeConflictError):
                error.message += ". Résolvez les conflits avant de continuer."
            
            raise error
        finally:
            # Revenir à la branche d'origine si nécessaire
            if branch_changed:
                try:
                    git.checkout(current_branch)
                except GitCommandError as e:
                    logger.error(f"Erreur lors du retour à la branche d'origine: {str(e)}")

@safe_git_command
def apply_stash(repo: Repo, stash_id: str, delete_after: bool = True) -> bool:
    """
    Applique un stash existant.
    
    Args:
        repo: Instance du dépôt Git
        stash_id: ID du stash à appliquer
        delete_after: Si True, supprime le stash après l'avoir appliqué
        
    Returns:
        True si le stash a été appliqué avec succès
    """
    git = Git(repo.working_dir)
    recovery = RecoveryManager(repo)
    
    with recovery.safe_operation("apply_stash"):
        # Sauvegarder l'état actuel
        recovery.save_state("pre_stash_apply")
        
        # Appliquer le stash
        git.stash("apply", stash_id)
        
        # Supprimer le stash si demandé
        if delete_after:
            git.stash("drop", stash_id)
        
        return True

@safe_git_command
def stash_changes(repo: Repo, message: Optional[str] = None, include_untracked: bool = True) -> Optional[str]:
    """
    Crée un stash avec les modifications actuelles.
    
    Args:
        repo: Instance du dépôt Git
        message: Message pour le stash
        include_untracked: Si True, inclut les fichiers non suivis
        
    Returns:
        ID du stash créé ou None si aucun changement à sauvegarder
    """
    git = Git(repo.working_dir)
    
    # Vérifier s'il y a des changements à sauvegarder
    if not repo.is_dirty(untracked_files=include_untracked):
        return None
    
    # Préparer la commande
    stash_args = ["save"]
    if include_untracked:
        stash_args.append("--include-untracked")
    if message:
        stash_args.append(message)
    
    # Créer le stash
    result = git.stash(*stash_args)
    
    # Vérifier si le stash a été créé
    if result.startswith("No local changes to save"):
        return None
    
    # Récupérer l'ID du stash
    stash_list = git.stash("list")
    if stash_list:
        stash_id = stash_list.splitlines()[0].split(":")[0].strip()
        return stash_id
    
    return None
