"""
Tests pour les utilitaires de commandes Git.

Ce module teste les fonctions du module git_commands.
"""

import os
import pytest
from git.exc import GitCommandError

from gitmove.utils.git_commands import (
    get_repo,
    get_current_branch,
    get_main_branch,
    is_branch_merged,
    get_branch_last_commit_date,
    get_branch_age,
    get_branch_commit_count,
    get_tracking_branch,
    get_branch_divergence,
    get_common_ancestor,
    get_modified_files,
    fetch_updates,
    delete_local_branch,
    delete_remote_branch,
    merge_branch,
    rebase_branch,
)


def test_get_repo(temp_dir):
    """Teste la récupération d'une instance de dépôt Git."""
    # Initialiser un dépôt dans le répertoire temporaire
    os.chdir(temp_dir)
    os.system("git init")
    
    # Tester avec le répertoire courant
    repo = get_repo()
    assert repo is not None
    assert repo.git_dir is not None
    
    # Tester avec un chemin spécifique
    repo = get_repo(temp_dir)
    assert repo is not None
    assert repo.git_dir is not None
    
    # Tester avec un chemin invalide
    with pytest.raises(ValueError):
        get_repo("/path/that/does/not/exist")


def test_get_current_branch(configured_git_repo):
    """Teste la récupération de la branche courante."""
    # La branche par défaut est 'main'
    branch = get_current_branch(configured_git_repo)
    assert branch == "main"
    
    # Changer de branche et vérifier
    configured_git_repo.git.checkout("-b", "test-branch")
    branch = get_current_branch(configured_git_repo)
    assert branch == "test-branch"


def test_get_main_branch(multi_branch_repo):
    """Teste la détection de la branche principale."""
    # Le dépôt de test utilise 'main' comme branche principale
    main_branch = get_main_branch(multi_branch_repo)
    assert main_branch == "main"


def test_is_branch_merged(multi_branch_repo):
    """Teste la détection des branches fusionnées."""
    # feature/b a été fusionnée dans main
    assert is_branch_merged(multi_branch_repo, "feature/b", "main") is True
    
    # feature/a n'a pas été fusionnée
    assert is_branch_merged(multi_branch_repo, "feature/a", "main") is False


def test_get_branch_last_commit_date(multi_branch_repo):
    """Teste la récupération de la date du dernier commit."""
    # Vérifier que la date est au format attendu (YYYY-MM-DD)
    date = get_branch_last_commit_date(multi_branch_repo, "main")
    assert len(date) == 10  # Format YYYY-MM-DD
    assert date[4] == "-" and date[7] == "-"  # Vérifier les séparateurs


def test_get_branch_age(multi_branch_repo):
    """Teste le calcul de l'âge d'une branche."""
    # L'âge est en jours, il devrait être un entier non négatif
    age = get_branch_age(multi_branch_repo, "main")
    assert isinstance(age, int)
    assert age >= 0


def test_get_branch_commit_count(multi_branch_repo):
    """Teste le comptage des commits dans une branche."""
    # Compter tous les commits dans main
    count = get_branch_commit_count(multi_branch_repo, "main")
    assert count >= 3  # Initial + feature/b merge + release/1.0 merge
    
    # Compter uniquement les commits propres à feature/a
    count = get_branch_commit_count(multi_branch_repo, "feature/a", "main")
    assert count == 1  # Un seul commit spécifique à feature/a


def test_get_branch_divergence(multi_branch_repo):
    """Teste le calcul de la divergence entre deux branches."""
    # Calculer la divergence entre feature/a et main
    ahead, behind = get_branch_divergence(multi_branch_repo, "feature/a", "main")
    
    # feature/a devrait être en avance d'au moins un commit
    assert ahead >= 1
    
    # Et en retard d'au moins un commit (les merges dans main)
    assert behind >= 1


def test_get_common_ancestor(multi_branch_repo):
    """Teste la recherche de l'ancêtre commun."""
    # Trouver l'ancêtre commun entre feature/a et main
    ancestor = get_common_ancestor(multi_branch_repo, "feature/a", "main")
    
    # Il doit y avoir un ancêtre commun
    assert ancestor is not None
    assert len(ancestor) > 0  # SHA non vide


def test_get_modified_files(multi_branch_repo):
    """Teste la récupération des fichiers modifiés."""
    # Trouver l'ancêtre commun entre feature/a et main
    ancestor = get_common_ancestor(multi_branch_repo, "feature/a", "main")
    
    # Obtenir les fichiers modifiés dans feature/a depuis l'ancêtre
    modified_files = get_modified_files(multi_branch_repo, ancestor, "feature/a")
    
    # feature_a.txt devrait être dans la liste
    assert "feature_a.txt" in modified_files


def test_delete_local_branch(multi_branch_repo):
    """Teste la suppression d'une branche locale."""
    # Créer une branche de test
    multi_branch_repo.git.checkout("-b", "test-delete-branch")
    
    # Revenir à main
    multi_branch_repo.git.checkout("main")
    
    # Supprimer la branche
    result = delete_local_branch(multi_branch_repo, "test-delete-branch")
    
    assert result is True
    
    # Vérifier que la branche n'existe plus
    branches = [b.name for b in multi_branch_repo.heads]
    assert "test-delete-branch" not in branches


def test_merge_branch(multi_branch_repo):
    """Teste la fusion d'une branche."""
    # Créer une branche de test
    multi_branch_repo.git.checkout("-b", "test-merge-source")
    
    # Ajouter un fichier dans cette branche
    repo_path = multi_branch_repo.working_dir
    with open(os.path.join(repo_path, "merge_test_file.txt"), "w") as f:
        f.write("Test content for merge\n")
    
    multi_branch_repo.git.add("merge_test_file.txt")
    multi_branch_repo.git.commit("-m", "Add file for merge test", author="Test User <test@example.com>")
    
    # Revenir à main
    multi_branch_repo.git.checkout("main")
    
    # Fusionner la branche
    result = merge_branch(multi_branch_repo, "test-merge-source")
    
    assert result["success"] is True
    assert "test-merge-source" in result["message"]
    
    # Vérifier que le fichier est présent dans main
    assert os.path.exists(os.path.join(repo_path, "merge_test_file.txt"))


def test_rebase_branch(multi_branch_repo):
    """Teste le rebase d'une branche."""
    # Créer une branche de test basée sur un commit antérieur
    multi_branch_repo.git.checkout("main~2")  # Deux commits avant la tête de main
    multi_branch_repo.git.checkout("-b", "test-rebase-branch")
    
    # Ajouter un fichier dans cette branche
    repo_path = multi_branch_repo.working_dir
    with open(os.path.join(repo_path, "rebase_test_file.txt"), "w") as f:
        f.write("Test content for rebase\n")
    
    multi_branch_repo.git.add("rebase_test_file.txt")
    multi_branch_repo.git.commit("-m", "Add file for rebase test", author="Test User <test@example.com>")
    
    # Rebaser sur main
    result = rebase_branch(multi_branch_repo, "main")
    
    # Le résultat peut être success=True ou avoir des conflits
    if result["success"]:
        assert "main" in result["message"]
        
        # Vérifier que le fichier est toujours présent
        assert os.path.exists(os.path.join(repo_path, "rebase_test_file.txt"))