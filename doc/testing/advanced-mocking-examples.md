# Techniques Avancées de Mocking pour les Tests GitMove

Ce document présente des techniques avancées de mocking pour tester efficacement le projet GitMove, en particulier pour gérer les dépendances complexes et les interactions avec Git.

## Mocking des Commandes Git

GitMove interagit fortement avec Git via GitPython, ce qui peut rendre les tests difficiles. Voici comment mocker efficacement ces interactions.

### Mocking simple d'une commande Git

```python
from unittest.mock import patch, MagicMock
import pytest
from git import GitCommandError

def test_branch_deletion_success():
    # Arrange
    repo_mock = MagicMock()
    git_mock = MagicMock()
    repo_mock.git = git_mock
    
    branch_manager = BranchManager(repo_mock, MagicMock())
    
    # Act
    result = branch_manager.clean_merged_branches(
        branches=[{"name": "feature/test", "is_remote": False}]
    )
    
    # Assert
    git_mock.branch.assert_called_once_with("-d", "feature/test")
    assert "feature/test" in result["cleaned_branches"]
    assert result["cleaned_count"] == 1

def test_branch_deletion_failure():
    # Arrange
    repo_mock = MagicMock()
    git_mock = MagicMock()
    repo_mock.git = git_mock
    
    # Simuler une erreur lors de la suppression
    git_mock.branch.side_effect = GitCommandError("branch -d feature/test", 128)
    
    branch_manager = BranchManager(repo_mock, MagicMock())
    
    # Act
    result = branch_manager.clean_merged_branches(
        branches=[{"name": "feature/test", "is_remote": False}]
    )
    
    # Assert
    git_mock.branch.assert_called_once_with("-d", "feature/test")
    assert "feature/test" in result["failed_branches"]
    assert result["failed_count"] == 1
```

### Mocking complexe avec contextes différents

Parfois, vous devez simuler des comportements Git différents selon le contexte :

```python
def test_sync_with_conflicts_then_resolution():
    # Arrange
    repo_mock = MagicMock()
    git_mock = MagicMock()
    repo_mock.git = git_mock
    config_mock = MagicMock()
    config_mock.get_value.return_value = "main"
    
    # Créer un compteur pour suivre le nombre d'appels
    call_count = {"merge": 0}
    
    # Simuler un comportement différent selon le nombre d'appels
    def merge_side_effect(*args, **kwargs):
        if call_count["merge"] == 0:
            call_count["merge"] += 1
            raise GitCommandError("merge conflict", 128)
        else:
            return "Merge successful"
    
    git_mock.merge.side_effect = merge_side_effect
    
    # Act - Premier appel (échec avec conflit)
    sync_manager = SyncManager(repo_mock, config_mock)
    
    with patch("gitmove.core.sync_manager.is_branch_merged", return_value=False):
        with patch("gitmove.core.sync_manager.get_branch_divergence", return_value=(2, 3)):
            # Simuler la vérification de l'état de synchronisation
            sync_manager.check_sync_status = MagicMock()
            sync_manager.check_sync_status.return_value = {
                "is_synced": False,
                "branch": "feature/test",
                "target": "main"
            }
            
            # Premier appel - devrait échouer avec conflit
            result1 = sync_manager.sync_with_main("feature/test", strategy="merge")
            
            # Deuxième appel - devrait réussir
            result2 = sync_manager.sync_with_main("feature/test", strategy="merge")
    
    # Assert
    assert result1["status"] == "conflict_occurred"
    assert result2["status"] == "synchronized"
```

## Mocking des Classes

Parfois, vous devez mocker des classes entières plutôt que des méthodes individuelles :

```python
@patch("gitmove.core.sync_manager.ConflictDetector")
@patch("gitmove.core.sync_manager.RecoveryManager")
def test_sync_manager_initialization(recovery_mock, conflict_detector_mock):
    # Arrange
    repo_mock = MagicMock()
    config_mock = MagicMock()
    
    # Les constructeurs retournent des instances mock
    recovery_instance = MagicMock()
    conflict_detector_instance = MagicMock()
    
    recovery_mock.return_value = recovery_instance
    conflict_detector_mock.return_value = conflict_detector_instance
    
    # Act
    sync_manager = SyncManager(repo_mock, config_mock)
    
    # Assert
    assert sync_manager.recovery == recovery_instance
    assert sync_manager.conflict_detector == conflict_detector_instance
    
    # Vérifier que les constructeurs ont été appelés avec les bons arguments
    recovery_mock.assert_called_once_with(repo_mock)
    conflict_detector_mock.assert_called_once_with(repo_mock, config_mock)
```

## Mocking des Exceptions Chaînées

GitMove utilise parfois des exceptions chaînées pour conserver le contexte d'erreur :

```python
@patch("gitmove.exceptions.convert_git_error")
def test_sync_with_converted_exception(convert_mock):
    # Arrange
    repo_mock = MagicMock()
    git_mock = MagicMock()
    repo_mock.git = git_mock
    
    # Simuler une erreur Git
    original_error = GitCommandError("merge", 128)
    
    # L'exception convertie
    converted_error = MergeConflictError("Conflit détecté", original_error=original_error)
    
    # Le convertisseur d'exceptions retourne l'exception convertie
    convert_mock.return_value = converted_error
    
    # Simuler l'échec de fusion
    git_mock.merge.side_effect = original_error
    
    # Act/Assert
    sync_manager = SyncManager(repo_mock, MagicMock())
    
    # La fonction devrait convertir l'exception GitCommandError en MergeConflictError
    with pytest.raises(MergeConflictError) as excinfo:
        sync_manager._perform_merge("feature/test", "main")
    
    # Vérifier que l'exception est bien celle retournée par convert_git_error
    assert excinfo.value == converted_error
    
    # Vérifier que convert_git_error a été appelé avec la bonne exception
    convert_mock.assert_called_once_with(original_error, ANY)
```

## Mocking des Méthodes de Classe

Pour mocker une méthode de classe (`@classmethod`) :

```python
def test_env_config_loader_class_method():
    # Arrange
    base_config = {"general": {"main_branch": "main"}}
    env_vars = {
        "GITMOVE_GENERAL_VERBOSE": "true",
        "GITMOVE_CLEAN_AUTO_CLEAN": "true"
    }
    
    # Patch la méthode _merge_config_value directement sur la classe
    with patch.object(EnvConfigManager, '_merge_config_value') as merge_mock:
        # Simuler le comportement de merge_config_value
        def side_effect(config, key, value):
            if key == "general_verbose":
                config.setdefault("general", {})["verbose"] = True
            elif key == "clean_auto_clean":
                config.setdefault("clean", {})["auto_clean"] = True
            return config
        
        merge_mock.side_effect = side_effect
        
        # Act
        with patch.dict(os.environ, env_vars, clear=True):
            result = EnvConfigManager.load_config(base_config)
    
    # Assert
    assert merge_mock.call_count == 2
    assert result["general"]["main_branch"] == "main"
    assert result["general"]["verbose"] is True
    assert result["clean"]["auto_clean"] is True
```

## Mocking des Entrées/Sorties Fichier

Mocker les opérations sur les fichiers est crucial pour les tests de configuration et de repo Git :

```python
@patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
@patch("toml.load")
def test_config_load_from_file(toml_load_mock, mock_file):
    # Arrange
    config_data = {
        "general": {"main_branch": "main"},
        "clean": {"auto_clean": False}
    }
    toml_load_mock.return_value = config_data
    
    config = Config()
    
    # Act
    config.load_from_file("/fake/path/config.toml")
    
    # Assert
    mock_file.assert_called_once_with("/fake/path/config.toml", "r", encoding="utf-8")
    toml_load_mock.assert_called_once()
    assert config.config == config_data
```

## Mocking des Opérations sur les Répertoires

Pour les tests impliquant des opérations sur les répertoires :

```python
@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
@patch("toml.dump")
def test_config_save_creates_directory(toml_dump_mock, mock_file, makedirs_mock):
    # Arrange
    config = Config()
    config.config = {"general": {"main_branch": "main"}}
    save_path = "/fake/directory/config.toml"
    
    # Act
    config.save(save_path)
    
    # Assert
    makedirs_mock.assert_called_once_with(os.path.dirname(save_path), exist_ok=True)
    mock_file.assert_called_once_with(save_path, "w", encoding="utf-8")
    toml_dump_mock.assert_called_once_with(config.config, mock_file())
```

## Mocking des Attributs Dynamiques

Pour les tests avec des objets qui créent des attributs dynamiquement :

```python
def test_dynamic_attributes():
    # Arrange
    mock_obj = MagicMock()
    
    # Simuler un comportement dynamique
    mock_attrs = {
        'heads': ['main', 'develop', 'feature/test'],
        'active_branch.name': 'feature/test',
        'is_dirty.return_value': False,
        'remotes.origin.refs': ['origin/main', 'origin/develop'],
    }
    
    # Configurer le mock avec des attributs dynamiques
    for attr_path, value in mock_attrs.items():
        parts = attr_path.split('.')
        current = mock_obj
        
        for part in parts[:-1]:
            if not hasattr(current, part):
                setattr(current, part, MagicMock())
            current = getattr(current, part)
        
        # Définir la valeur finale
        final_part = parts[-1]
        setattr(current, final_part, value)
    
    # Act/Assert
    assert mock_obj.active_branch.name == 'feature/test'
    assert not mock_obj.is_dirty()
    assert 'main' in mock_obj.heads
```

## Mocking des Contextes

Pour les tests de gestionnaires de contexte (`with` statements) :

```python
def test_safe_operation_context():
    # Arrange
    repo_mock = MagicMock()
    recovery_manager = RecoveryManager(repo_mock)
    
    # Mock la méthode save_state
    recovery_manager.save_state = MagicMock()
    
    # Mock la méthode restore_state
    recovery_manager.restore_state = MagicMock()
    
    # Act
    try:
        with recovery_manager.safe_operation("test_operation"):
            # Simuler une opération normale
            pass
        
        # Assert - pas de restauration en cas de succès
        recovery_manager.save_state.assert_called_once_with("test_operation")
        recovery_manager.restore_state.assert_not_called()
        
        # Réinitialiser les mocks pour le test suivant
        recovery_manager.save_state.reset_mock()
        recovery_manager.restore_state.reset_mock()
        
        # Test avec une exception
        with pytest.raises(ValueError):
            with recovery_manager.safe_operation("test_operation"):
                raise ValueError("Test error")
        
        # Assert - restauration en cas d'erreur
        recovery_manager.save_state.assert_called_once_with("test_operation")
        recovery_manager.restore_state.assert_called_once_with("test_operation")
    except Exception as e:
        pytest.fail(f"Unexpected exception: {str(e)}")
```

## Mocking de Plusieurs Appels Successifs

Pour simuler différents comportements lors d'appels successifs :

```python
def test_multiple_fetch_attempts():
    # Arrange
    repo_mock = MagicMock()
    git_mock = MagicMock()
    repo_mock.git = git_mock
    
    # Premier appel échoue, deuxième réussit
    git_mock.fetch.side_effect = [
        GitCommandError("fetch failed", 128),
        "Success"
    ]
    
    # Act/Assert
    sync_manager = SyncManager(repo_mock, MagicMock())
    
    # Premier appel - devrait échouer
    with pytest.raises(GitError):
        sync_manager._fetch_updates()
    
    # Réinitialiser le compteur d'appels pour le test
    git_mock.fetch.side_effect = [
        "Success"
    ]
    
    # Deuxième appel - devrait réussir
    result = sync_manager._fetch_updates()
    assert result is True
```

## Utilisation des Espions (Spies)

Les espions permettent de vérifier les appels sans remplacer complètement l'implémentation :

```python
from unittest.mock import create_autospec

def test_with_spy():
    # Arrange
    original_function = some_module.some_function
    
    # Créer un espion qui appelle la fonction originale mais enregistre les appels
    spy = create_autospec(original_function, wraps=original_function)
    some_module.some_function = spy
    
    # Act
    result = call_function_that_uses_some_function()
    
    # Assert
    spy.assert_called_once_with(expected_args)
    
    # Restaurer la fonction originale
    some_module.some_function = original_function
```

## Tests avec des Événements Asynchrones

Pour tester du code qui utilise des callbacks ou des événements :

```python
def test_async_operation():
    # Arrange
    repo_mock = MagicMock()
    manager = SomeManager(repo_mock)
    
    # Créer un Event pour synchroniser les threads
    import threading
    callback_called = threading.Event()
    callback_result = None
    
    def callback(result):
        nonlocal callback_result
        callback_result = result
        callback_called.set()
    
    # Act
    manager.perform_async_operation(callback)
    
    # Attendre que le callback soit appelé ou timeout après 5 secondes
    callback_called.wait(timeout=5)
    
    # Assert
    assert callback_called.is_set(), "Callback n'a pas été appelé"
    assert callback_result == expected_result
```

## Mocking de Propriétés

Pour mocker des propriétés Python (getters/setters) :

```python
class SomeClass:
    @property
    def some_property(self):
        return "original_value"

def test_property_mocking():
    # Créer un mock avec une propriété remplacée
    instance = SomeClass()
    
    # Utiliser patch.object pour mocker la propriété
    with patch.object(SomeClass, 'some_property', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = "mocked_value"
        
        # Act
        result = instance.some_property
        
        # Assert
        assert result == "mocked_value"
        mock_property.assert_called_once()
```

## Assertions Avancées pour les Mocks

Pour des assertions plus complexes sur les appels de mock :

```python
def test_advanced_mock_assertions():
    # Arrange
    mock_func = MagicMock()
    
    # Act
    mock_func(1, 2, key="value")
    mock_func("string", key="other")
    
    # Assert - vérifier le nombre d'appels
    assert mock_func.call_count == 2
    
    # Vérifier les appels spécifiques
    mock_func.assert_any_call(1, 2, key="value")
    
    # Vérifier les arguments de tous les appels
    calls = mock_func.call_args_list
    assert calls[0] == call(1, 2, key="value")
    assert calls[1] == call("string", key="other")
    
    # Vérifier l'ordre des appels
    mock_func.assert_has_calls([
        call(1, 2, key="value"),
        call("string", key="other")
    ], any_order=False)
    
    # Vérifier qu'il n'y a pas eu d'autres appels
    mock_func.assert_has_calls([
        call(1, 2, key="value"),
        call("string", key="other")
    ], any_order=True)
    assert len(mock_func.mock_calls) == 2
```

## Combinaison de Mocks et d'Objets Réels

Il est parfois utile de combiner des objets réels et des mocks :

```python
def test_partial_mocking():
    # Créer un objet réel
    real_config = Config()
    real_config.set_value("general.main_branch", "main")
    
    # Créer un repo mock
    repo_mock = MagicMock()
    
    # Créer un objet réel avec une dépendance mockée
    branch_manager = BranchManager(repo_mock, real_config)
    
    # Mock seulement certaines méthodes
    branch_manager._get_branch_info = MagicMock()
    branch_manager._get_branch_info.return_value = {
        "name": "feature/test",
        "is_merged": True
    }
    
    # Act
    result = branch_manager.get_branch_status("feature/test")
    
    # Assert
    assert result["name"] == "feature/test"
    assert result["is_merged"] is True
    
    # L'objet réel est toujours utilisé pour la configuration
    assert branch_manager.main_branch == "main"
```

## Mocking des Dépendances Imbriquées

Pour des dépendances profondément imbriquées :

```python
def test_nested_dependencies():
    # Crée un mock profondément imbriqué
    def create_nested_mock(**kwargs):
        mock = MagicMock()
        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(mock, key, create_nested_mock(**value))
            else:
                setattr(mock, key, value)
        return mock
    
    # Créer un repo avec des dépendances imbriquées
    repo_mock = create_nested_mock(
        git=MagicMock(),
        working_dir="/fake/path",
        active_branch={"name": "feature/test"},
        is_dirty=lambda: False,
        heads=["main", "feature/test"],
        remotes={
            "origin": {
                "refs": ["origin/main", "origin/feature/test"]
            }
        }
    )
    
    # Act
    result = some_function_that_uses_repo(repo_mock)
    
    # Assert
    assert result == expected_result
```

Ces techniques de mocking avancées vous permettront de tester efficacement les fonctionnalités complexes de GitMove, en particulier celles qui interagissent avec Git ou d'autres dépendances externes.