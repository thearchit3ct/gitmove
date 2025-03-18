# Exemples de Tests avec pytest pour GitMove

Ce document fournit des exemples pratiques pour écrire des tests avec pytest pour le projet GitMove. Ces exemples couvrent différents scénarios de test et peuvent être utilisés comme référence pour ajouter de nouveaux tests.

## Paramétrage des Tests

Les tests paramétrés permettent d'exécuter la même fonction de test avec différentes entrées. Voici un exemple de test paramétré pour le module `EnvConfigManager` :

```python
import pytest
from gitmove.env_config import EnvConfigManager

@pytest.mark.parametrize("input_value,expected_output", [
    ("true", True),
    ("false", False),
    ("yes", True),
    ("no", False),
    ("1", True),
    ("0", False),
    ("42", 42),
    ("3.14", 3.14),
    ('["a", "b", "c"]', ["a", "b", "c"]),
    ('{"key": "value"}', {"key": "value"}),
    ("simple string", "simple string"),
])
def test_convert_value(input_value, expected_output):
    """Tester la conversion de différentes valeurs d'entrée."""
    # Act
    result = EnvConfigManager._convert_value(input_value)
    
    # Assert
    assert result == expected_output
    assert type(result) == type(expected_output)
```

## Tests avec Mocks

Les mocks permettent de simuler des dépendances externes. Voici un exemple de test utilisant des mocks pour le module `SyncManager` :

```python
from unittest.mock import patch, MagicMock
from gitmove.core.sync_manager import SyncManager

def test_sync_with_main_already_synced():
    """Tester la synchronisation quand la branche est déjà à jour."""
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    config_mock.get_value.return_value = "main"
    
    sync_manager = SyncManager(repo_mock, config_mock)
    sync_manager.check_sync_status = MagicMock()
    sync_manager.check_sync_status.return_value = {
        "is_synced": True,
        "branch": "feature/test",
        "target": "main",
        "ahead_commits": 2,
        "behind_commits": 0,
        "message": "La branche est à jour avec la branche principale"
    }
    
    # Act
    result = sync_manager.sync_with_main("feature/test")
    
    # Assert
    assert result["status"] == "up-to-date"
    assert result["branch"] == "feature/test"
    assert result["target"] == "main"
    
    # Vérifier que check_sync_status a été appelé avec les bons arguments
    sync_manager.check_sync_status.assert_called_once_with("feature/test")
```

## Tests avec Fixtures

Les fixtures pytest permettent de préparer l'état de test et de le réutiliser dans plusieurs tests :

```python
import pytest
import tempfile
import os
from git import Repo
from gitmove.config import Config

@pytest.fixture
def temp_git_repo():
    """Fixture qui crée un dépôt Git temporaire pour les tests."""
    # Créer un répertoire temporaire
    temp_dir = tempfile.mkdtemp()
    
    # Initialiser un dépôt Git
    repo = Repo.init(temp_dir)
    git = repo.git
    
    # Configurer Git
    git.config('user.name', 'Test User')
    git.config('user.email', 'test@example.com')
    
    # Créer un commit initial
    readme_path = os.path.join(temp_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write('# Test Repository\n')
    
    git.add('README.md')
    git.commit('-m', 'Initial commit')
    
    # Rendre accessible pour le test
    yield {
        'repo': repo,
        'git': git,
        'path': temp_dir
    }
    
    # Nettoyer après le test
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except (PermissionError, OSError):
        pass

@pytest.fixture
def config():
    """Fixture qui crée une configuration de test."""
    config = Config()
    config.set_value('general.main_branch', 'main')
    config.set_value('clean.exclude_branches', ['develop'])
    return config

def test_branch_manager_get_current_branch(temp_git_repo, config):
    """Tester la récupération de la branche courante."""
    # Arrange
    from gitmove.core.branch_manager import BranchManager
    repo = temp_git_repo['repo']
    branch_manager = BranchManager(repo, config)
    
    # Act
    current_branch = branch_manager.get_current_branch()
    
    # Assert - le nom peut varier selon la version de Git (master ou main)
    assert current_branch in ['master', 'main']
```

## Tests d'Exceptions

Pour tester que des exceptions sont correctement levées :

```python
import pytest
from gitmove.core.branch_manager import BranchManager
from gitmove.exceptions import BranchError, MissingBranchError

def test_get_branch_status_non_existent(temp_git_repo, config):
    """Tester la récupération du statut d'une branche inexistante."""
    # Arrange
    repo = temp_git_repo['repo']
    branch_manager = BranchManager(repo, config)
    
    # Act/Assert
    with pytest.raises(ValueError) as excinfo:
        branch_manager.get_branch_status("non-existent-branch")
    
    # Vérifier le message d'erreur
    assert "n'existe pas" in str(excinfo.value)
```

## Tests d'Intégration

Les tests d'intégration vérifient l'interaction entre plusieurs composants :

```python
import os
import tempfile
import shutil
from git import Repo
from gitmove import get_manager

def test_complete_workflow_integration():
    """Test d'intégration pour un workflow complet."""
    # Créer un répertoire temporaire
    test_dir = tempfile.mkdtemp()
    
    try:
        # Initialiser un dépôt Git
        repo = Repo.init(test_dir)
        git = repo.git
        
        # Configurer Git
        git.config('user.name', 'Test User')
        git.config('user.email', 'test@example.com')
        
        # Créer un commit initial
        readme_path = os.path.join(test_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write('# Test Repository\n')
        
        git.add('README.md')
        git.commit('-m', 'Initial commit')
        
        # S'assurer que la branche principale est "main"
        current_branch = repo.active_branch.name
        if current_branch != 'main':
            git.branch('-m', current_branch, 'main')
        
        # Obtenir les gestionnaires
        managers = get_manager(test_dir)
        branch_manager = managers['branch_manager']
        sync_manager = managers['sync_manager']
        
        # Créer une branche de fonctionnalité
        git.checkout('-b', 'feature/test')
        
        # Ajouter un commit dans la branche
        test_file = os.path.join(test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('Test content\n')
        
        git.add('test.txt')
        git.commit('-m', 'Add test file')
        
        # Revenir à main et ajouter un autre commit
        git.checkout('main')
        main_file = os.path.join(test_dir, 'main.txt')
        with open(main_file, 'w') as f:
            f.write('Main content\n')
        
        git.add('main.txt')
        git.commit('-m', 'Add main file')
        
        # Vérifier la synchronisation
        git.checkout('feature/test')
        status = sync_manager.check_sync_status('feature/test')
        assert not status['is_synced']
        assert status['behind_commits'] == 1
        
        # Synchroniser la branche
        result = sync_manager.sync_with_main('feature/test')
        assert result['status'] == 'synchronized'
        
        # Vérifier que la branche est maintenant à jour
        status_after = sync_manager.check_sync_status('feature/test')
        assert status_after['is_synced']
        assert status_after['behind_commits'] == 0
        
        # Revenir à main et fusionner la branche
        git.checkout('main')
        git.merge('feature/test', '--no-ff', '-m', 'Merge feature/test')
        
        # Nettoyer les branches fusionnées
        merged_branches = branch_manager.find_merged_branches()
        branch_names = [b['name'] for b in merged_branches]
        assert 'feature/test' in branch_names
        
        result = branch_manager.clean_merged_branches(branches=merged_branches)
        assert 'feature/test' in result['cleaned_branches']
        
        # Vérifier que la branche a été supprimée
        branches_after = branch_manager.list_branches()
        branch_names_after = [b['name'] for b in branches_after]
        assert 'feature/test' not in branch_names_after
    
    finally:
        # Nettoyer
        shutil.rmtree(test_dir)
```

## Tests avec Marqueurs

Les marqueurs pytest permettent de catégoriser les tests et de les exécuter sélectivement :

```python
import pytest

@pytest.mark.slow
def test_something_slow():
    """Un test lent qui ne doit pas être exécuté par défaut."""
    # ...

@pytest.mark.integration
def test_something_integration():
    """Un test d'intégration."""
    # ...

@pytest.mark.parametrize("input_value", ["value1", "value2"])
def test_with_different_inputs(input_value):
    """Un test avec différentes entrées."""
    # ...
```

Pour exécuter des tests avec un marqueur spécifique :

```bash
pytest -m slow
pytest -m "not slow"
pytest -m "integration or slow"
```

## Couverture de Code

Pour exécuter les tests avec mesure de la couverture de code :

```bash
pytest --cov=gitmove --cov-report=term --cov-report=html tests/
```

Cela générera un rapport de couverture dans le terminal et un rapport HTML dans le répertoire `htmlcov/`.

## Bonnes Pratiques

1. **Nommage des Tests** : Utilisez des noms descriptifs qui indiquent clairement ce qui est testé.
2. **Structure AAA** : Structurez vos tests selon le modèle Arrange-Act-Assert.
3. **Isolation** : Chaque test doit être indépendant des autres.
4. **Nettoyer les Ressources** : Utilisez des fixtures ou des blocs `try/finally` pour nettoyer les ressources.
5. **Tests Paramétrés** : Utilisez `@pytest.mark.parametrize` pour tester plusieurs cas d'entrée.
6. **Mocks** : N'utilisez des mocks que lorsque c'est nécessaire et documentez leur comportement.
7. **Assertions Claires** : Utilisez des assertions explicites avec des messages d'erreur descriptifs.