"""
Fixtures et configuration pour les tests GitMove.

Ce module définit des fixtures pytest réutilisables pour les tests.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from git import Actor, Repo

from gitmove.config import Config


@pytest.fixture
def temp_dir():
    """Crée un répertoire temporaire pour les tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Nettoyer après le test
    shutil.rmtree(temp_path)


@pytest.fixture
def git_repo(temp_dir):
    """
    Crée un dépôt Git temporaire pour les tests.
    
    Le dépôt contient :
    - une branche main avec quelques commits
    - une configuration Git de base
    """
    # Initialiser le dépôt
    repo_path = os.path.join(temp_dir, "test_repo")
    os.makedirs(repo_path)
    repo = Repo.init(repo_path)
    
    # Configurer l'auteur
    author = Actor("Test User", "test@example.com")
    
    # Créer un premier commit (fichier README)
    readme_path = os.path.join(repo_path, "README.md")
    with open(readme_path, "w") as f:
        f.write("# Test Repository\n\nThis is a test repository for GitMove.")
    
    repo.git.add("README.md")
    repo.git.commit("-m", "Initial commit", author=str(author), committer=str(author))
    
    # Configurer la branche par défaut comme "main"
    repo.git.branch("-M", "main")
    
    yield repo
    
    # Le nettoyage est géré par la fixture temp_dir


@pytest.fixture
def configured_git_repo(git_repo):
    """
    Un dépôt Git avec la configuration GitMove.
    """
    repo_path = git_repo.working_dir
    
    # Créer un fichier de configuration GitMove
    config = Config()
    config.set_value("general.main_branch", "main")
    config.save(os.path.join(repo_path, ".gitmove.toml"))
    
    return git_repo


@pytest.fixture
def multi_branch_repo(git_repo):
    """
    Un dépôt Git avec plusieurs branches dans différents états.
    
    Branches créées :
    - main : branche principale
    - feature/a : branche de fonctionnalité non fusionnée
    - feature/b : branche de fonctionnalité fusionnée
    - bugfix/x : branche de correction non fusionnée
    - release/1.0 : branche de release fusionnée
    """
    repo = git_repo
    repo_path = repo.working_dir
    
    # Auteur pour les commits
    author = Actor("Test User", "test@example.com")
    
    # Ajouter des commits supplémentaires sur main
    file_path = os.path.join(repo_path, "main_file.txt")
    with open(file_path, "w") as f:
        f.write("Content in main branch\n")
    
    repo.git.add("main_file.txt")
    repo.git.commit("-m", "Add file in main", author=str(author), committer=str(author))
    
    # Créer et configurer les branches
    
    # 1. feature/a - Non fusionnée
    repo.git.checkout("-b", "feature/a")
    file_path = os.path.join(repo_path, "feature_a.txt")
    with open(file_path, "w") as f:
        f.write("Feature A content\n")
    
    repo.git.add("feature_a.txt")
    repo.git.commit("-m", "Add feature A", author=str(author), committer=str(author))
    
    # 2. feature/b - Sera fusionnée
    repo.git.checkout("main")
    repo.git.checkout("-b", "feature/b")
    file_path = os.path.join(repo_path, "feature_b.txt")
    with open(file_path, "w") as f:
        f.write("Feature B content\n")
    
    repo.git.add("feature_b.txt")
    repo.git.commit("-m", "Add feature B", author=str(author), committer=str(author))
    
    # Fusionner feature/b dans main
    repo.git.checkout("main")
    repo.git.merge("feature/b", "--no-ff", "-m", "Merge feature B")
    
    # 3. bugfix/x - Non fusionnée
    repo.git.checkout("-b", "bugfix/x")
    file_path = os.path.join(repo_path, "bugfix_x.txt")
    with open(file_path, "w") as f:
        f.write("Bugfix X content\n")
    
    repo.git.add("bugfix_x.txt")
    repo.git.commit("-m", "Add bugfix X", author=str(author), committer=str(author))
    
    # 4. release/1.0 - Sera fusionnée
    repo.git.checkout("main")
    repo.git.checkout("-b", "release/1.0")
    file_path = os.path.join(repo_path, "release_file.txt")
    with open(file_path, "w") as f:
        f.write("Release 1.0 content\n")
    
    repo.git.add("release_file.txt")
    repo.git.commit("-m", "Add release 1.0 file", author=str(author), committer=str(author))
    
    # Fusionner release/1.0 dans main
    repo.git.checkout("main")
    repo.git.merge("release/1.0", "--no-ff", "-m", "Merge release 1.0")
    
    # Revenir à main
    repo.git.checkout("main")
    
    return repo


@pytest.fixture
def conflict_repo(git_repo):
    """
    Un dépôt Git avec des branches qui génèreront des conflits lors de la fusion.
    """
    repo = git_repo
    repo_path = repo.working_dir
    
    # Auteur pour les commits
    author = Actor("Test User", "test@example.com")
    
    # Créer un fichier qui sera modifié dans deux branches
    file_path = os.path.join(repo_path, "conflict_file.txt")
    with open(file_path, "w") as f:
        f.write("Original content\nLine 1\nLine 2\nLine 3\n")
    
    repo.git.add("conflict_file.txt")
    repo.git.commit("-m", "Add file for conflict testing", author=str(author), committer=str(author))
    
    # Créer une branche feature/conflict
    repo.git.checkout("-b", "feature/conflict")
    
    # Modifier le fichier dans feature/conflict
    with open(file_path, "w") as f:
        f.write("Original content\nLine 1 modified in feature\nLine 2\nLine 3\nFeature line\n")
    
    repo.git.add("conflict_file.txt")
    repo.git.commit("-m", "Modify file in feature branch", author=str(author), committer=str(author))
    
    # Revenir à main et modifier le même fichier
    repo.git.checkout("main")
    
    with open(file_path, "w") as f:
        f.write("Original content\nLine 1\nLine 2 modified in main\nLine 3\nMain line\n")
    
    repo.git.add("conflict_file.txt")
    repo.git.commit("-m", "Modify file in main branch", author=str(author), committer=str(author))
    
    return repo


@pytest.fixture
def gitmove_config():
    """Crée une instance de configuration GitMove pour les tests."""
    config = Config()
    config.set_value("general.main_branch", "main")
    config.set_value("clean.auto_clean", False)
    config.set_value("clean.exclude_branches", ["develop", "staging"])
    config.set_value("sync.default_strategy", "rebase")
    config.set_value("advice.rebase_threshold", 5)
    
    return config