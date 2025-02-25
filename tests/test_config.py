"""
Tests pour la gestion de la configuration.

Ce module teste les fonctionnalités de la classe Config.
"""

import os
import tempfile
import pytest
import toml

from gitmove.config import Config, DEFAULT_CONFIG


def test_init():
    """Teste l'initialisation de la configuration."""
    config = Config()
    
    # Vérifier que la configuration par défaut est utilisée
    assert config.config == DEFAULT_CONFIG
    assert config.config_path is None


def test_get_value():
    """Teste la récupération des valeurs de configuration."""
    config = Config()
    
    # Récupérer des valeurs existantes
    assert config.get_value("general.main_branch") == "main"
    assert config.get_value("clean.auto_clean") is False
    assert config.get_value("sync.default_strategy") == "rebase"
    
    # Récupérer une valeur inexistante
    assert config.get_value("non.existent.key") is None
    
    # Récupérer une valeur inexistante avec valeur par défaut
    assert config.get_value("non.existent.key", "default_value") == "default_value"


def test_set_value():
    """Teste la définition des valeurs de configuration."""
    config = Config()
    
    # Modifier une valeur existante
    config.set_value("general.main_branch", "master")
    assert config.get_value("general.main_branch") == "master"
    
    # Définir une nouvelle valeur
    config.set_value("custom.new_key", "new_value")
    assert config.get_value("custom.new_key") == "new_value"
    
    # Définir une valeur de type liste
    config.set_value("custom.list_value", [1, 2, 3])
    assert config.get_value("custom.list_value") == [1, 2, 3]


def test_save_and_load():
    """Teste l'enregistrement et le chargement de la configuration."""
    # Créer une configuration avec des valeurs personnalisées
    config = Config()
    config.set_value("general.main_branch", "custom-main")
    config.set_value("clean.exclude_branches", ["branch1", "branch2"])
    
    # Enregistrer dans un fichier temporaire
    temp_fd, temp_path = tempfile.mkstemp(suffix=".toml")
    os.close(temp_fd)
    
    try:
        config.save(temp_path)
        
        # Vérifier que le fichier existe
        assert os.path.exists(temp_path)
        
        # Charger dans une nouvelle instance
        config2 = Config()
        config2.load_from_file(temp_path)
        
        # Vérifier que les valeurs sont identiques
        assert config2.get_value("general.main_branch") == "custom-main"
        assert config2.get_value("clean.exclude_branches") == ["branch1", "branch2"]
        
        # Vérifier le contenu brut du fichier
        with open(temp_path, "r") as f:
            content = toml.load(f)
        
        assert content["general"]["main_branch"] == "custom-main"
        assert content["clean"]["exclude_branches"] == ["branch1", "branch2"]
        
    finally:
        # Nettoyer
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_load_nonexistent_file():
    """Teste le chargement d'un fichier inexistant."""
    config = Config()
    
    with pytest.raises(FileNotFoundError):
        config.load_from_file("/path/to/nonexistent/file.toml")


def test_merge_config():
    """Teste la fusion de configurations."""
    config = Config()
    
    # Configuration de base
    assert config.get_value("general.main_branch") == "main"
    assert config.get_value("clean.auto_clean") is False
    
    # Nouvelle configuration à fusionner
    new_config = {
        "general": {
            "main_branch": "master"
        },
        "custom": {
            "key": "value"
        }
    }
    
    # Fusionner
    config._merge_config(new_config)
    
    # Vérifier les valeurs fusionnées
    assert config.get_value("general.main_branch") == "master"
    assert config.get_value("clean.auto_clean") is False  # Inchangé
    assert config.get_value("custom.key") == "value"  # Nouvelle valeur


def test_get_all():
    """Teste la récupération de toute la configuration."""
    config = Config()
    
    # Modifier quelques valeurs
    config.set_value("general.main_branch", "modified")
    config.set_value("custom.key", "value")
    
    # Récupérer toute la configuration
    all_config = config.get_all()
    
    # Vérifier qu'il s'agit d'une copie (non d'une référence)
    assert all_config is not config.config
    
    # Vérifier les valeurs
    assert all_config["general"]["main_branch"] == "modified"
    assert all_config["custom"]["key"] == "value"
    
    # Modifier la copie ne devrait pas affecter l'original
    all_config["general"]["main_branch"] = "changed_again"
    assert config.get_value("general.main_branch") == "modified"


def test_validate():
    """Teste la validation de la configuration."""
    config = Config()
    
    # Configuration par défaut valide
    issues = config.validate()
    assert len(issues) == 0
    
    # Invalider la configuration
    config.set_value("general.main_branch", "")  # Valeur vide
    config.set_value("clean.age_threshold", "not_an_int")  # Mauvais type
    config.set_value("sync.default_strategy", "invalid")  # Valeur non autorisée
    
    # Vérifier les problèmes détectés
    issues = config.validate()
    assert len(issues) >= 3
    
    # Vérifier les messages d'erreur
    assert any("branche principale" in issue for issue in issues)
    assert any("seuil d'âge" in issue for issue in issues)
    assert any("stratégie de synchronisation" in issue for issue in issues)