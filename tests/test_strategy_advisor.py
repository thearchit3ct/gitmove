"""
Tests pour le conseiller de stratégie.

Ce module teste les fonctionnalités de StrategyAdvisor.
"""

import os
import pytest

from gitmove.core.strategy_advisor import StrategyAdvisor


def test_init(configured_git_repo, gitmove_config):
    """Teste l'initialisation du conseiller de stratégie."""
    strategy_advisor = StrategyAdvisor(configured_git_repo, gitmove_config)
    
    assert strategy_advisor.repo == configured_git_repo
    assert strategy_advisor.config == gitmove_config
    assert strategy_advisor.main_branch == "main"
    assert strategy_advisor.rebase_threshold == 5


def test_get_strategy_advice_same_branch(configured_git_repo, gitmove_config):
    """Teste le conseil de stratégie quand la branche source et la cible sont identiques."""
    strategy_advisor = StrategyAdvisor(configured_git_repo, gitmove_config)
    
    advice = strategy_advisor.get_strategy_advice("main", "main")
    
    assert advice["strategy"] == "none"
    assert "branche cible" in advice["reason"]
    assert advice["details"]["branch"] == "main"
    assert advice["details"]["target"] == "main"


def test_get_strategy_advice_feature_branch(multi_branch_repo, gitmove_config):
    """Teste le conseil de stratégie pour une branche de fonctionnalité."""
    strategy_advisor = StrategyAdvisor(multi_branch_repo, gitmove_config)
    
    # feature/a a peu de commits, donc rebase devrait être recommandé
    advice = strategy_advisor.get_strategy_advice("feature/a", "main")
    
    assert advice["strategy"] in ["rebase", "merge"]
    assert "details" in advice
    
    # Vérifier que l'analyse contient les données attendues
    details = advice["details"]
    assert "ahead_commits" in details
    assert "behind_commits" in details
    assert "branch_age_days" in details
    assert "branch_pattern" in details


def test_forced_strategy(multi_branch_repo, gitmove_config):
    """Teste la stratégie forcée selon le pattern de branche."""
    # Configurer des patterns de force
    gitmove_config.set_value("advice.force_merge_patterns", ["feature/*"])
    gitmove_config.set_value("advice.force_rebase_patterns", ["bugfix/*"])
    
    strategy_advisor = StrategyAdvisor(multi_branch_repo, gitmove_config)
    
    # feature/a devrait être forcé en merge
    advice = strategy_advisor.get_strategy_advice("feature/a", "main")
    assert advice["strategy"] == "merge"
    assert "forcée" in advice["reason"].lower()
    
    # bugfix/x devrait être forcé en rebase
    advice = strategy_advisor.get_strategy_advice("bugfix/x", "main")
    assert advice["strategy"] == "rebase"
    assert "forcée" in advice["reason"].lower()


def test_strategy_recommendation_factors(multi_branch_repo, gitmove_config):
    """Teste les facteurs qui influencent la recommandation de stratégie."""
    # Réinitialiser les patterns de force
    gitmove_config.set_value("advice.force_merge_patterns", [])
    gitmove_config.set_value("advice.force_rebase_patterns", [])
    
    strategy_advisor = StrategyAdvisor(multi_branch_repo, gitmove_config)
    
    # Analyser une branche
    analysis = strategy_advisor._analyze_branch("feature/a", "main")
    
    # Modifier artificiellement l'analyse pour tester différents scénarios
    
    # 1. Peu de commits (≤ rebase_threshold) -> devrait privilégier rebase
    analysis_few_commits = analysis.copy()
    analysis_few_commits["ahead_commits"] = 3
    strategy, reason = strategy_advisor._determine_strategy(analysis_few_commits)
    assert strategy == "rebase"
    
    # 2. Beaucoup de commits (> rebase_threshold) -> devrait privilégier merge
    analysis_many_commits = analysis.copy()
    analysis_many_commits["ahead_commits"] = 10
    strategy, reason = strategy_advisor._determine_strategy(analysis_many_commits)
    assert strategy == "merge"
    
    # 3. Branche ancienne -> devrait privilégier merge
    analysis_old_branch = analysis.copy()
    analysis_old_branch["branch_age_days"] = 40
    strategy, reason = strategy_advisor._determine_strategy(analysis_old_branch)
    assert strategy == "merge"


def test_branch_pattern_recognition(multi_branch_repo, gitmove_config):
    """Teste la reconnaissance des patterns de branches."""
    strategy_advisor = StrategyAdvisor(multi_branch_repo, gitmove_config)
    
    # Reconnaître différents patterns
    assert strategy_advisor._get_branch_pattern("feature/a") == "feature"
    assert strategy_advisor._get_branch_pattern("bugfix/x") == "bugfix"
    assert strategy_advisor._get_branch_pattern("release/1.0") == "release"
    assert strategy_advisor._get_branch_pattern("main") == "unknown"
    assert strategy_advisor._get_branch_pattern("dev") == "unknown"
    
    # Test avec d'autres patterns courants
    assert strategy_advisor._get_branch_pattern("fix/issue-123") == "bugfix"
    assert strategy_advisor._get_branch_pattern("hotfix/security") == "bugfix"
    assert strategy_advisor._get_branch_pattern("docs/update-readme") == "doc"
    assert strategy_advisor._get_branch_pattern("chore/update-deps") == "chore"


def test_file_type_classification(multi_branch_repo, gitmove_config):
    """Teste la classification des types de fichiers."""
    strategy_advisor = StrategyAdvisor(multi_branch_repo, gitmove_config)
    
    # Tester différents types de fichiers
    assert strategy_advisor._get_file_type("src/app.py") == "code"
    assert strategy_advisor._get_file_type("config.json") == "config"
    assert strategy_advisor._get_file_type("README.md") == "doc"
    assert strategy_advisor._get_file_type("tests/test_app.py") == "test"
    assert strategy_advisor._get_file_type("static/logo.png") == "other"
    assert strategy_advisor._get_file_type("src/styles.css") == "code"
    assert strategy_advisor._get_file_type("schema.sql") == "code"