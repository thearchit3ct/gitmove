"""
Tests pour le gestionnaire de synchronisation.

Ce module teste les fonctionnalités de SyncManager.
"""

import os
import pytest

from gitmove.core.sync_manager import SyncManager


def test_init(configured_git_repo, gitmove_config):
    """Teste l'initialisation du gestionnaire de synchronisation."""
    sync_manager = SyncManager(configured_git_repo, gitmove_config)
    
    assert sync_manager.repo == configured_git_repo
    assert sync_manager.config == gitmove_config
    assert sync_manager.main_branch == "main"
    assert sync_manager.default_strategy == "rebase"


def test_check_sync_status_main_branch(configured_git_repo, gitmove_config):
    """Teste la vérification du statut de synchronisation pour la branche principale."""
    sync_manager = SyncManager(configured_git_repo, gitmove_config)
    
    # La branche main est toujours considérée comme synchronisée avec elle-même
    status = sync_manager.check_sync_status("main")
    
    assert status["is_synced"] is True
    assert status["branch"] == "main"
    assert status["target"] == "main"
    assert status["ahead_commits"] == 0
    assert status["behind_commits"] == 0


def test_check_sync_status_feature_branch(multi_branch_repo, gitmove_config):
    """Teste la vérification du statut de synchronisation pour une branche de fonctionnalité."""
    sync_manager = SyncManager(multi_branch_repo, gitmove_config)
    
    # La branche feature/a n'est pas synchronisée avec main
    status = sync_manager.check_sync_status("feature/a")
    
    # Elle devrait être en retard par rapport à main
    assert status["is_synced"] is False
    assert status["branch"] == "feature/a"
    assert status["target"] == "main"
    assert status["behind_commits"] > 0


def test_determine_sync_strategy(multi_branch_repo, gitmove_config):
    """Teste la détermination de la stratégie de synchronisation."""
    sync_manager = SyncManager(multi_branch_repo, gitmove_config)
    
    # Pour une branche avec peu de commits, rebase devrait être recommandé
    strategy = sync_manager._determine_sync_strategy("feature/a", "main")
    assert strategy == "rebase"
    
    # Modifier la configuration pour tester d'autres cas
    gitmove_config.set_value("advice.force_merge_patterns", ["feature/*"])
    sync_manager = SyncManager(multi_branch_repo, gitmove_config)
    
    # Maintenant, merge devrait être forcé pour les branches feature/*
    strategy = sync_manager._determine_sync_strategy("feature/a", "main")
    assert strategy == "merge"


def test_sync_up_to_date(multi_branch_repo, gitmove_config):
    """Teste la synchronisation quand la branche est déjà à jour."""
    sync_manager = SyncManager(multi_branch_repo, gitmove_config)
    
    # feature/b est déjà fusionnée dans main, donc elle est à jour
    result = sync_manager.sync_with_main("feature/b")
    
    assert result["status"] == "up-to-date"
    assert result["branch"] == "feature/b"
    assert result["target"] == "main"


def test_sync_with_changes(multi_branch_repo, gitmove_config):
    """Teste la synchronisation quand des modifications sont nécessaires."""
    repo = multi_branch_repo
    sync_manager = SyncManager(repo, gitmove_config)
    
    # S'assurer que nous sommes sur feature/a
    repo.git.checkout("feature/a")
    
    # Synchroniser avec rebase
    result = sync_manager.sync_with_main(strategy="rebase")
    
    # Vérifier le résultat
    assert result["status"] in ["synchronized", "conflicts"]
    assert result["branch"] == "feature/a"
    assert result["target"] == "main"
    
    if result["status"] == "synchronized":
        assert result["strategy"] == "rebase"
    
    # Vérifier le statut après la synchronisation
    if result["status"] == "synchronized":
        status = sync_manager.check_sync_status("feature/a")
        assert status["is_synced"] is True
        assert status["behind_commits"] == 0


def test_sync_with_conflicts(conflict_repo, gitmove_config):
    """Teste la détection des conflits pendant la synchronisation."""
    repo = conflict_repo
    sync_manager = SyncManager(repo, gitmove_config)
    
    # Synchroniser feature/conflict qui a des conflits avec main
    result = sync_manager.sync_with_main("feature/conflict")
    
    # La synchronisation devrait détecter des conflits
    assert result["status"] == "conflicts"
    assert "conflicts" in result
    assert result["conflicts"]["has_conflicts"] is True


def test_schedule_sync(configured_git_repo, gitmove_config):
    """Teste la planification de synchronisation."""
    # Activer la synchronisation automatique
    gitmove_config.set_value("sync.auto_sync", True)
    
    sync_manager = SyncManager(configured_git_repo, gitmove_config)
    
    # Planifier une synchronisation quotidienne
    result = sync_manager.schedule_sync("daily")
    
    assert result["status"] == "scheduled"
    assert result["frequency"] == "daily"
    assert result["target"] == "main"
    assert result["strategy"] == "rebase"
    
    # Désactiver la synchronisation automatique
    gitmove_config.set_value("sync.auto_sync", False)
    
    result = sync_manager.schedule_sync("daily")
    assert result["status"] == "disabled"