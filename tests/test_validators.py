"""
Tests pour les validateurs Git.

Ce module teste les fonctions du module git_repo_validator.
"""

import os
import pytest
from git.repo import Repo

from gitmove.validators.git_repo_validator import (
    validate_git_repo,
    validate_branch_exists,
    validate_clean_working_tree,
    validate_branch_permission,
    validate_branch_naming,
    validate_safe_operation,
    check_repo_state,
)


def test_validate_git_repo(configured_git_repo):
    """Teste la validation d'un dépôt Git."""
    # Un dépôt valide
    assert validate_git_repo(configured_git_repo) is True
    
    # Un objet None
    with pytest.raises(ValueError, match="None"):
        validate_git_repo(None)
    
    # Un objet qui n'est pas un dépôt Git
    with pytest.raises(ValueError, match="instance Repo"):
        validate_git_repo("not_a_repo")


def test_validate_branch_exists(multi_branch_repo):
    """Teste la validation de l'existence d'une branche."""
    # Une branche qui existe
    assert validate_branch_exists(multi_branch_repo, "main") is True
    assert validate_branch_exists(multi_branch_repo, "feature/a") is True
    
    # Une branche qui n'existe pas
    with pytest.raises(ValueError, match="n'existe pas"):
        validate_branch_exists(multi_branch_repo, "non_existent_branch")


def test_validate_clean_working_tree(configured_git_repo):
    """Teste la validation d'un répertoire de travail propre."""
    # Un répertoire propre
    assert validate_clean_working_tree(configured_git_repo) is True
    
    # Modifier un fichier pour rendre le répertoire sale
    repo_path = configured_git_repo.working_dir
    with open(os.path.join(repo_path, "README.md"), "a") as f:
        f.write("\nModified for test\n")
    
    # Le répertoire n'est plus propre
    with pytest.raises(ValueError, match="changements non commités"):
        validate_clean_working_tree(configured_git_repo)
    
    # Mais avec allow_untracked=True, un nouveau fichier non suivi serait autorisé
    with open(os.path.join(repo_path, "untracked_file.txt"), "w") as f:
        f.write("This is an untracked file\n")
    
    # Le fichier modifié (README.md) devrait toujours causer une erreur
    with pytest.raises(ValueError, match="changements non commités"):
        validate_clean_working_tree(configured_git_repo, allow_untracked=True)
    
    # Restaurer le fichier README.md
    configured_git_repo.git.checkout("--", "README.md")
    
    # Maintenant, seul le fichier non suivi est présent
    # Cela devrait passer avec allow_untracked=True
    assert validate_clean_working_tree(configured_git_repo, allow_untracked=True) is True
    
    # Mais pas avec allow_untracked=False
    with pytest.raises(ValueError, match="changements non commités"):
        validate_clean_working_tree(configured_git_repo, allow_untracked=False)
    
    # Nettoyer
    os.unlink(os.path.join(repo_path, "untracked_file.txt"))


def test_validate_branch_permission(configured_git_repo):
    """Teste la validation des permissions de branche."""
    # Une branche non protégée
    assert validate_branch_permission(configured_git_repo, "feature/test") is True
    
    # Une branche protégée (main)
    with pytest.raises(ValueError, match="protégée"):
        validate_branch_permission(configured_git_repo, "main")
    
    # Une branche correspondant à un pattern protégé
    with pytest.raises(ValueError, match="protégée"):
        validate_branch_permission(configured_git_repo, "release/1.0")
    
    # Avec une liste personnalisée de branches protégées
    assert validate_branch_permission(configured_git_repo, "main", []) is True
    with pytest.raises(ValueError, match="protégée"):
        validate_branch_permission(configured_git_repo, "custom-protected", ["custom-*"])


def test_validate_branch_naming(configured_git_repo):
    """Teste la validation du nommage des branches."""
    # Noms valides
    assert validate_branch_naming("feature/new-login") is True
    assert validate_branch_naming("bugfix/issue-123") is True
    assert validate_branch_naming("main") is True
    
    # Noms invalides (caractères spéciaux)
    with pytest.raises(ValueError, match="caractères non autorisés"):
        validate_branch_naming("feature/invalid#branch")
    
    # Nom trop long
    long_name = "feature/" + "x" * 100
    with pytest.raises(ValueError, match="trop long"):
        validate_branch_naming(long_name)
    
    # Pattern non autorisé
    with pytest.raises(ValueError, match="conventions de nommage"):
        validate_branch_naming("random-branch", ["feature/*", "bugfix/*"])


def test_validate_safe_operation(configured_git_repo):
    """Teste la validation de la sécurité des opérations."""
    # Créer une branche de test
    configured_git_repo.git.checkout("-b", "test-branch")
    
    # Revenir à main
    configured_git_repo.git.checkout("main")
    
    # Opération sûre (supprimer une branche qui n'est pas la courante)
    assert validate_safe_operation(configured_git_repo, "delete", "test-branch") is True
    
    # Opération non sûre (supprimer la branche courante)
    with pytest.raises(ValueError, match="branche courante"):
        validate_safe_operation(configured_git_repo, "delete", "main")
    
    # Opération dangereuse (reset) sans force
    with pytest.raises(ValueError, match="destructrice"):
        validate_safe_operation(configured_git_repo, "reset", "main")
    
    # Opération dangereuse (reset) avec force
    assert validate_safe_operation(configured_git_repo, "reset", "main", force=True) is True


def test_check_repo_state(multi_branch_repo):
    """Teste la vérification de l'état du dépôt."""
    # Obtenir l'état du dépôt
    state = check_repo_state(multi_branch_repo)
    
    # Vérifier les informations de base
    assert "current_branch" in state
    assert state["current_branch"] == "main"
    assert "is_clean" in state
    assert isinstance(state["is_clean"], bool)
    
    # Vérifier les informations sur le stash
    assert "has_stashed" in state
    assert isinstance(state["has_stashed"], bool)
    assert "stash_count" in state
    assert isinstance(state["stash_count"], int)
    
    # Vérifier les informations sur le remote
    assert "has_remote" in state
    # Note : dans notre fixture, il n'y a pas de remote configuré
    assert state["has_remote"] is False